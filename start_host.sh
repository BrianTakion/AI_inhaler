#!/bin/bash
# 호스트에서 devcontainer 내부의 서버를 시작하는 스크립트
# WSL, Linux, macOS 모두 지원

set -e

# 스크립트 위치 기반으로 프로젝트 루트 찾기
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="AI_inhaler"
CONTAINER_WORKSPACE="/workspaces/AI_inhaler"

# Docker 컨테이너 찾기 함수
find_container() {
    # 방법 1: 프로젝트 워크스페이스 경로로 찾기
    local container=$(docker ps --filter "ancestor=mcr.microsoft.com/devcontainers/python:3.11" \
        --format "{{.Names}}" 2>/dev/null | head -1)
    
    if [ -z "$container" ]; then
        # 방법 2: 프로젝트 이름 기반으로 찾기
        container=$(docker ps --filter "name=${PROJECT_NAME}" \
            --format "{{.Names}}" 2>/dev/null | head -1)
    fi
    
    if [ -z "$container" ]; then
        # 방법 3: /workspaces 경로를 마운트한 컨테이너 찾기
        container=$(docker ps --format "{{.Names}}\t{{.Mounts}}" 2>/dev/null | \
            grep -i "workspaces\|${PROJECT_NAME}" | cut -f1 | head -1)
    fi
    
    if [ -z "$container" ]; then
        # 방법 4: 모든 실행 중인 컨테이너에서 확인
        for name in $(docker ps --format "{{.Names}}" 2>/dev/null); do
            if docker exec "$name" test -d "$CONTAINER_WORKSPACE" 2>/dev/null; then
                container="$name"
                break
            fi
        done
    fi
    
    echo "$container"
}

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
    exit 1
fi

# 컨테이너 찾기
echo "컨테이너 찾는 중..."
CONTAINER_NAME=$(find_container)

if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ 오류: 실행 중인 devcontainer를 찾을 수 없습니다."
    echo ""
    echo "해결 방법:"
    echo "  1. VS Code에서 'Reopen in Container'로 컨테이너를 시작하세요"
    echo "  2. 또는 다음 명령으로 컨테이너를 확인하세요:"
    echo "     docker ps"
    echo ""
    echo "수동으로 컨테이너 이름을 지정하려면:"
    echo "  CONTAINER_NAME=your-container-name ./start_host.sh"
    exit 1
fi

echo "✓ 컨테이너 발견: $CONTAINER_NAME"
echo ""

# 호스트 IP 주소 파악 함수
get_host_ip() {
    local host_ip=""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: ifconfig 사용
        host_ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
        # Linux/WSL: hostname -I 사용
        if command -v hostname >/dev/null 2>&1; then
            host_ip=$(hostname -I | awk '{print $1}' 2>/dev/null)
        fi
        
        # Docker 컨테이너 IP(172.17.x.x, 172.18.x.x 등)인 경우 다른 방법 시도
        if [[ "$host_ip" =~ ^172\.(17|18|19|20)\. ]]; then
            # ip 명령어로 실제 호스트 인터페이스 찾기
            if command -v ip >/dev/null 2>&1; then
                # eth0, enp*, ens* 등의 실제 네트워크 인터페이스에서 IP 찾기
                host_ip=$(ip addr show 2>/dev/null | grep -E "inet [0-9]" | grep -v "127.0.0.1" | grep -v "172.17" | grep -v "172.18" | grep -v "172.19" | grep -v "172.20" | head -1 | awk '{print $2}' | cut -d/ -f1)
            fi
        fi
        
        # 여전히 찾지 못한 경우 ip route로 기본 게이트웨이 IP 찾기
        if [ -z "$host_ip" ] || [[ "$host_ip" =~ ^172\.(17|18|19|20)\. ]]; then
            if command -v ip >/dev/null 2>&1; then
                host_ip=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' 2>/dev/null)
            fi
        fi
    fi
    
    echo "$host_ip"
}

# 호스트 IP 주소 파악
HOST_IP=$(get_host_ip)

# 컨테이너 내부에서 start_container.sh 실행
echo "=========================================="
echo "호스트에서 컨테이너 내부 서버 시작"
echo "=========================================="
echo "컨테이너: $CONTAINER_NAME"
echo "프로젝트: $CONTAINER_WORKSPACE"
echo ""

# 호스트 IP 정보 미리 출력
if [ ! -z "$HOST_IP" ] && [[ ! "$HOST_IP" =~ ^172\.(17|18|19|20)\. ]]; then
    echo "호스트 IP 주소: $HOST_IP"
    echo ""
    echo "서버 시작 후 원격 브라우저에서 접속:"
    echo "  - 프론트엔드: http://${HOST_IP}:8080"
    echo "  - 백엔드 API: http://${HOST_IP}:8000"
    echo ""
elif [ -z "$HOST_IP" ]; then
    echo "⚠️  호스트 IP 주소를 자동으로 찾을 수 없습니다."
    echo "   수동으로 확인하려면:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "     ifconfig | grep 'inet ' | grep -v 127.0.0.1"
    else
        echo "     hostname -I"
        echo "     또는"
        echo "     ip addr show | grep 'inet '"
    fi
    echo ""
fi

echo "=========================================="
echo ""

# 컨테이너 내부에서 start_container.sh 실행
# -it 옵션으로 인터랙티브 모드 사용 (Ctrl+C로 종료 가능)
docker exec -it "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && ./start_container.sh"

