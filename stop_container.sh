#!/bin/bash
# 백엔드와 프론트엔드를 종료하는 스크립트

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="${PROJECT_ROOT}/.server_pids"

echo "=========================================="
echo "서버 종료 중..."
echo "=========================================="
echo ""

# PID 파일에서 프로세스 종료
if [ -f "${PID_FILE}" ]; then
    echo "PID 파일에서 프로세스 확인 중..."
    while read pid; do
        if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "프로세스 종료: PID $pid"
            kill "$pid" 2>/dev/null || true
        fi
    done < "${PID_FILE}"
    rm -f "${PID_FILE}"
    echo ""
fi

# 추가 프로세스 정리
echo "추가 프로세스 정리 중..."

# API 서버 프로세스 종료
pkill -f "api_server.py" 2>/dev/null && echo "  ✓ API 서버 프로세스 종료" || echo "  - API 서버 프로세스 없음"

# Uvicorn 프로세스 종료
pkill -f "uvicorn.*api_server" 2>/dev/null && echo "  ✓ Uvicorn 프로세스 종료" || echo "  - Uvicorn 프로세스 없음"

# HTTP 서버 프로세스 종료 (포트 8080)
# 크로스 플랫폼 지원: macOS와 Linux 모두 지원
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: lsof 사용
    if lsof -ti:8080 > /dev/null 2>&1; then
        lsof -ti:8080 | xargs kill -9 2>/dev/null
        echo "  ✓ 프론트엔드 서버 프로세스 종료"
    else
        echo "  - 프론트엔드 서버 프로세스 없음"
    fi
else
    # Linux/WSL: ss, lsof, 또는 fuser 사용
    FOUND=false
    if command -v ss >/dev/null 2>&1; then
        PIDS=$(ss -tlnp 2>/dev/null | grep :8080 | sed -n 's/.*pid=\([0-9]*\).*/\1/p')
        if [ ! -z "$PIDS" ]; then
            echo "$PIDS" | xargs kill -9 2>/dev/null || true
            echo "  ✓ 프론트엔드 서버 프로세스 종료"
            FOUND=true
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -ti:8080 > /dev/null 2>&1; then
            lsof -ti:8080 | xargs kill -9 2>/dev/null
            echo "  ✓ 프론트엔드 서버 프로세스 종료"
            FOUND=true
        fi
    elif command -v fuser >/dev/null 2>&1; then
        if fuser 8080/tcp >/dev/null 2>&1; then
            fuser -k 8080/tcp 2>/dev/null || true
            echo "  ✓ 프론트엔드 서버 프로세스 종료"
            FOUND=true
        fi
    fi
    
    if [ "$FOUND" = false ]; then
        # 대체 방법: python http.server 프로세스 종료
        if pkill -f "python.*http.server.*8080" 2>/dev/null; then
            echo "  ✓ 프론트엔드 서버 프로세스 종료"
        else
            echo "  - 프론트엔드 서버 프로세스 없음"
        fi
    fi
fi

# 잠시 대기
sleep 1

echo ""
echo "=========================================="
echo "✓ 서버가 종료되었습니다."
echo "=========================================="

