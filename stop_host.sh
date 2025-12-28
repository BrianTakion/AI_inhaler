#!/bin/bash
# 호스트에서 devcontainer 내부의 서버를 종료하는 스크립트
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
    exit 1
fi

# Docker 데몬 실행 확인
if ! docker ps >/dev/null 2>&1; then
    echo "❌ 오류: Docker 데몬이 실행 중이지 않습니다."
    exit 1
fi

# 컨테이너 찾기
CONTAINER_NAME=$(find_container)

if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ 오류: 실행 중인 devcontainer를 찾을 수 없습니다."
    echo ""
    echo "수동으로 컨테이너 이름을 지정하려면:"
    echo "  CONTAINER_NAME=your-container-name ./stop_host.sh"
    exit 1
fi

echo "컨테이너: $CONTAINER_NAME"
echo "서버 종료 중..."

# 컨테이너 내부에서 stop_container.sh 실행
docker exec "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && ./stop_container.sh" 2>/dev/null || {
    echo "⚠️  stop_container.sh 실행 실패, 직접 프로세스 종료 시도..."
    # 대체 방법: 컨테이너 내부에서 직접 프로세스 종료
    docker exec "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && pkill -f api_server.py || true"
    docker exec "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && pkill -f 'python.*http.server.*8080' || true"
    docker exec "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && lsof -ti:8080 | xargs kill -9 2>/dev/null || true"
    docker exec "$CONTAINER_NAME" bash -c "cd $CONTAINER_WORKSPACE && lsof -ti:8000 | xargs kill -9 2>/dev/null || true"
}

echo "✓ 서버 종료 완료"

