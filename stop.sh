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
if lsof -ti:8080 > /dev/null 2>&1; then
    lsof -ti:8080 | xargs kill -9 2>/dev/null
    echo "  ✓ 프론트엔드 서버 프로세스 종료"
else
    echo "  - 프론트엔드 서버 프로세스 없음"
fi

# 잠시 대기
sleep 1

echo ""
echo "=========================================="
echo "✓ 서버가 종료되었습니다."
echo "=========================================="

