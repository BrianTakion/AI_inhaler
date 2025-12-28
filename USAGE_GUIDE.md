# AI 흡입기 분석 시스템 사용 가이드

이 문서는 AI 흡입기 분석 시스템의 주요 구성 요소들의 사용법을 설명합니다.

## 목차

1. [초기 설정](#초기-설정)
2. [macOS 서버 설정](#macos-서버-설정)
3. [서버 실행 스크립트](#서버-실행-스크립트)
   - [start_AI_inhaler.sh - 호스트에서 실행 (통합 스크립트)](#start_ai_inhalersh---호스트에서-실행-통합-스크립트)
   - [start_inside_container.sh - 컨테이너 내부에서 직접 실행](#start_inside_containersh---컨테이너-내부에서-직접-실행)
4. [전체 워크플로우](#전체-워크플로우)
5. [app_main.py - 통합 분석 애플리케이션](#app_mainpy---통합-분석-애플리케이션)
6. [api_server.py - FastAPI 백엔드 서버](#api_serverpy---fastapi-백엔드-서버)
7. [test_api_server.py - API 서버 테스트](#test_api_serverpy---api-서버-테스트)
8. [문제 해결](#문제-해결)
9. [추가 정보](#추가-정보)

---

## 초기 설정

시스템을 사용하기 전에 다음 설정을 완료해야 합니다.

### 1. API 키 설정 (필수)

**중요**: `/workspaces/AI_inhaler/app_server/.env` 파일에 API 키를 설정해야 합니다.

#### .env 파일 생성 및 설정

```bash
# app_server 디렉토리로 이동
cd /workspaces/AI_inhaler/app_server

# .env 파일 생성 (이미 존재하는 경우 건너뛰기)
touch .env

# .env 파일 편집
nano .env
# 또는
vim .env
```

#### API 키 기록

`.env` 파일에 다음과 같이 API 키를 기록합니다:

```bash
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
```

**설명:**

- `OPENAI_API_KEY`: OpenAI 모델(`gpt-4.1`, `gpt-5-nano` 등)을 사용하는 경우 필수
- `GOOGLE_API_KEY`: Google Gemini 모델(`gemini-2.5-pro` 등)을 사용하는 경우 필수
- 실제 API 키 값으로 `your-openai-api-key-here`와 `your-google-api-key-here`를 교체해야 합니다
- 사용하지 않는 API는 해당 줄을 비워두거나 주석 처리할 수 있습니다

**API 키 발급:**

- OpenAI: https://platform.openai.com/api-keys
- Google Gemini: https://makersuite.google.com/app/apikey

**확인:**

```bash
# 설정 확인 (키 값은 마스킹하여 출력)
cat app_server/.env | grep -E "OPENAI_API_KEY|GOOGLE_API_KEY"
```

### 2. 의존성 패키지 설치

```bash
# 프로젝트 루트 디렉토리에서
cd /workspaces/AI_inhaler

# 패키지 설치
pip install -r requirements.txt
```

**주요 패키지:**

- `opencv-python-headless`: 비디오/이미지 처리 (WSL/Linux/macOS 호환)
- `fastapi`, `uvicorn`: 웹 서버
- `langchain`, `langgraph`: 멀티 에이전트 시스템
- 기타 의존성은 `requirements.txt` 참조

### 3. 서버 시작

초기 설정이 완료되면 서버를 시작할 수 있습니다:

**호스트에서 실행 (권장):**

```bash
./start_AI_inhaler.sh
```

**컨테이너 내부에서 직접 실행:**

```bash
# 컨테이너 내부 터미널에서
./start_inside_container.sh
```

자세한 내용은 [서버 실행 스크립트](#서버-실행-스크립트) 섹션을 참조하세요.

---

## macOS 서버 설정

macOS 서버 환경에서 추가로 확인할 사항:

### 1. Macmini 서버 접속 설정

원격 Macmini 서버에 접속하여 작업하는 방법:

#### 1.1 Macmini 서버 IP 주소 확인

Macmini 서버에서 IP 주소를 확인하려면:

```bash
# Macmini 서버 터미널에서 실행
# 이더넷 연결인 경우
ifconfig en0 | grep "inet "

# Wi-Fi 연결인 경우
ifconfig en1 | grep "inet "

# 또는 모든 인터페이스 확인
ifconfig | grep "inet " | grep -v 127.0.0.1
```

#### 1.2 Cursor에 SSH Config 설정

Cursor에서 Macmini 서버에 SSH로 접속하기 위한 설정:

1. **SSH Config 파일 편집:**

   - Windows: `C:\Users\<사용자명>\.ssh\config`
   - macOS/Linux: `~/.ssh/config`

2. **다음 내용 추가:**

   ```
   Host jnu-MacMini-1234
       HostName 172.30.1.7
       User jnu
       Port 22
   ```

   **설명:**

   - `Host`: 연결에 사용할 별칭 (원하는 이름으로 변경 가능)
   - `HostName`: Macmini 서버의 IP 주소
   - `User`: SSH 접속할 사용자명
   - `Port`: SSH 포트 (기본값: 22)

3. **접속 테스트:**

   ```bash
   # Cursor 터미널에서
   ssh jnu-MacMini-1234
   ```

4. **Cursor에서 원격 연결:**
   - Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
   - "Remote-SSH: Connect to Host"
   - `jnu-MacMini-1234` 선택

#### 1.3 Docker 데몬 실행 확인

Macmini 서버에서 Docker Desktop이 실행 중인지 확인:

```bash
# Docker Desktop 실행
open -a Docker

# Docker 데몬 상태 확인
docker ps
```

**주의사항:**

- Docker Desktop이 실행되어야 `start_AI_inhaler.sh` 스크립트가 정상 작동합니다
- 로그인 시 자동 실행하려면 Docker Desktop 설정에서 "Start Docker Desktop when you log in" 옵션 활성화

#### 1.4 OpenGL 설치 (필요시)

일부 환경에서 OpenGL 관련 라이브러리가 필요할 수 있습니다:

```bash
# Homebrew로 Mesa 설치
brew install mesa
```

**참고:**

- 이 프로젝트는 `opencv-python-headless`를 사용하므로 일반적으로 OpenGL 설치가 필요하지 않습니다
- 다른 의존성 문제가 있는 경우에만 설치하세요

### 2. 방화벽 설정

macOS 시스템 설정에서 포트를 허용해야 할 수 있습니다:

1. **시스템 설정** → **네트워크** → **방화벽**
2. 방화벽이 활성화되어 있는 경우, 포트 8000과 8080 허용 필요
3. 또는 터미널에서 Python 허용:
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
   ```

### 3. VS Code Dev Container 환경에서의 접속

VS Code Dev Container 환경을 사용하는 경우:

**중요**: `172.17.0.2`는 Docker 컨테이너 내부 IP 주소입니다. Windows 브라우저에서 이 IP로 직접 접근할 수 없습니다.

**올바른 접속 방법:**

1. **VS Code 포트 포워딩 사용 (권장)**:

   - Dev Container는 자동으로 포트를 포워딩합니다 (`.devcontainer/devcontainer.json`의 `forwardPorts: [8080, 8000]`)
   - Windows 브라우저에서 **`http://localhost:8080`** 으로 접속
   - 이 방법이 가장 간단하고 안정적입니다

2. **macOS 호스트 IP 사용** (포트 포워딩이 작동하지 않는 경우):
   - macOS 호스트의 실제 IP 주소를 확인:
     ```bash
     # macOS 터미널에서 실행
     ifconfig | grep "inet " | grep -v 127.0.0.1
     ```
   - 예: `192.168.1.100`인 경우 → `http://192.168.1.100:8080`

**포트 포워딩 확인:**

- VS Code 하단 상태 표시줄에서 "Ports" 탭 확인
- 8080, 8000 포트가 "Forwarded" 상태인지 확인

### 4. Python 인터프리터

macOS에서는 기본적으로 `python3`가 설치되어 있습니다:

- `python3` 명령어 사용 (스크립트에서 자동 선택됨)
- Homebrew를 통해 설치된 Python 사용 가능

---

## 서버 실행 스크립트

서버를 실행하는 방법은 두 가지가 있습니다:

1. **호스트에서 실행 (권장)**: `start_AI_inhaler.sh` - 컨테이너 자동 관리 포함
2. **컨테이너 내부에서 직접 실행**: `start_inside_container.sh`

---

### start_AI_inhaler.sh - 호스트에서 실행 (통합 스크립트)

#### 개요

**호스트(macOS/Linux/WSL)**에서 실행하는 통합 시작 스크립트입니다. 컨테이너가 없으면 자동으로 생성하고, 있으면 포트 매핑을 확인한 후 서버를 시작합니다.

#### 주요 기능

- **Docker 자동 확인**: Docker 설치 및 데몬 실행 상태 확인
- **컨테이너 자동 검색**: 실행 중인 Dev Container 자동 감지
- **컨테이너 자동 생성**: 컨테이너가 없으면 `devcontainer.json` 설정으로 새로 생성
- **포트 매핑 자동 설정**: 8080, 8000 포트 자동 매핑
- **호스트 IP 주소 표시**: 원격 접속을 위한 호스트 IP 주소 안내
- **크로스 플랫폼 지원**: macOS, Linux, WSL 모두 지원

#### 사용 환경

- 호스트 터미널에서 실행 (컨테이너 내부 접속 불필요)
- macOS, Linux, WSL 모두 지원

#### 사전 요구사항

1. **Docker 설치 및 실행**

   - Docker Desktop (macOS) 또는 Docker Engine (Linux/WSL)
   - Docker 데몬이 실행 중이어야 함
   - macOS: `open -a Docker`로 Docker Desktop 시작

2. **devcontainer.json 파일**
   - 프로젝트 루트의 `.devcontainer/devcontainer.json` 파일 필요
   - 이미지 정보, 포트 매핑 설정 포함

#### 사용법

##### 서버 시작

```bash
# 프로젝트 루트 디렉토리에서
./start_AI_inhaler.sh
```

##### 서버 종료

서버를 종료하려면 스크립트가 실행 중인 터미널에서 `Ctrl+C`를 누르세요.

또는 컨테이너 내부에서 직접 종료:

```bash
# 컨테이너 내부 터미널에서
docker exec -it <container-name> bash -c "cd /workspaces/AI_inhaler && pkill -f api_server.py && pkill -f 'python.*http.server.*8080'"
```

#### 실행 과정

1. **Docker 확인** - Docker 설치 및 데몬 실행 상태 확인
2. **컨테이너 검색** - 실행 중인 Dev Container 자동 감지
3. **컨테이너 생성 (필요시)** - 컨테이너가 없으면 `devcontainer.json` 설정으로 새로 생성
4. **포트 매핑 확인** - 8080, 8000 포트 매핑이 없으면 재시작하여 설정
5. **호스트 IP 주소 표시** - 원격 접속을 위한 호스트 IP 주소 안내
6. **서버 시작** - 컨테이너 내부에서 `start_inside_container.sh` 실행

#### 컨테이너 검색 방법

스크립트는 다음 방법으로 컨테이너를 자동으로 찾습니다:

1. 실행 중인 컨테이너 이름 패턴 검색 (`vsc-.*`, `AI_inhaler`)
2. `/workspaces` 경로를 마운트한 컨테이너 검색
3. 중지된 컨테이너도 검색

#### 접속 주소

스크립트 실행 후 다음 주소로 접속할 수 있습니다:

**로컬 접속:**

- 프론트엔드: `http://localhost:8080`
- 백엔드 API: `http://localhost:8000`

**원격 접속 (호스트 IP가 표시된 경우):**

- 프론트엔드: `http://<호스트_IP>:8080`
- 백엔드 API: `http://<호스트_IP>:8000`

**주의**: Docker 내부 IP(172.17.x.x, 172.18.x.x 등)는 표시되지 않으며, 실제 호스트 IP만 표시됩니다.

#### 출력 예시

```
==========================================
AI Inhaler 통합 시작 스크립트
==========================================

컨테이너 찾는 중...
✓ 컨테이너 발견: amazing-username-12345

컨테이너 시작 중...
✓ 컨테이너가 시작되었습니다.

✓ 포트 매핑이 이미 설정되어 있습니다.

==========================================
서버 시작
==========================================
컨테이너: amazing-username-12345
프로젝트: /workspaces/AI_inhaler

호스트 IP 주소: 192.168.1.100

서버 시작 후 원격 브라우저에서 접속:
  - 백엔드 API: http://192.168.1.100:8000
  - 프론트엔드: http://192.168.1.100:8080

==========================================

서버를 종료하려면 Ctrl+C를 누르세요.

start_inside_container.sh 파일 확인 중...
✓ start_inside_container.sh 파일 확인됨

==========================================
AI 흡입기 분석 시스템 시작
==========================================
...
```

#### 컨테이너가 없을 때의 동작

컨테이너가 없는 경우, 스크립트는 자동으로 새 컨테이너를 생성합니다:

1. **devcontainer.json 읽기** - 이미지 정보, 포트 매핑, postCreateCommand 확인
2. **이미지 다운로드** - 필요한 이미지가 없으면 자동 다운로드
3. **컨테이너 생성** - 포트 매핑(8080:8080, 8000:8000) 포함하여 생성
4. **postCreateCommand 실행** - devcontainer.json에 설정된 명령 실행 (있는 경우)

#### 문제 해결

##### Docker 데몬이 실행되지 않는 경우

**macOS:**

```bash
open -a Docker
```

**Linux/WSL:**

```bash
# WSL
sudo service docker start

# Linux
sudo systemctl start docker
```

##### 컨테이너를 찾을 수 없는 경우

스크립트가 자동으로 새 컨테이너를 생성합니다. `devcontainer.json` 파일이 올바른지 확인하세요.

##### 포트 매핑이 설정되지 않은 경우

스크립트가 자동으로 컨테이너를 재시작하여 포트 매핑을 설정합니다. 기존 컨테이너가 재시작될 수 있으니 주의하세요.

##### 호스트 IP 주소를 찾을 수 없는 경우

스크립트는 `localhost`로 접속하는 방법을 안내합니다. 수동으로 IP를 확인하려면:

**macOS:**

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Linux/WSL:**

```bash
hostname -I
# 또는
ip addr show | grep "inet "
```

#### 주의사항

- 호스트에서 실행해도 서버는 **컨테이너 내부**에서 실행됩니다
- 로그 파일은 컨테이너 내부의 `/workspaces/AI_inhaler/logs/`에 저장됩니다
- 컨테이너를 종료하면 서버도 함께 종료됩니다
- 포트 매핑이 없는 기존 컨테이너는 재시작될 수 있습니다

---

### start_inside_container.sh - 컨테이너 내부에서 직접 실행

#### 개요

컨테이너 내부에서 직접 백엔드와 프론트엔드 서버를 동시에 시작하는 스크립트입니다.

#### 사용 환경

- VS Code Dev Container 내부 터미널에서 실행
- 컨테이너에 직접 접속하여 실행
- `start_AI_inhaler.sh`가 내부적으로 호출하는 스크립트

#### 사용법

##### 서버 시작

```bash
# 컨테이너 내부 터미널에서
./start_inside_container.sh
```

##### 서버 종료

```bash
# 서버가 실행 중인 터미널에서
Ctrl+C
```

또는 프로세스 직접 종료:

```bash
# 백엔드 종료
pkill -f api_server.py

# 프론트엔드 종료 (포트 8080)
# macOS
lsof -ti:8080 | xargs kill -9

# Linux/WSL
ss -tlnp | grep :8080 | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | xargs kill -9
```

#### 실행 과정

1. **기존 프로세스 정리** - 실행 중인 서버 프로세스 자동 종료
2. **백엔드 서버 시작** - `api_server.py` 실행 (포트 8000)
3. **백엔드 상태 확인** - 서버가 정상적으로 시작되었는지 확인
4. **프론트엔드 서버 시작** - Python HTTP 서버 실행 (포트 8080, 0.0.0.0에 바인딩)
5. **프론트엔드 상태 확인** - 서버가 정상적으로 시작되었는지 확인

#### 주요 기능

- **자동 프로세스 정리**: 기존 실행 중인 서버 자동 종료
- **상태 확인**: 서버 시작 후 정상 동작 여부 확인 (curl 사용)
- **로그 파일**: 모든 로그를 `logs/` 디렉토리에 저장
  - 백엔드: `logs/backend.log`
  - 프론트엔드: `logs/frontend.log`
- **PID 파일**: `.server_pids` 파일에 프로세스 ID 저장
- **크로스 플랫폼 지원**: WSL, Linux, macOS 모두 지원
- **시그널 핸들러**: Ctrl+C 시 정상 종료

#### 출력 예시

```
==========================================
AI 흡입기 분석 시스템 시작
==========================================

1. 백엔드 서버 시작 중...
   백엔드 PID: 12345
   로그: /workspaces/AI_inhaler/logs/backend.log
   ✓ 백엔드 서버 실행 중: http://localhost:8000

2. 프론트엔드 서버 시작 중...
   프론트엔드 PID: 12346
   로그: /workspaces/AI_inhaler/logs/frontend.log
   ✓ 프론트엔드 서버 실행 중: http://localhost:8080

==========================================
✓ 모든 서버가 실행되었습니다!
==========================================

서버 정보:
  - 백엔드 API: http://localhost:8000
  - 프론트엔드: http://localhost:8080

로그 파일:
  - 백엔드: tail -f /workspaces/AI_inhaler/logs/backend.log
  - 프론트엔드: tail -f /workspaces/AI_inhaler/logs/frontend.log

서버를 종료하려면 Ctrl+C를 누르세요.

==========================================
```

#### 포트 바인딩

프론트엔드 서버는 `0.0.0.0`에 바인딩되어 외부 IP에서도 접속 가능합니다:

```bash
python -m http.server 8080 --bind 0.0.0.0
```

이렇게 하면 컨테이너 외부에서도 접속할 수 있습니다 (포트 매핑이 설정된 경우).

#### 로그 확인

서버 실행 중 로그를 실시간으로 확인하려면:

```bash
# 백엔드 로그
tail -f logs/backend.log

# 프론트엔드 로그
tail -f logs/frontend.log

# 둘 다 동시에
tail -f logs/*.log
```

#### 문제 해결

##### 서버가 시작되지 않는 경우

1. **포트 사용 확인:**

   ```bash
   # 포트 8000
   lsof -i:8000
   # 포트 8080
   lsof -i:8080
   ```

2. **로그 확인:**

   ```bash
   tail -f logs/backend.log
   tail -f logs/frontend.log
   ```

3. **Python 인터프리터 확인:**
   ```bash
   python3 --version
   # 또는
   python --version
   ```

##### 프로세스가 정리되지 않는 경우

```bash
# 모든 서버 프로세스 강제 종료
pkill -9 -f api_server.py
pkill -9 -f "python.*http.server.*8080"

# PID 파일 삭제
rm -f .server_pids
```

---

## 전체 워크플로우

### 1. 시스템 시작

**호스트에서 실행 (권장):**

```bash
# 호스트 터미널에서 (프로젝트 루트 디렉토리)
./start_AI_inhaler.sh
```

이 스크립트는:

- Docker 설치 및 실행 상태 확인
- 컨테이너 자동 검색 또는 생성
- 포트 매핑 자동 설정
- 호스트 IP 주소 표시
- 서버 자동 시작

**컨테이너 내부에서 직접 실행:**

```bash
# 컨테이너 내부 터미널에서
./start_inside_container.sh
```

### 2. 웹 브라우저에서 접속

서버 시작 후 출력된 접속 주소를 사용하세요:

**로컬 접속:**

- 프론트엔드: `http://localhost:8080`
- 백엔드 API: `http://localhost:8000`

**원격 접속 (호스트 IP가 표시된 경우):**

- 프론트엔드: `http://<호스트_IP>:8080`
- 백엔드 API: `http://<호스트_IP>:8000`

**VS Code Dev Container 환경:**

- 포트 포워딩이 자동 설정되므로 `http://localhost:8080` 사용

### 3. 분석 수행

1. 기기 선택
2. 비디오 파일 업로드
3. 분석 시작
4. 결과 확인 및 저장

### 4. 시스템 종료

**호스트에서 시작한 경우:**

```bash
# 서버가 실행 중인 터미널에서
Ctrl+C
```

**컨테이너 내부에서 직접 시작한 경우:**

```bash
# 서버가 실행 중인 터미널에서
Ctrl+C
```

또는 프로세스 직접 종료:

```bash
# 컨테이너 내부에서
pkill -f api_server.py
pkill -f "python.*http.server.*8080"
```

---

## app_main.py - 통합 분석 애플리케이션

### 개요

`app_main.py`는 여러 디바이스 타입에 대해 통합적으로 흡입기 사용법 분석을 수행하는 메인 애플리케이션입니다.

### 주요 기능

- 다양한 디바이스 타입 지원 (pMDI_type1, pMDI_type2, DPI_type1, DPI_type2, DPI_type3, SMI_type1)
- 멀티 LLM 모델 기반 분석
- 개별 에이전트 리포트 생성 옵션
- 분석 결과 요약 출력

### 사용법

#### 1. 직접 실행 (메인 함수 사용)

```bash
cd app_server
python app_main.py
```

**설정 변경:**

`main()` 함수 내의 변수를 수정하여 설정을 변경할 수 있습니다:

```python
# 비디오 파일 경로
video_path = r"/workspaces/AI_inhaler/app_server/test_clip.mp4"

# 디바이스 타입 선택
device_list = ['pMDI_type1', 'pMDI_type2', 'DPI_type1', 'DPI_type2', 'DPI_type3', 'SMI_type1']
device_type = device_list[1]  # 예: pMDI_type2

# LLM 모델 설정
set_llm_models = ['gpt-4.1', 'gpt-4.1']
# 또는
# set_llm_models = ['gpt-4.1', 'gpt-5.1', 'gemini-2.5-pro', 'gemini-3-flash-preview']

# 개별 리포트 저장 여부
save_individual_report = True
```

#### 2. 모듈로 import하여 사용

```python
from app_server import app_main

result = app_main.run_device_analysis(
    device_type="pMDI_type2",
    video_path="/path/to/video.mp4",
    llm_models=["gpt-4.1", "gpt-4.1"],
    save_individual_report=True
)

if result and result.get("status") == "completed":
    print("분석 완료!")
    report = result.get("final_report", {})
    # 결과 처리...
```

### 함수 설명

#### `run_device_analysis(device_type, video_path, llm_models, save_individual_report)`

특정 디바이스 타입에 대한 분석을 실행합니다.

**매개변수:**

- `device_type` (str): 디바이스 타입

  - `pMDI_type1`: Suspension pressurized metered-dose inhaler
  - `pMDI_type2`: Solution pressurized metered-dose inhaler
  - `DPI_type1`: Multi-dose cap-opening dry powder inhaler
  - `DPI_type2`: Multi-dose rotating/button-actuated dry powder inhaler
  - `DPI_type3`: Single-dose capsule-based dry powder inhaler
  - `SMI_type1`: Soft mist inhaler

- `video_path` (str): 분석할 비디오 파일의 절대 경로

- `llm_models` (list): 사용할 LLM 모델 리스트

  - OpenAI 모델: `"gpt-4.1"`, `"gpt-5-nano"`, `"gpt-5.1"`, `"gpt-5.2"`
  - Google 모델: `"gemini-2.5-pro"`, `"gemini-3-flash-preview"`, `"gemini-3-pro-preview"`

- `save_individual_report` (bool): 개별 에이전트 결과물에 대한 시각화 HTML 저장 여부

**반환값:**

```python
{
    "status": "completed" | "error",
    "final_report": {
        "video_info": {...},
        "action_decisions": {...},
        "action_order": [...],
        "action_analysis": {...},
        "final_summary": "...",
        "individual_html_paths": [...]
    },
    "agent_logs": [...],
    "errors": [...],
    "llm_models": [...]
}
```

### 환경 변수 설정

**참고**: API 키 설정은 [초기 설정](#초기-설정) 섹션을 참조하세요.

`.env` 파일(`/workspaces/AI_inhaler/app_server/.env`)에 `OPENAI_API_KEY`와 `GOOGLE_API_KEY`를 설정해야 합니다.

### 출력 예시

```
================================================================================
디바이스 타입: pMDI_type2
================================================================================
[모듈 로드] pMDI_type2 모듈을 독립적으로 로드했습니다.
  - agents.state: /workspaces/AI_inhaler/app_pMDI_type2/agents/state.py
  - graph_workflow: /workspaces/AI_inhaler/app_pMDI_type2/graph_workflow.py

LLM 모델 초기화 (2개):
  1. gpt-4.1
  2. gpt-4.1

분석할 비디오: /workspaces/AI_inhaler/app_server/test_clip.mp4

✅ 분석이 성공적으로 완료되었습니다!

==================================================
=== 비디오 분석 결과 요약 ===
==================================================

[비디오 정보]
  파일명: test_clip.mp4
  재생시간: 45.2초
  총 프레임: 1356
  해상도: 1920x1080px

[최종 판단 결과]
  sit_stand: SUCCESS (1)
  shake: SUCCESS (1)
  ...

[최종 종합 기술]
  환자는 흡입기를 올바르게 사용했습니다...
```

---

## api_server.py - FastAPI 백엔드 서버

### 개요

`api_server.py`는 FastAPI 기반의 RESTful API 서버로, 프론트엔드와 백엔드 분석 로직을 연결합니다.

### 주요 기능

- 비디오 파일 업로드
- 비동기 분석 작업 실행
- 분석 상태 조회
- 분석 결과 조회
- 결과 다운로드 (JSON)

### 사용법

#### 1. 서버 시작

```bash
cd app_server
python api_server.py
```

또는 uvicorn으로 직접 실행:

```bash
cd app_server
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

#### 2. 서버 확인

```bash
curl http://localhost:8000/
```

응답:

```json
{
  "message": "AI Inhaler Analysis API",
  "version": "1.0.0"
}
```

### API 엔드포인트

#### 1. 서버 상태 확인

```http
GET /
```

**응답:**

```json
{
  "message": "AI Inhaler Analysis API",
  "version": "1.0.0"
}
```

#### 2. 서버 설정 정보 조회

```http
GET /api/config
```

**응답:**

```json
{
  "llmModels": ["gpt-4.1", "gpt-4.1"],
  "version": "1.0.0"
}
```

#### 3. 비디오 업로드

```http
POST /api/video/upload
Content-Type: multipart/form-data
```

**요청:**

- `file`: 비디오 파일 (MP4, MOV, AVI, MKV)

**응답:**

```json
{
  "videoId": "uuid-string",
  "thumbnail": "",
  "metadata": {
    "fileName": "video.mp4",
    "duration": 0,
    "size": 12345678,
    "resolution": "",
    "type": "video/mp4",
    "width": 0,
    "height": 0
  }
}
```

**예제 (curl):**

```bash
curl -X POST http://localhost:8000/api/video/upload \
  -F "file=@/path/to/video.mp4"
```

#### 4. 분석 시작

```http
POST /api/analysis/start
Content-Type: application/json
```

**요청 본문:**

```json
{
  "videoId": "uuid-string",
  "deviceType": "pMDI_type2",
  "saveIndividualReport": true
}
```

**응답:**

```json
{
  "analysisId": "uuid-string",
  "estimatedTime": 300
}
```

**예제 (curl):**

```bash
curl -X POST http://localhost:8000/api/analysis/start \
  -H "Content-Type: application/json" \
  -d '{
    "videoId": "video-uuid",
    "deviceType": "pMDI_type2",
    "saveIndividualReport": true
  }'
```

#### 5. 분석 상태 조회

```http
GET /api/analysis/status/{analysis_id}
```

**응답:**

```json
{
  "status": "processing",
  "progress": 45,
  "current_stage": "비디오 분석 중...",
  "logs": ["[10:30:15] 분석 시작", "[10:30:20] 비디오 로드 완료"],
  "error": null
}
```

**상태 값:**

- `pending`: 대기 중
- `processing`: 처리 중
- `completed`: 완료
- `error`: 오류 발생

#### 6. 분석 결과 조회

```http
GET /api/analysis/result/{analysis_id}
```

**응답:**

```json
{
  "status": "completed",
  "deviceType": "pMDI_type2",
  "videoInfo": {
    "fileName": "video.mp4",
    "duration": 45.2,
    "resolution": "1920x1080",
    "frameCount": 1356
  },
  "actionSteps": [
    {
      "id": "sit_stand",
      "order": 1,
      "name": "sit_stand",
      "description": "...",
      "time": [5.2, 10.5],
      "score": [1],
      "result": "pass"
    }
  ],
  "summary": {
    "totalSteps": 10,
    "passedSteps": 8,
    "failedSteps": 2,
    "score": 80.0
  },
  "modelInfo": {
    "models": ["gpt-4.1", "gpt-4.1"],
    "analysisTime": 180
  },
  "finalSummary": "최종 종합 기술 텍스트...",
  "individualHtmlPaths": ["/path/to/agent1.html", "/path/to/agent2.html"]
}
```

#### 7. 결과 다운로드

```http
GET /api/analysis/download/{analysis_id}?format=json
```

**응답:** JSON 파일 다운로드

### LLM 모델 설정

`api_server.py` 파일 상단에서 고정된 LLM 모델을 설정할 수 있습니다:

```python
# 고정된 LLM 모델 설정
FIXED_LLM_MODELS = ["gpt-4.1", "gpt-4.1"]
```

**참고:** 프론트엔드 요청의 `llmModels`는 무시되고, 서버의 `FIXED_LLM_MODELS`가 항상 사용됩니다.

### 업로드 디렉토리

업로드된 비디오 파일은 다음 디렉토리에 저장됩니다:

```
{project_root}/uploads/{video_id}.{extension}
```

### CORS 설정

개발 환경에서는 모든 origin을 허용하도록 설정되어 있습니다:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**프로덕션 환경에서는 특정 origin만 허용하도록 변경하는 것을 권장합니다.**

---

## test_api_server.py - API 서버 테스트

### 개요

`test_api_server.py`는 API 서버의 전체 분석 플로우를 테스트하고 최종 결과를 검증하는 테스트 스크립트입니다.

### 사용법

#### 1. 기본 실행

```bash
cd app_server
python test_api_server.py
```

#### 2. 테스트 설정 변경

스크립트 상단의 `TEST_CONFIG`를 수정하여 테스트 설정을 변경할 수 있습니다:

```python
TEST_CONFIG = {
    "video_path": "/workspaces/AI_inhaler/app_server/test_clip.mp4",
    "device_type": "pMDI_type2",
    "save_individual_report": True
}
```

#### 3. 서버 URL 변경

기본 URL이 `http://localhost:8000/api`가 아닌 경우:

```python
BASE_URL = "http://your-server:8000/api"
tester = APIAnalysisTester(base_url=BASE_URL)
```

### 테스트 단계

스크립트는 다음 단계를 순차적으로 실행합니다:

1. **서버 상태 확인** - 서버가 실행 중인지 확인
2. **서버 설정 정보 조회** - LLM 모델 정보 확인
3. **비디오 업로드** - 테스트 비디오 파일 업로드
4. **분석 시작** - 분석 작업 시작
5. **분석 진행 상태 모니터링** - 분석 완료까지 상태 폴링
6. **분석 결과 조회** - 최종 결과 가져오기
7. **결과 데이터 검증** - 필수 필드 존재 여부 확인
8. **app_main.py 출력 형식과 비교** - 결과 형식 검증
9. **결과 저장** - `test_analysis_result.json` 파일로 저장

### 출력 예시

```
================================================================================
API 서버 완전 분석 테스트 시작
================================================================================
테스트 설정:
  - 비디오: test_clip.mp4
  - 디바이스 타입: pMDI_type2
  - 개별 리포트 저장: True

================================================================================
1. 서버 상태 확인
================================================================================
✓ 서버 실행 중: AI Inhaler Analysis API (v1.0.0)

================================================================================
2. 서버 설정 정보 조회
================================================================================
✓ 설정 정보 조회 성공
  버전: 1.0.0
  LLM 모델: ['gpt-4.1', 'gpt-4.1']
✓ LLM 모델 검증 통과 (2개 모델)

================================================================================
3. 비디오 업로드
================================================================================
업로드할 파일: test_clip.mp4
파일 크기: 12.34 MB
✓ 비디오 업로드 성공
  Video ID: abc123...
  파일명: test_clip.mp4
  파일 크기: 12.34 MB

...

================================================================================
5. 분석 진행 상태 모니터링
================================================================================
[00:00] 상태: processing   | 진행률:   0% | 분석 초기화 중...
[00:05] 상태: processing   | 진행률:  10% | 비디오 로드 중...
[00:10] 상태: processing   | 진행률:  25% | 프레임 분석 중...
...

✓ 분석 완료! (소요 시간: 180초)

================================================================================
6. 분석 결과 조회 및 검증
================================================================================
✓ 결과 조회 성공

================================================================================
7. 결과 데이터 검증
================================================================================
필수 필드 검증:
  ✓ status: 존재
  ✓ deviceType: 존재
  ✓ videoInfo: 존재
  ...
```

### 주요 설정

- **최대 대기 시간**: `MAX_WAIT_TIME = 1800` (30분)
- **상태 확인 간격**: `POLL_INTERVAL = 5` (5초)

### 결과 파일

테스트 완료 후 `test_analysis_result.json` 파일이 생성됩니다.

### 오류 처리

서버가 실행되지 않은 경우:

```
✗ 서버 연결 실패: Connection refused

해결 방법:
  1. 서버를 시작하세요:
     cd app_server
     python api_server.py

  2. 또는 백그라운드로 실행:
     cd app_server
     python api_server.py > /tmp/api_server.log 2>&1 &

  3. 서버가 실행 중인지 확인:
     curl http://localhost:8000/
```

---

## 문제 해결

### 백엔드 서버가 시작되지 않는 경우

1. 포트 8000이 이미 사용 중인지 확인:

   ```bash
   lsof -i:8000
   ```

2. 로그 확인:

   ```bash
   tail -f logs/backend.log
   ```

3. **API 키 설정 확인 (중요)**:

   ```bash
   # .env 파일이 존재하는지 확인
   ls -la app_server/.env

   # .env 파일 내용 확인
   cat app_server/.env
   ```

   **필수 확인 사항:**

   - `/workspaces/AI_inhaler/app_server/.env` 파일이 존재해야 합니다
   - `OPENAI_API_KEY` 또는 `GOOGLE_API_KEY`가 설정되어 있어야 합니다
   - 사용하려는 LLM 모델에 맞는 API 키가 설정되어 있어야 합니다
   - API 키 값 앞뒤에 공백이나 따옴표가 없어야 합니다

### API 키 관련 오류

**증상:**

- 분석 시작 후 오류 발생
- 로그에 API 인증 오류 메시지

**원인:**

- `.env` 파일이 없거나 경로가 잘못됨
- API 키가 설정되지 않음
- API 키가 잘못됨 (만료, 잘못된 형식 등)

**해결 방법:**

1. `.env` 파일 경로 확인:

   - 정확한 경로: `/workspaces/AI_inhaler/app_server/.env`
   - `app_server` 디렉토리 내부에 있어야 함

2. API 키 확인:

   ```bash
   # 파일 존재 확인
   ls -la /workspaces/AI_inhaler/app_server/.env

   # 파일 내용 확인 (키 값은 보안상 마스킹됨)
   grep -E "OPENAI_API_KEY|GOOGLE_API_KEY" /workspaces/AI_inhaler/app_server/.env
   ```

3. API 키 재설정:
   - OpenAI API 키: https://platform.openai.com/api-keys
   - Google API 키: https://makersuite.google.com/app/apikey
4. 서버 재시작:
   ```bash
   # 현재 실행 중인 서버 종료 (Ctrl+C)
   # 그 다음 다시 시작
   ./start_AI_inhaler.sh
   ```

### 프론트엔드 서버가 시작되지 않는 경우

1. 포트 8080이 이미 사용 중인지 확인:

   ```bash
   lsof -i:8080
   ```

2. 로그 확인:
   ```bash
   tail -f logs/frontend.log
   ```

### 분석이 완료되지 않는 경우

1. 백엔드 로그 확인:

   ```bash
   tail -f logs/backend.log
   ```

2. API 서버 상태 확인:

   ```bash
   curl http://localhost:8000/
   ```

3. 테스트 스크립트 실행:
   ```bash
   cd app_server
   python test_api_server.py
   ```

### OpenCV 관련 오류 (libGL.so.1 오류)

**증상:**

```
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

**원인:**

- `opencv-python` 패키지를 사용한 경우 발생
- macOS에서는 `libGL.so.1` 라이브러리가 없음
- WSL/Linux에서도 일부 환경에서는 누락될 수 있음

**해결 방법:**

1. `opencv-python-headless` 사용 (권장):

   ```bash
   pip uninstall opencv-python
   pip install opencv-python-headless>=4.10.0,<5.0.0
   ```

2. `requirements.txt` 확인:
   - `opencv-python` 대신 `opencv-python-headless`가 명시되어 있는지 확인
   - 수정 후 재설치: `pip install -r requirements.txt`

**참고:**

- 이 프로젝트는 GUI 기능을 사용하지 않으므로 `opencv-python-headless`로 충분합니다.
- 모든 플랫폼(WSL, Linux, macOS)에서 동일하게 동작합니다.

---

## 추가 정보

- 프로젝트 루트: `/workspaces/AI_inhaler`
- 백엔드 디렉토리: `app_server/`
- 프론트엔드 디렉토리: `webUX/`
- 업로드 디렉토리: `uploads/`
- 로그 디렉토리: `logs/`

### 주요 의존성 패키지

#### OpenCV (opencv-python-headless)

이 프로젝트는 **`opencv-python-headless`** 패키지를 사용합니다.

**사용 이유:**

- 서버 환경(디스플레이 없음)에 최적화
- GUI 의존성(`libGL.so.1` 등) 없이 동작
- WSL, Linux, macOS 모든 플랫폼에서 정상 작동
- 비디오/이미지 처리 기능은 `opencv-python`과 동일

**지원 기능:**

- `cv2.VideoCapture` - 비디오 파일 읽기
- `cv2.imread` - 이미지 읽기
- `cv2.imwrite` - 이미지 저장
- `cv2.imencode` - 이미지 인코딩
- `cv2.cvtColor` - 색상 변환
- `cv2.resize` - 이미지 크기 조정
- `cv2.VideoWriter` - 비디오 파일 쓰기

**주의사항:**

- `cv2.imshow()`, `cv2.waitKey()` 등 GUI 기능은 사용 불가
- 현재 코드베이스에서는 GUI 기능을 사용하지 않으므로 문제 없음

**설치:**

```bash
pip install opencv-python-headless>=4.10.0,<5.0.0
```

**macOS 환경에서의 이점:**

- `libGL.so.1` 오류 없이 동작
- 추가 시스템 라이브러리 설치 불필요

---

## 라이선스 및 저작권

이 문서는 AI 흡입기 분석 시스템의 사용 가이드입니다.
