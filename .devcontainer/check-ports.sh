#!/bin/bash
# devcontainer 시작 전 포트 사용 확인 및 정리

PORTS=(8080 8000)

echo "🔍 Checking ports before starting devcontainer..."

for PORT in "${PORTS[@]}"; do
    # 포트 사용 중인 프로세스 찾기
    PID=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ ! -z "$PID" ]; then
        echo "⚠️  Port $PORT is in use by PID: $PID"
        
        # 프로세스 정보 출력
        ps -p $PID -o pid,comm,args 2>/dev/null
        
        echo "   You can kill this process with: kill $PID"
        echo "   Or use: sudo kill -9 $PID (force kill)"
        
        # Docker 컨테이너인지 확인
        CONTAINER=$(docker ps --filter "publish=$PORT" --format "{{.ID}} {{.Names}}" 2>/dev/null)
        if [ ! -z "$CONTAINER" ]; then
            echo "   This is a Docker container: $CONTAINER"
            echo "   You can stop it with: docker stop <container_id>"
        fi
        
        exit 1
    else
        echo "✅ Port $PORT is available"
    fi
done

echo "✅ All ports are available. Safe to start devcontainer."
exit 0
