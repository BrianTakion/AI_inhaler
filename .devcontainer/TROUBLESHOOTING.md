# Devcontainer 문제 해결 가이드

## 일반적인 문제와 해결 방법

### 1. 컨테이너 시작 실패 (Port Already in Use)

#### 증상
```
Failed to install Cursor server: Failed to run devcontainer command
Error: address already in use
```

#### 원인
- 포트 8080 또는 8000이 다른 프로세스나 컨테이너에서 사용 중

#### 해결 방법

**방법 1: 포트 확인 스크립트 실행**
```bash
./.devcontainer/check-ports.sh
```

**방법 2: 수동으로 포트 사용 확인**
```bash
# 포트 8000 사용 중인 프로세스 확인
sudo lsof -i:8000
# 또는
sudo netstat -tlnp | grep :8000

# 프로세스 종료
sudo kill -9 <PID>

# Docker 컨테이너가 포트를 점유 중인 경우
docker ps | grep 8000
docker stop <container_id>
```

---

### 2. 컨테이너 Exit 128 에러

#### 증상
```
Container exited with code 128
```

#### 원인
- 잘못된 종료 시그널
- 네트워크 문제
- 리소스 부족

#### 해결 방법

**1단계: 문제 컨테이너 제거**
```bash
# 모든 컨테이너 확인
docker ps -a

# 문제 컨테이너 제거
docker rm -f <container_id>
```

**2단계: Docker 리소스 정리**
```bash
# 자동 정리 스크립트 실행
./.devcontainer/docker-cleanup.sh

# 또는 수동 정리
docker system prune -f
docker network prune -f
```

**3단계: Devcontainer 재시작**
- Cursor에서 `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

---

### 3. Broken Pipe 에러

#### 증상
```
Error: write unix /run/docker.sock: write: broken pipe
```

#### 원인
- Docker 데몬과 클라이언트 간 통신 중단
- 네트워크 불안정

#### 해결 방법

**Docker 서비스 재시작**
```bash
# WSL2의 경우
sudo systemctl restart docker

# 또는 Docker Desktop 재시작
```

---

### 4. Sandbox Not Found

#### 증상
```
error locating sandbox id: sandbox not found
```

#### 원인
- 컨테이너가 비정상 종료되어 네트워크 샌드박스가 정리되지 않음

#### 해결 방법
```bash
# 네트워크 정리
docker network prune -f

# Docker 재시작
sudo systemctl restart docker
```

---

## 예방적 유지보수

### 정기적인 정리 (주 1회 권장)
```bash
# Docker 리소스 정리
./.devcontainer/docker-cleanup.sh

# 또는
docker system prune -a -f --volumes
```

### Devcontainer 시작 전 체크리스트
1. ✅ 포트 사용 여부 확인: `./.devcontainer/check-ports.sh`
2. ✅ Docker 디스크 공간 확인: `docker system df`
3. ✅ 중지된 컨테이너 정리: `docker ps -a`

---

## 추가 리소스

### Docker 디스크 사용량 확인
```bash
docker system df
```

### 현재 실행 중인 컨테이너 확인
```bash
docker ps
```

### Docker 로그 확인
```bash
# 특정 컨테이너 로그
docker logs <container_id>

# 시스템 로그
journalctl -u docker --since "1 hour ago"
```

---

## 개선 사항 (적용됨)

### devcontainer.json 변경사항
- ✅ `shutdownAction: "stopContainer"`: 깔끔한 종료 보장
- ✅ `forwardPorts` 사용: devcontainer가 자동으로 포트 매핑 관리
- ✅ `runArgs`에서 중복 포트 설정 제거: 충돌 방지

이 설정들은 포트 충돌과 컨테이너 시작 실패 문제를 방지합니다.

---

## 알려진 문제 해결

### "Command failed: docker run --rm" 에러

#### 증상
```
Command failed: docker run --sig-proxy=false ... --rm -p 8080:8080
An error occurred setting up the container.
```

#### 원인
- `--rm` 플래그가 devcontainer의 실행 방식과 충돌
- `runArgs`에 포트 매핑을 중복 지정하면 충돌 발생

#### 해결됨
- `runArgs`에서 `--rm` 플래그 제거
- 포트 매핑은 `forwardPorts`만 사용하도록 변경
