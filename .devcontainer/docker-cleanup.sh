#!/bin/bash
# Docker 정기 유지보수 스크립트
# 주기적으로 실행하여 Docker 리소스 정리

echo "🧹 Starting Docker cleanup..."

# 1. 중지된 컨테이너 정리
echo "📦 Removing stopped containers..."
STOPPED=$(docker ps -a -q -f status=exited 2>/dev/null)
if [ ! -z "$STOPPED" ]; then
    docker rm $STOPPED
    echo "   ✅ Removed $(echo $STOPPED | wc -w) stopped containers"
else
    echo "   ℹ️  No stopped containers to remove"
fi

# 2. 사용하지 않는 이미지 정리
echo "🖼️  Removing dangling images..."
DANGLING=$(docker images -f "dangling=true" -q 2>/dev/null)
if [ ! -z "$DANGLING" ]; then
    docker rmi $DANGLING
    echo "   ✅ Removed $(echo $DANGLING | wc -w) dangling images"
else
    echo "   ℹ️  No dangling images to remove"
fi

# 3. 사용하지 않는 네트워크 정리
echo "🌐 Removing unused networks..."
docker network prune -f

# 4. 사용하지 않는 볼륨 정리 (주의: 데이터 손실 가능)
echo "💾 Checking for unused volumes..."
VOLUMES=$(docker volume ls -q -f dangling=true 2>/dev/null)
if [ ! -z "$VOLUMES" ]; then
    echo "   ⚠️  Found unused volumes. Run 'docker volume prune -f' to remove them."
    echo "   Warning: This will delete data in unused volumes!"
else
    echo "   ℹ️  No unused volumes found"
fi

# 5. 디스크 사용량 확인
echo ""
echo "📊 Current Docker disk usage:"
docker system df

echo ""
echo "✅ Docker cleanup completed!"
