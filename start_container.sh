#!/bin/bash
# 백엔드와 프론트엔드를 동시에 실행하는 스크립트

set -e

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/app_server"
FRONTEND_DIR="${PROJECT_ROOT}/webUX"

# PID 파일 경로
PID_FILE="${PROJECT_ROOT}/.server_pids"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"

# 로그 디렉토리 생성
mkdir -p "${LOG_DIR}"

# Python 인터프리터 자동 선택 (python3 우선, 없으면 python)
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ 오류: Python이 설치되어 있지 않습니다."
    exit 1
fi

# 기존 프로세스 종료 함수
cleanup_existing() {
    echo "기존 프로세스 확인 중..."
    
    # 기존 API 서버 프로세스 종료
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "uvicorn.*api_server" 2>/dev/null || true
    
    # 기존 HTTP 서버 프로세스 종료 (포트 8080)
    # 크로스 플랫폼 지원: macOS와 Linux 모두 지원
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: lsof 사용
        if lsof -ti:8080 > /dev/null 2>&1; then
            lsof -ti:8080 | xargs kill -9 2>/dev/null || true
        fi
    else
        # Linux/WSL: ss, lsof, 또는 fuser 사용
        if command -v ss >/dev/null 2>&1; then
            # sed 사용 (macOS grep -oP 호환성 문제 해결)
            ss -tlnp 2>/dev/null | grep :8080 | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | xargs kill -9 2>/dev/null || true
        elif command -v lsof >/dev/null 2>&1; then
            lsof -ti:8080 | xargs kill -9 2>/dev/null || true
        elif command -v fuser >/dev/null 2>&1; then
            fuser -k 8080/tcp 2>/dev/null || true
        else
            # 대체 방법: python http.server 프로세스 종료
            pkill -f "python.*http.server.*8080" 2>/dev/null || true
        fi
    fi
    
    sleep 2
}

# 프로세스 종료 함수
cleanup() {
    echo ""
    echo "=========================================="
    echo "서버 종료 중..."
    echo "=========================================="
    
    if [ -f "${PID_FILE}" ]; then
        while read pid; do
            if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo "프로세스 종료: PID $pid"
                kill "$pid" 2>/dev/null || true
            fi
        done < "${PID_FILE}"
        rm -f "${PID_FILE}"
    fi
    
    # 추가 정리
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "python.*http.server.*8080" 2>/dev/null || true
    
    echo "서버가 종료되었습니다."
    exit 0
}

# 시그널 핸들러 등록
trap cleanup SIGINT SIGTERM

# 기존 프로세스 정리
cleanup_existing

echo "=========================================="
echo "AI 흡입기 분석 시스템 시작"
echo "=========================================="
echo ""

# 백엔드 서버 시작
echo "1. 백엔드 서버 시작 중..."
cd "${BACKEND_DIR}"
${PYTHON_CMD} api_server.py > "${BACKEND_LOG}" 2>&1 &
BACKEND_PID=$!
echo "   백엔드 PID: $BACKEND_PID"
echo "   로그: ${BACKEND_LOG}"

# 백엔드 서버 시작 대기
sleep 3

# 백엔드 서버 상태 확인
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✓ 백엔드 서버 실행 중: http://localhost:8000"
else
    echo "   ✗ 백엔드 서버 시작 실패"
    echo "   로그 확인: tail -f ${BACKEND_LOG}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""

# 프론트엔드 서버 시작
echo "2. 프론트엔드 서버 시작 중..."
cd "${FRONTEND_DIR}"
# 0.0.0.0에 바인딩하여 외부 IP에서도 접속 가능하도록 설정
${PYTHON_CMD} -m http.server 8080 --bind 0.0.0.0 > "${FRONTEND_LOG}" 2>&1 &
FRONTEND_PID=$!
echo "   프론트엔드 PID: $FRONTEND_PID"
echo "   로그: ${FRONTEND_LOG}"

# 프론트엔드 서버 시작 대기
sleep 2

# 프론트엔드 서버 상태 확인
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "   ✓ 프론트엔드 서버 실행 중: http://localhost:8080"
else
    echo "   ✗ 프론트엔드 서버 시작 실패"
    echo "   로그 확인: tail -f ${FRONTEND_LOG}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

# PID 파일에 저장
echo "$BACKEND_PID" > "${PID_FILE}"
echo "$FRONTEND_PID" >> "${PID_FILE}"

echo ""
echo "=========================================="
echo "✓ 모든 서버가 실행되었습니다!"
echo "=========================================="
echo ""
echo "서버 정보:"
echo "  - 백엔드 API: http://localhost:8000"
echo "  - 프론트엔드: http://localhost:8080"
echo ""
echo "로그 파일:"
echo "  - 백엔드: tail -f ${BACKEND_LOG}"
echo "  - 프론트엔드: tail -f ${FRONTEND_LOG}"
echo ""
echo "서버를 종료하려면:"
echo "  - Ctrl+C를 누르거나"
echo "  - ./stop_container.sh 실행"
echo ""
echo "=========================================="
echo ""

# 프로세스가 종료될 때까지 대기
wait

