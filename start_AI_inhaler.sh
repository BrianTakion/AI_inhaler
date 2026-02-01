#!/bin/bash
# AI Inhaler 통합 시작 스크립트
# 컨테이너가 있으면 포트 매핑 확인 후 서버 시작
# 컨테이너가 없으면 devcontainer.json 설정으로 새 컨테이너 생성 후 서버 시작
#
# 사용법:
#   ./start_AI_inhaler.sh           # 포그라운드 실행 (Ctrl+C로 종료)
#   ./start_AI_inhaler.sh --detach  # 백그라운드 실행 (SSH 종료해도 유지)
#   ./start_AI_inhaler.sh -d        # --detach 단축 옵션
#   ./start_AI_inhaler.sh --stop    # 백그라운드 서버 종료
#   ./start_AI_inhaler.sh --status  # 서버 상태 확인
#
# 지원 플랫폼: macOS, Linux, WSL (Windows Subsystem for Linux)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="AI_inhaler"
CONTAINER_WORKSPACE="/workspaces/AI_inhaler"
DEVCONTAINER_JSON="${SCRIPT_DIR}/.devcontainer/devcontainer.json"

# Docker 설치 확인
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ 오류: Docker가 설치되어 있지 않습니다."
    echo "   Docker를 설치하고 실행한 후 다시 시도하세요."
    exit 1
fi

# Docker 데몬 실행 확인
if ! docker ps >/dev/null 2>&1; then
    echo "❌ 오류: Docker 데몬이 실행 중이지 않습니다."
    echo "   Docker를 시작한 후 다시 시도하세요."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   macOS: open -a Docker"
    elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
        # WSL 감지
        if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
            echo "   WSL: Docker Desktop을 시작하거나 다음 명령 실행:"
            echo "        sudo service docker start"
        else
            echo "   Linux: sudo systemctl start docker"
            echo "   또는: sudo service docker start"
        fi
    fi
    exit 1
fi

# Docker 컨테이너 찾기 함수
find_container() {
    # 실행 중인 컨테이너 찾기
    local container=$(docker ps --format "{{.Names}}" 2>/dev/null | \
        grep -E "vsc-.*|${PROJECT_NAME}" | head -1)
    
    if [ -z "$container" ]; then
        # /workspaces 경로를 마운트한 컨테이너 찾기
        for name in $(docker ps --format "{{.Names}}" 2>/dev/null); do
            if docker inspect "$name" --format '{{range .Mounts}}{{.Destination}}{{end}}' 2>/dev/null | grep -q "workspaces"; then
                container="$name"
                break
            fi
        done
    fi
    
    # 중지된 컨테이너도 찾기
    if [ -z "$container" ]; then
        container=$(docker ps -a --format "{{.Names}}" 2>/dev/null | \
            grep -E "vsc-.*|${PROJECT_NAME}" | head -1)
    fi
    
    # 프로젝트 워크스페이스 경로로 찾기
    if [ -z "$container" ]; then
        for name in $(docker ps -a --format "{{.Names}}" 2>/dev/null); do
            if docker inspect "$name" --format '{{range .Mounts}}{{.Destination}}{{end}}' 2>/dev/null | grep -q "workspaces"; then
                container="$name"
                break
            fi
        done
    fi
    
    echo "$container"
}

# devcontainer.json에서 설정 읽기 함수
read_devcontainer_config() {
    if [ ! -f "$DEVCONTAINER_JSON" ]; then
        echo "❌ 오류: devcontainer.json을 찾을 수 없습니다: $DEVCONTAINER_JSON"
        exit 1
    fi
    
    # Python으로 JSON 파싱
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import json
import sys

try:
    with open('${DEVCONTAINER_JSON}', 'r') as f:
        config = json.load(f)
        
        # 이미지 정보
        image = config.get('image', '')
        if image:
            print(f'IMAGE={image}')
        
        # remoteUser
        remote_user = config.get('remoteUser', '')
        if remote_user:
            print(f'REMOTE_USER={remote_user}')
        
        # runArgs (포트 매핑)
        run_args = config.get('runArgs', [])
        if run_args:
            print(f'RUN_ARGS={json.dumps(run_args)}')
        
        # postCreateCommand
        post_create = config.get('postCreateCommand', '')
        if post_create:
            print(f'POST_CREATE={post_create}')
            
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"
    else
        echo "❌ 오류: Python3가 필요합니다 (devcontainer.json 파싱용)"
        exit 1
    fi
}

# 포트 매핑 확인 및 설정 함수
ensure_port_mapping() {
    local container_name=$1
    
    # 포트 매핑 확인
    PORT_MAPPING=$(docker inspect "$container_name" --format '{{json .HostConfig.PortBindings}}' 2>/dev/null || echo "{}")
    HAS_PORT_8080=$(echo "$PORT_MAPPING" | grep -q '"8080/tcp"' && echo "yes" || echo "no")
    HAS_PORT_8000=$(echo "$PORT_MAPPING" | grep -q '"8000/tcp"' && echo "yes" || echo "no")
    
    if [ "$HAS_PORT_8080" = "yes" ] && [ "$HAS_PORT_8000" = "yes" ]; then
        echo "✓ 포트 매핑이 이미 설정되어 있습니다."
        return 0
    fi
    
    # 포트 매핑이 없으면 재시작 필요
    echo "⚠️  포트 매핑이 없습니다. 컨테이너를 포트 매핑과 함께 재시작합니다."
    echo ""
    
    # 컨테이너 정보 수집
    IMAGE_ID=$(docker inspect "$container_name" --format '{{.Image}}' 2>/dev/null)
    MOUNTS=$(docker inspect "$container_name" --format '{{range .Mounts}}-v {{.Source}}:{{.Destination}} {{end}}' 2>/dev/null)
    ENV_VARS=$(docker inspect "$container_name" --format '{{range .Config.Env}}{{.}}{{end}}' 2>/dev/null)
    NETWORK_MODE=$(docker inspect "$container_name" --format '{{.HostConfig.NetworkMode}}' 2>/dev/null)
    
    # 기본 마운트 설정
    PROJECT_MOUNT="-v ${SCRIPT_DIR}:${CONTAINER_WORKSPACE}"
    
    # 추가 마운트가 있으면 포함
    if [ ! -z "$MOUNTS" ] && [ "$MOUNTS" != "-v " ]; then
        MOUNT_ARGS="$MOUNTS"
    else
        MOUNT_ARGS="$PROJECT_MOUNT"
    fi
    
    # 네트워크 모드 설정
    if [ "$NETWORK_MODE" != "default" ] && [ ! -z "$NETWORK_MODE" ]; then
        NETWORK_ARG="--network $NETWORK_MODE"
    else
        NETWORK_ARG=""
    fi
    
    # 기존 컨테이너 중지 및 제거
    if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "컨테이너 중지 중..."
        docker stop "$container_name" >/dev/null 2>&1 || true
    fi
    
    echo "기존 컨테이너 제거 중..."
    docker rm "$container_name" >/dev/null 2>&1 || true
    
    # 새 컨테이너 시작 (포트 매핑 포함)
    echo "포트 매핑과 함께 컨테이너 시작 중..."
    echo "  - 프론트엔드: 8080:8080"
    echo "  - 백엔드 API: 8000:8000"
    echo ""
    
    # 환경 변수 설정
    ENV_ARGS=""
    if [ ! -z "$ENV_VARS" ]; then
        while IFS= read -r env_var; do
            if [ ! -z "$env_var" ]; then
                ENV_ARGS="$ENV_ARGS -e \"$env_var\""
            fi
        done <<< "$ENV_VARS"
    fi
    
    # 컨테이너 시작
    eval docker run -d \
        --name "$container_name" \
        -p 8080:8080 \
        -p 8000:8000 \
        $MOUNT_ARGS \
        $NETWORK_ARG \
        -w "$CONTAINER_WORKSPACE" \
        "$IMAGE_ID" \
        sleep infinity
    
    echo "✓ 컨테이너가 포트 매핑과 함께 시작되었습니다."
    echo ""
    
    # 포트 매핑 확인
    sleep 2
    docker ps --filter "name=$container_name" --format "table {{.Names}}\t{{.Ports}}"
    echo ""
}

# 새 컨테이너 생성 함수
create_new_container() {
    local container_name=""
    
    {
        echo "==========================================" >&2
        echo "새 컨테이너 생성" >&2
        echo "==========================================" >&2
        echo "" >&2
        
        # devcontainer.json에서 설정 읽기
        echo "devcontainer.json 설정 읽는 중..." >&2
        DEVCONTAINER_CONFIG=$(read_devcontainer_config)
        
        # 설정 파싱
        IMAGE=$(echo "$DEVCONTAINER_CONFIG" | grep "^IMAGE=" | cut -d'=' -f2-)
        REMOTE_USER=$(echo "$DEVCONTAINER_CONFIG" | grep "^REMOTE_USER=" | cut -d'=' -f2-)
        RUN_ARGS_JSON=$(echo "$DEVCONTAINER_CONFIG" | grep "^RUN_ARGS=" | cut -d'=' -f2-)
        POST_CREATE=$(echo "$DEVCONTAINER_CONFIG" | grep "^POST_CREATE=" | cut -d'=' -f2-)
        
        if [ -z "$IMAGE" ]; then
            echo "❌ 오류: devcontainer.json에서 이미지 정보를 찾을 수 없습니다." >&2
            exit 1
        fi
        
        echo "이미지: $IMAGE" >&2
        echo "사용자: ${REMOTE_USER:-root}" >&2
        echo "" >&2
        
        # 이미지가 로컬에 있는지 확인
        if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE}" && \
           ! docker images --format "{{.ID}}" | grep -q "^${IMAGE}"; then
            echo "이미지 다운로드 중: $IMAGE" >&2
            docker pull "$IMAGE" || {
                echo "❌ 오류: 이미지를 다운로드할 수 없습니다: $IMAGE" >&2
                exit 1
            }
        fi
        
        # 컨테이너 이름 생성
        container_name="ai-inhaler-$(date +%s)"
        
        # runArgs 파싱 (포트 매핑)
        PORT_ARGS=""
        if [ ! -z "$RUN_ARGS_JSON" ] && [ "$RUN_ARGS_JSON" != "null" ]; then
            # JSON 배열을 파싱하여 포트 매핑 추출
            PORT_ARGS=$(echo "$RUN_ARGS_JSON" | python3 -c "
import json, sys
try:
    args = json.load(sys.stdin)
    port_args = []
    i = 0
    while i < len(args):
        if args[i] == '-p' and i + 1 < len(args):
            port_args.append('-p')
            port_args.append(args[i+1])
            i += 2
        else:
            i += 1
    print(' '.join(port_args))
except:
    print('-p 8080:8080 -p 8000:8000')
" 2>/dev/null || echo "-p 8080:8080 -p 8000:8000")
        else
            # 기본 포트 매핑
            PORT_ARGS="-p 8080:8080 -p 8000:8000"
        fi
        
        echo "포트 매핑: $PORT_ARGS" >&2
        echo "" >&2
        
        # 컨테이너 생성
        echo "컨테이너 생성 중..." >&2
        docker run -d \
            --name "$container_name" \
            $PORT_ARGS \
            -v "${SCRIPT_DIR}:${CONTAINER_WORKSPACE}" \
            -w "$CONTAINER_WORKSPACE" \
            "$IMAGE" \
            sleep infinity
        
        echo "✓ 컨테이너가 생성되었습니다: $container_name" >&2
        echo "" >&2
        
        # 컨테이너가 완전히 준비될 때까지 대기
        echo "컨테이너 준비 대기 중..." >&2
        for i in {1..10}; do
            if docker exec "$container_name" test -d "$CONTAINER_WORKSPACE" >/dev/null 2>&1; then
                echo "✓ 컨테이너가 준비되었습니다." >&2
                break
            fi
            if [ $i -eq 10 ]; then
                echo "⚠️  컨테이너 준비 확인 실패 (계속 진행)" >&2
            else
                sleep 1
            fi
        done
        echo "" >&2
        
        # postCreateCommand 실행 (선택적)
        if [ ! -z "$POST_CREATE" ] && [ "$POST_CREATE" != "null" ]; then
            echo "postCreateCommand 실행 중: $POST_CREATE" >&2
            docker exec "$container_name" bash -c "cd $CONTAINER_WORKSPACE && $POST_CREATE" || {
                echo "⚠️  postCreateCommand 실행 실패 (계속 진행)" >&2
            }
            echo "" >&2
        fi
        
        # 포트 매핑 확인
        sleep 2
        echo "포트 매핑 확인:" >&2
        docker ps --filter "name=$container_name" --format "table {{.Names}}\t{{.Ports}}" >&2
        echo "" >&2
    } >&2
    
    # 컨테이너 이름만 stdout으로 반환
    echo "$container_name"
}

# 호스트 IP 주소 파악 함수
get_host_ip() {
    local host_ip=""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: ifconfig 사용
        host_ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
        # WSL 감지
        local is_wsl=false
        if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
            is_wsl=true
        fi
        
        # Linux/WSL: hostname -I 사용 (가장 간단한 방법)
        if command -v hostname >/dev/null 2>&1; then
            host_ip=$(hostname -I | awk '{print $1}' 2>/dev/null)
        fi
        
        # Docker 네트워크 IP(172.17.x.x, 172.18.x.x 등)인 경우 다른 방법 시도
        if [[ "$host_ip" =~ ^172\.(17|18|19|20)\. ]]; then
            # ip 명령어로 실제 호스트 인터페이스 찾기
            if command -v ip >/dev/null 2>&1; then
                # eth0, enp*, ens*, wlan* 등의 실제 네트워크 인터페이스에서 IP 찾기
                host_ip=$(ip addr show 2>/dev/null | grep -E "inet [0-9]" | grep -v "127.0.0.1" | grep -v "172.17" | grep -v "172.18" | grep -v "172.19" | grep -v "172.20" | head -1 | awk '{print $2}' | cut -d/ -f1)
            fi
        fi
        
        # 여전히 찾지 못한 경우 ip route로 기본 게이트웨이 IP 찾기
        if [ -z "$host_ip" ] || [[ "$host_ip" =~ ^172\.(17|18|19|20)\. ]]; then
            if command -v ip >/dev/null 2>&1; then
                host_ip=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' 2>/dev/null)
            fi
        fi
        
        # WSL의 경우 Windows 호스트 IP 찾기 (선택적)
        if [ "$is_wsl" = true ] && [ -z "$host_ip" ]; then
            # WSL2에서 Windows 호스트 IP 찾기
            if command -v ip >/dev/null 2>&1; then
                local wsl_host_ip=$(ip route show | grep -i default | awk '{print $3}' 2>/dev/null)
                if [ ! -z "$wsl_host_ip" ]; then
                    host_ip="$wsl_host_ip"
                fi
            fi
        fi
    fi
    
    echo "$host_ip"
}

# --stop / --status: 컨테이너를 찾아서 바로 처리 후 종료
if [ "$1" = "--stop" ] || [ "$1" = "--status" ]; then
    CONTAINER_NAME=$(find_container)
    if [ -z "$CONTAINER_NAME" ]; then
        echo "❌ 실행 중인 AI Inhaler 컨테이너를 찾을 수 없습니다."
        exit 1
    fi

    if [ "$1" = "--status" ]; then
        echo "=========================================="
        echo "AI Inhaler 서버 상태"
        echo "=========================================="
        echo "컨테이너: $CONTAINER_NAME"
        echo ""

        # 컨테이너 실행 여부
        if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            echo "  컨테이너 상태: 중지됨"
            exit 0
        fi
        echo "  컨테이너 상태: 실행 중"
        echo ""

        # 백엔드 확인
        BACKEND_OK=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")
        if [ "$BACKEND_OK" != "000" ]; then
            echo "  백엔드 API (8000): 실행 중"
        else
            echo "  백엔드 API (8000): 중지됨"
        fi

        # 프론트엔드 확인
        FRONTEND_OK=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
        if [ "$FRONTEND_OK" != "000" ]; then
            echo "  프론트엔드 (8080): 실행 중"
        else
            echo "  프론트엔드 (8080): 중지됨"
        fi
        echo "=========================================="
        exit 0
    fi

    # --stop 처리
    echo "=========================================="
    echo "AI Inhaler 서버 종료"
    echo "=========================================="
    echo "컨테이너: $CONTAINER_NAME"
    echo ""

    # 1단계: SIGTERM으로 정상 종료 요청
    docker exec "$CONTAINER_NAME" bash -c '
        pkill -f "api_server.py" 2>/dev/null
        pkill -f "uvicorn.*api_server" 2>/dev/null
        pkill -f "python.*http.server.*8080" 2>/dev/null
        pkill -f "start_inside_container.sh" 2>/dev/null
    ' 2>/dev/null || true

    sleep 2

    # 2단계: 아직 살아있으면 SIGKILL로 강제 종료
    docker exec "$CONTAINER_NAME" bash -c '
        # PID 파일 기반 종료
        if [ -f /workspaces/AI_inhaler/.server_pids ]; then
            while read pid; do
                [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
            done < /workspaces/AI_inhaler/.server_pids
            rm -f /workspaces/AI_inhaler/.server_pids
        fi
        if [ -f /workspaces/AI_inhaler/api_server.pid ]; then
            pid=$(cat /workspaces/AI_inhaler/api_server.pid)
            [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
            rm -f /workspaces/AI_inhaler/api_server.pid
        fi

        # 패턴 매칭으로 남은 프로세스 강제 종료
        pkill -9 -f "api_server.py" 2>/dev/null
        pkill -9 -f "uvicorn.*api_server" 2>/dev/null
        pkill -9 -f "python.*http.server.*8080" 2>/dev/null
        pkill -9 -f "start_inside_container.sh" 2>/dev/null

        # 포트 직접 해제 (Linux)
        if command -v fuser >/dev/null 2>&1; then
            fuser -k 8000/tcp 2>/dev/null
            fuser -k 8080/tcp 2>/dev/null
        fi
    ' 2>/dev/null || true

    sleep 1

    # 종료 확인
    BACKEND_OK=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")
    FRONTEND_OK=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")

    if [ "$BACKEND_OK" = "000" ] && [ "$FRONTEND_OK" = "000" ]; then
        echo "  ✓ 모든 서버가 종료되었습니다."
    else
        [ "$BACKEND_OK" != "000" ] && echo "  ⚠️  백엔드 API가 아직 실행 중입니다."
        [ "$FRONTEND_OK" != "000" ] && echo "  ⚠️  프론트엔드가 아직 실행 중입니다."
    fi
    echo "=========================================="
    exit 0
fi

# 메인 로직
echo "=========================================="
echo "AI Inhaler 통합 시작 스크립트"
echo "=========================================="
echo ""

# 컨테이너 찾기
echo "컨테이너 찾는 중..."
CONTAINER_NAME=$(find_container)

if [ -z "$CONTAINER_NAME" ]; then
    # 컨테이너가 없으면 새로 생성
    echo "컨테이너를 찾을 수 없습니다. 새 컨테이너를 생성합니다."
    echo ""
    CONTAINER_NAME=$(create_new_container)
else
    echo "✓ 컨테이너 발견: $CONTAINER_NAME"
    echo ""
    
    # 컨테이너가 중지되어 있으면 시작
    if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo "컨테이너 시작 중..."
        docker start "$CONTAINER_NAME" >/dev/null 2>&1
        sleep 2
        echo "✓ 컨테이너가 시작되었습니다."
        echo ""
    fi
    
    # 포트 매핑 확인 및 설정
    ensure_port_mapping "$CONTAINER_NAME"
fi

# 호스트 IP 주소 확인
HOST_IP=$(get_host_ip)

echo "=========================================="
echo "서버 시작"
echo "=========================================="
echo "컨테이너: $CONTAINER_NAME"
echo "프로젝트: $CONTAINER_WORKSPACE"
echo ""

if [ ! -z "$HOST_IP" ] && [[ ! "$HOST_IP" =~ ^172\.(17|18|19|20)\. ]]; then
    echo "호스트 IP 주소: $HOST_IP"
    echo ""
    echo "서버 시작 후 원격 브라우저에서 접속:"
    echo "  - 백엔드 API: http://${HOST_IP}:8000"
    echo "  - 프론트엔드: http://${HOST_IP}:8080"
    echo ""
elif [ -z "$HOST_IP" ]; then
    echo "⚠️  호스트 IP 주소를 자동으로 찾을 수 없습니다."
    echo "   수동으로 확인하려면:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "     ifconfig | grep 'inet ' | grep -v 127.0.0.1"
    elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
        if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
            echo "     WSL: hostname -I"
            echo "     또는: ip addr show | grep 'inet '"
        else
            echo "     hostname -I"
            echo "     또는: ip addr show | grep 'inet '"
        fi
    fi
    echo ""
    echo "   또는 localhost로 접속:"
    echo "     - 백엔드 API: http://localhost:8000"
    echo "     - 프론트엔드: http://localhost:8080"
    echo ""
fi

echo "=========================================="
echo ""
echo "서버를 종료하려면 Ctrl+C를 누르세요."
echo ""

# 컨테이너가 실행 중인지 확인
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ 오류: 컨테이너가 실행 중이지 않습니다: $CONTAINER_NAME"
    exit 1
fi

# start_inside_container.sh 파일 존재 확인
echo "start_inside_container.sh 파일 확인 중..."
if ! docker exec "$CONTAINER_NAME" test -f "$CONTAINER_WORKSPACE/start_inside_container.sh" >/dev/null 2>&1; then
    echo "❌ 오류: start_inside_container.sh 파일을 찾을 수 없습니다: $CONTAINER_WORKSPACE/start_inside_container.sh"
    echo ""
    echo "컨테이너 내부 파일 확인:"
    docker exec "$CONTAINER_NAME" ls -la "$CONTAINER_WORKSPACE" | head -10
    exit 1
fi
echo "✓ start_inside_container.sh 파일 확인됨"
echo ""

# 실행 모드 선택: --detach 옵션으로 백그라운드 실행 가능
if [ "$1" = "--detach" ] || [ "$1" = "-d" ]; then
    # 백그라운드 모드: SSH 터미널 종료 후에도 서버 유지
    echo "🔧 백그라운드 모드로 서버를 시작합니다..."
    echo ""

    docker exec -d "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && ./start_inside_container.sh"

    # 서버 시작 대기
    sleep 5

    # 서버 상태 확인
    BACKEND_OK=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")
    FRONTEND_OK=$(docker exec "$CONTAINER_NAME" curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")

    echo "=========================================="
    echo "서버 상태 확인"
    echo "=========================================="
    if [ "$BACKEND_OK" != "000" ]; then
        echo "  ✓ 백엔드 API:  http://localhost:8000 (정상)"
    else
        echo "  ✗ 백엔드 API:  시작 대기 중... (로그 확인: docker exec $CONTAINER_NAME tail -f $CONTAINER_WORKSPACE/logs/backend.log)"
    fi
    if [ "$FRONTEND_OK" != "000" ]; then
        echo "  ✓ 프론트엔드:  http://localhost:8080 (정상)"
    else
        echo "  ✗ 프론트엔드:  시작 대기 중... (로그 확인: docker exec $CONTAINER_NAME tail -f $CONTAINER_WORKSPACE/logs/frontend.log)"
    fi
    echo ""
    echo "=========================================="
    echo "서버가 백그라운드에서 실행 중입니다."
    echo "SSH 터미널을 종료해도 서버는 계속 실행됩니다."
    echo ""
    echo "서버 로그 확인:"
    echo "  docker exec $CONTAINER_NAME tail -f $CONTAINER_WORKSPACE/logs/backend.log"
    echo "  docker exec $CONTAINER_NAME tail -f $CONTAINER_WORKSPACE/logs/frontend.log"
    echo ""
    echo "서버 종료:"
    echo "  docker exec $CONTAINER_NAME bash -c 'pkill -f api_server.py; pkill -f \"python.*http.server.*8080\"'"
    echo "=========================================="
else
    # 포그라운드 모드 (기존 방식): Ctrl+C로 종료
    # 컨테이너 내부에서 start_inside_container.sh 실행
    if [ -t 0 ]; then
        docker exec -it "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && ./start_inside_container.sh"
    else
        docker exec "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && ./start_inside_container.sh"
    fi
fi

