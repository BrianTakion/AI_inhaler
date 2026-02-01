# AI 흡입기 분석 시스템 사용 가이드

이 문서는 AI 흡입기 분석 시스템의 설치, 설정, 실행 방법을 설명합니다.

## 목차

1. [빠른 시작](#빠른-시작)
2. [시스템 요구사항](#시스템-요구사항)
3. [설치 및 설정](#설치-및-설정)
4. [서버 운영](#서버-운영)
5. [분석 워크플로우](#분석-워크플로우)
6. [API 레퍼런스](#api-레퍼런스)
7. [서버 설정](#서버-설정)
8. [플랫폼별 설정](#플랫폼별-설정)
9. [문제 해결](#문제-해결)
10. [참고 정보](#참고-정보)

---

## 빠른 시작

### 1단계: API 키 설정

```bash
cd /workspaces/AI_inhaler/app_server

cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
EOF
```

- `OPENAI_API_KEY`: OpenAI 모델 사용 시 필수 ([발급](https://platform.openai.com/api-keys))
- `GOOGLE_API_KEY`: Google Gemini 모델 사용 시 필수 ([발급](https://makersuite.google.com/app/apikey))

### 2단계: 의존성 패키지 설치

```bash
cd /workspaces/AI_inhaler
pip install -r requirements.txt
```

### 3단계: 서버 시작

```bash
./start_AI_inhaler.sh --detach    # 백그라운드 실행 (권장)
```

### 접속

- **프론트엔드**: `http://localhost:8080`
- **백엔드 API**: `http://localhost:8000`

> 상세 설정은 [설치 및 설정](#설치-및-설정), 서버 운영 옵션은 [서버 운영](#서버-운영) 참조

---

## 시스템 요구사항

### 필수 소프트웨어

| 소프트웨어 | 요구 버전 |
|---|---|
| Docker | Docker Desktop (macOS) 또는 Docker Engine (Linux/WSL) |
| Python | 3.8 이상 |
| 패키지 | `requirements.txt` 참조 |

### 지원 플랫폼

- **macOS**: Intel 및 Apple Silicon
- **Linux**: Ubuntu 20.04 이상 권장
- **WSL**: Windows Subsystem for Linux 2 (WSL2)

### 네트워크 포트

| 포트 | 용도 |
|---|---|
| 8000 | 백엔드 API 서버 (FastAPI) |
| 8080 | 프론트엔드 웹 서버 (Python HTTP) |

---

## 설치 및 설정

### 1. API 키 설정 (필수)

`.env` 파일을 `app_server/` 디렉토리에 생성합니다:

```bash
cd /workspaces/AI_inhaler/app_server
nano .env
```

파일 내용:

```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

| 키 | 대상 모델 | 필수 여부 |
|---|---|---|
| `OPENAI_API_KEY` | `gpt-4.1`, `gpt-5-nano`, `gpt-5.1` 등 | OpenAI 모델 사용 시 |
| `GOOGLE_API_KEY` | `gemini-2.5-pro`, `gemini-3-flash-preview` 등 | Google 모델 사용 시 |

설정 확인:

```bash
ls -la /workspaces/AI_inhaler/app_server/.env
grep -E "OPENAI_API_KEY|GOOGLE_API_KEY" /workspaces/AI_inhaler/app_server/.env
```

### 2. 의존성 패키지 설치

```bash
cd /workspaces/AI_inhaler
pip install -r requirements.txt
```

주요 패키지:

- `opencv-python-headless` - 비디오/이미지 처리 (GUI 의존성 없음)
- `fastapi`, `uvicorn` - 웹 서버
- `langchain`, `langgraph` - 멀티 에이전트 시스템
- `openai` - OpenAI API 클라이언트
- `google-genai` - Google Gemini API 클라이언트

---

## 서버 운영

### 명령어 요약

| 명령어 | 설명 |
|---|---|
| `./start_AI_inhaler.sh` | 포그라운드 실행 (Ctrl+C로 종료) |
| `./start_AI_inhaler.sh --detach` | 백그라운드 실행 (SSH 종료해도 서버 유지) |
| `./start_AI_inhaler.sh -d` | `--detach` 단축 옵션 |
| `./start_AI_inhaler.sh --stop` | 서버 종료 (포그라운드/백그라운드 모두) |
| `./start_AI_inhaler.sh --status` | 서버 실행 상태 확인 |

> 컨테이너 내부에서 직접 실행할 경우: `./start_inside_container.sh`

### 서버 시작

**백그라운드 실행 (권장):**

```bash
./start_AI_inhaler.sh --detach
```

SSH 터미널을 종료해도 서버가 계속 실행됩니다. 리눅스 서버에 SSH로 접속하여 서비스를 운영하는 경우 이 방식을 사용하세요.

**포그라운드 실행:**

```bash
./start_AI_inhaler.sh
```

터미널에 로그가 실시간 출력되며, `Ctrl+C`로 종료합니다.

### 서버 종료

```bash
./start_AI_inhaler.sh --stop
```

컨테이너 내부의 `api_server.py`, `http.server`(8080), `start_inside_container.sh` 프로세스를 모두 종료합니다. 포그라운드/백그라운드 구분 없이 실행 중인 모든 서버를 종료합니다.

### 서버 상태 확인

```bash
./start_AI_inhaler.sh --status
```

컨테이너 실행 여부, 백엔드 API(8000), 프론트엔드(8080) 서버의 동작 상태를 확인합니다.

### 로그 확인

```bash
# 백엔드 로그
tail -f logs/backend.log

# 프론트엔드 로그
tail -f logs/frontend.log

# 호스트에서 컨테이너 내부 로그 확인
docker exec <컨테이너명> tail -f /workspaces/AI_inhaler/logs/backend.log
docker exec <컨테이너명> tail -f /workspaces/AI_inhaler/logs/frontend.log
```

### 접속 주소

**로컬 접속:**

- 프론트엔드: `http://localhost:8080`
- 백엔드 API: `http://localhost:8000`

**원격 접속 (호스트 IP가 표시된 경우):**

- 프론트엔드: `http://<호스트_IP>:8080`
- 백엔드 API: `http://<호스트_IP>:8000`

**VS Code Dev Container 환경:**

- 포트 포워딩이 자동 설정되므로 `http://localhost:8080` 사용

> Docker 내부 IP(172.17.x.x 등)는 외부에서 접근할 수 없습니다. `start_AI_inhaler.sh`가 실제 호스트 IP를 자동으로 표시합니다.

### 스크립트 내부 동작

`start_AI_inhaler.sh`는 다음 과정을 자동 수행합니다:

1. Docker 설치 및 데몬 실행 상태 확인
2. AI Inhaler 컨테이너 자동 검색 (실행 중/중지된 컨테이너 모두)
3. 컨테이너가 없으면 `devcontainer.json` 설정으로 새 컨테이너 생성
4. 포트 매핑(8080, 8000) 확인 및 자동 설정
5. 호스트 IP 주소 표시
6. 컨테이너 내부에서 `start_inside_container.sh` 실행

`start_inside_container.sh`는 컨테이너 내부에서:

1. 기존 서버 프로세스 자동 정리
2. 백엔드 서버 시작 (`api_server.py`, 포트 8000)
3. 프론트엔드 서버 시작 (`python -m http.server 8080 --bind 0.0.0.0`)
4. 각 서버 정상 시작 여부 확인
5. PID 파일(`.server_pids`)에 프로세스 ID 저장
6. `SIGINT`/`SIGTERM` 시그널 핸들러로 정상 종료 처리

---

## 분석 워크플로우

### 1. 기기 선택

웹 UI(`http://localhost:8080`)에서 흡입기 타입을 선택합니다.

지원 디바이스:

| 타입 | 설명 |
|---|---|
| `pMDI_type1` | Suspension pressurized metered-dose inhaler |
| `pMDI_type2` | Solution pressurized metered-dose inhaler |
| `DPI_type1` | Multi-dose cap-opening dry powder inhaler |
| `DPI_type2` | Multi-dose rotating/button-actuated dry powder inhaler |
| `DPI_type3` | Single-dose capsule-based dry powder inhaler |
| `SMI_type1` | Soft mist inhaler |

### 2. 비디오 업로드

분석할 비디오 파일을 업로드합니다 (최대 500MB, MP4/MOV/AVI/MKV).

### 3. 분석 실행 및 결과 확인

분석을 시작하면 진행 상황을 모니터링할 수 있으며, 완료 후 결과를 확인하고 저장합니다.

**다중 사용자 지원:**

- 여러 사용자가 동시에 분석 요청 가능 (최대 5개 동시 실행)
- 초과 시 자동 대기, 완료 후 순차 시작
- 각 분석은 독립 프로세스에서 실행되어 서로 간섭 없음
- 서버 상태 모니터링: `http://localhost:8000/api/stats`

---

## API 레퍼런스

### api_server.py - FastAPI 백엔드 서버

FastAPI 기반 RESTful API 서버로, 프론트엔드와 분석 로직을 연결합니다.

#### 엔드포인트 요약

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 서버 상태 확인 |
| `GET` | `/api/config` | 서버 설정 정보 조회 |
| `POST` | `/api/video/upload` | 비디오 파일 업로드 |
| `POST` | `/api/analysis/start` | 분석 시작 |
| `GET` | `/api/analysis/status/{id}` | 분석 상태 조회 |
| `GET` | `/api/analysis/result/{id}` | 분석 결과 조회 |
| `GET` | `/api/analysis/download/{id}` | 결과 다운로드 (JSON) |
| `GET` | `/api/stats` | 서버 상태 통계 |

#### GET /

서버 상태 확인.

```json
{"message": "AI Inhaler Analysis API", "version": "1.0.0"}
```

#### GET /api/config

서버 설정 정보 조회.

```json
{"llmModels": ["gpt-4.1", "gpt-4.1"], "version": "1.0.0"}
```

#### POST /api/video/upload

비디오 파일 업로드. `multipart/form-data` 형식.

- 허용 확장자: `.mp4`, `.mov`, `.avi`, `.mkv`
- 최대 파일 크기: 500MB
- 스트리밍 방식으로 실시간 크기 검증

```bash
curl -X POST http://localhost:8000/api/video/upload \
  -F "file=@/path/to/video.mp4"
```

응답:

```json
{
  "videoId": "uuid-string",
  "thumbnail": "",
  "metadata": {"fileName": "video.mp4", "duration": 0, "size": 12345678, "type": "video/mp4"}
}
```

#### POST /api/analysis/start

분석 시작.

```bash
curl -X POST http://localhost:8000/api/analysis/start \
  -H "Content-Type: application/json" \
  -d '{"videoId": "uuid", "deviceType": "pMDI_type2", "saveIndividualReport": true}'
```

응답:

```json
{"analysisId": "uuid-string", "estimatedTime": 300}
```

#### GET /api/analysis/status/{analysis_id}

분석 상태 조회.

```json
{
  "status": "processing",
  "progress": 45,
  "current_stage": "비디오 분석 중...",
  "logs": ["[10:30:15] 분석 시작", "[10:30:20] 비디오 로드 완료"],
  "error": null
}
```

상태 값: `pending` | `processing` | `completed` | `error`

#### GET /api/analysis/result/{analysis_id}

분석 결과 조회.

```json
{
  "status": "completed",
  "deviceType": "pMDI_type2",
  "videoInfo": {"fileName": "video.mp4", "duration": 45.2, "resolution": "1920x1080", "frameCount": 1356},
  "actionSteps": [...],
  "summary": {"totalSteps": 10, "passedSteps": 8, "failedSteps": 2, "score": 80.0},
  "modelInfo": {"models": ["gpt-4.1", "gpt-4.1"], "analysisTime": 180},
  "finalSummary": "최종 종합 기술 텍스트...",
  "individualHtmlPaths": ["/path/to/agent1.html"]
}
```

#### GET /api/analysis/download/{analysis_id}?format=json

분석 결과 JSON 파일 다운로드.

#### GET /api/stats

서버 상태 통계 조회.

```json
{
  "currentAnalyses": 2,
  "maxConcurrentAnalyses": 5,
  "activeAnalyses": 2,
  "completedAnalyses": 15,
  "errorAnalyses": 1,
  "uploadedFiles": 18,
  "uploadedSizeMB": 1250.5,
  "processTimeoutSeconds": 1800,
  "cleanupDurationHours": 24
}
```

### app_main.py - 통합 분석 애플리케이션

여러 디바이스 타입에 대해 통합적으로 흡입기 사용법 분석을 수행합니다.

#### 직접 실행

```bash
cd app_server
python app_main.py
```

`main()` 함수 내의 변수를 수정하여 설정을 변경:

```python
video_path = r"/workspaces/AI_inhaler/app_server/test_clip.mp4"
device_type = 'pMDI_type2'
set_llm_models = ['gpt-4.1', 'gpt-4.1']
save_individual_report = True
```

#### 모듈로 import

```python
from app_server import app_main

result = app_main.run_device_analysis(
    device_type="pMDI_type2",
    video_path="/path/to/video.mp4",
    llm_models=["gpt-4.1", "gpt-4.1"],
    save_individual_report=True
)
```

#### run_device_analysis() 매개변수

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `device_type` | str | 디바이스 타입 (`pMDI_type1`, `pMDI_type2`, `DPI_type1`~`3`, `SMI_type1`) |
| `video_path` | str | 분석할 비디오 파일의 절대 경로 |
| `llm_models` | list | 사용할 LLM 모델 리스트 |
| `save_individual_report` | bool | 개별 에이전트 HTML 리포트 저장 여부 |

사용 가능한 LLM 모델:

- **OpenAI**: `gpt-4.1`, `gpt-5-nano`, `gpt-5.1`, `gpt-5.2`
- **Google**: `gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3-pro-preview`

#### 반환값

```python
{
    "status": "completed" | "error",
    "final_report": {
        "video_info": {...}, "action_decisions": {...}, "action_order": [...],
        "action_analysis": {...}, "final_summary": "...", "individual_html_paths": [...]
    },
    "agent_logs": [...], "errors": [...], "llm_models": [...]
}
```

### test_api_server.py - API 서버 테스트

API 서버의 전체 분석 플로우를 테스트하고 결과를 검증합니다.

```bash
cd app_server
python test_api_server.py
```

테스트 단계: 서버 상태 확인 -> 설정 조회 -> 비디오 업로드 -> 분석 시작 -> 상태 모니터링 -> 결과 조회 -> 데이터 검증 -> 결과 저장 (`test_analysis_result.json`)

설정:

```python
TEST_CONFIG = {
    "video_path": "/workspaces/AI_inhaler/app_server/test_clip.mp4",
    "device_type": "pMDI_type2",
    "save_individual_report": True
}
MAX_WAIT_TIME = 1800   # 최대 대기 30분
POLL_INTERVAL = 5      # 상태 확인 간격 5초
```

---

## 서버 설정

### LLM 모델 설정

`api_server.py` 파일 상단에서 고정된 LLM 모델을 설정합니다:

```python
FIXED_LLM_MODELS = ["gpt-4.1", "gpt-4.1"]
```

> 프론트엔드 요청의 `llmModels`는 무시되고, 서버의 `FIXED_LLM_MODELS`가 항상 사용됩니다.

### 리소스 제한 설정

`api_server.py` 파일 상단에서 변경 가능:

```python
MAX_CONCURRENT_ANALYSES = 5              # 최대 동시 분석 수
PROCESS_TIMEOUT = 1800                   # 프로세스 타임아웃 (초, 기본 30분)
MAX_FILE_SIZE = 500 * 1024 * 1024        # 최대 업로드 파일 크기 (500MB)
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}
CLEANUP_OLD_FILES_DURATION = 24          # 업로드 파일 자동 정리 기준 (시간)
ANALYSIS_STORAGE_TTL_HOURS = 2           # 완료/에러 분석 결과 메모리 보관 시간
```

| 설정 | 조정 기준 |
|---|---|
| `MAX_CONCURRENT_ANALYSES` | 서버 메모리, CPU 사용량 |
| `PROCESS_TIMEOUT` | 분석에 필요한 최대 시간 |
| `MAX_FILE_SIZE` | 디스크 용량, 네트워크 대역폭 |
| `CLEANUP_OLD_FILES_DURATION` | 디스크 용량, 보관 기간 요구사항 |
| `ANALYSIS_STORAGE_TTL_HOURS` | 메모리 사용량, 결과 조회 필요 기간 |

### 다중 사용자 지원

**프로세스 격리:**

- 각 분석 요청은 별도의 `multiprocessing` 프로세스에서 실행
- `sys.path`, `sys.modules` 오염 방지, 메모리 격리
- 프로세스 크래시가 다른 분석에 영향 없음

**동시 분석 제한:**

- `Semaphore`로 동시 분석 수 제한 (기본 5개)
- 제한 초과 시 대기 상태로 전환, 완료 시 자동 시작

**프로세스 타임아웃:**

- 기본 30분, 초과 시 `terminate()` -> 10초 대기 -> `kill()` 순서로 강제 종료
- LLM API 요청별 120초 timeout과 연속 에러 3회 중단이 적용되어, 정상 분석은 30분 내 완료됨

**LLM API Timeout:**

- 요청당 최대 대기 시간: 120초 (OpenAI: `httpx.Timeout`, Google GenAI: `HttpOptions`)
- 연결 수립 타임아웃: 10초
- OpenAI 자동 재시도: 2회
- API timeout 발생 시 `"API Error: ..."` 형태로 에러 반환 → 에이전트가 연속 3회 에러 시 탐색 중단

**전용 스레드 풀:**

- 분석 작업은 전용 `ThreadPoolExecutor`에서 실행 (기본 이벤트 루프 스레드 풀 오염 방지)
- `max_workers`는 `MAX_CONCURRENT_ANALYSES`와 동일 (기본 5)

**자동 정리:**

- 업로드 파일: 24시간 이상 된 파일 자동 삭제 (`CLEANUP_OLD_FILES_DURATION`)
- 분석 결과 메모리: 완료/에러 상태의 분석 결과를 2시간 후 자동 삭제 (`ANALYSIS_STORAGE_TTL_HOURS`)
- 1시간마다 스케줄러 실행, 서버 시작 시에도 즉시 실행

### CORS 설정

개발 환경에서는 모든 origin을 허용:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> 프로덕션 환경에서는 특정 origin만 허용하도록 변경을 권장합니다.

---

## 플랫폼별 설정

### macOS

#### SSH 원격 접속 설정

SSH Config 파일(`~/.ssh/config` 또는 Windows: `C:\Users\<사용자명>\.ssh\config`):

```
Host jnu-MacMini-1234
    HostName 172.30.1.7
    User jnu
    Port 22
```

접속: `ssh jnu-MacMini-1234`

Cursor에서 원격 연결: Command Palette -> "Remote-SSH: Connect to Host" -> 호스트 선택

#### Docker 실행

```bash
open -a Docker        # Docker Desktop 시작
docker ps             # 실행 확인
```

> 로그인 시 자동 실행하려면 Docker Desktop 설정에서 "Start Docker Desktop when you log in" 활성화

#### 방화벽 설정

포트 8000, 8080이 차단된 경우:

```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
```

#### IP 주소 확인

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

#### VS Code Dev Container 접속

- VS Code 포트 포워딩으로 `http://localhost:8080` 접속 (권장)
- 포트 포워딩이 안 되면 macOS 호스트 IP로 접속: `http://<호스트_IP>:8080`
- VS Code 하단 "Ports" 탭에서 8080, 8000 포트 포워딩 상태 확인

### Linux / WSL

#### Docker 실행

```bash
# WSL
sudo service docker start

# Linux
sudo systemctl start docker
```

#### IP 주소 확인

```bash
hostname -I | awk '{print $1}'
# 또는
ip addr show | grep "inet " | grep -v 127.0.0.1
# 또는
ip route get 8.8.8.8 | awk '{print $7; exit}'
```

---

## 문제 해결

### 서버가 시작되지 않는 경우

**1. Docker 확인:**

```bash
docker ps    # Docker 데몬이 실행 중인지 확인
```

Docker가 실행되지 않으면:
- macOS: `open -a Docker`
- WSL: `sudo service docker start`
- Linux: `sudo systemctl start docker`

**2. 포트 사용 확인:**

```bash
lsof -i:8000    # 백엔드 포트
lsof -i:8080    # 프론트엔드 포트
```

**3. 로그 확인:**

```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

**4. Python 확인:**

```bash
python3 --version
```

### API 키 관련 오류

**증상:** 분석 시작 후 오류 발생, 로그에 API 인증 오류

**확인:**

```bash
ls -la /workspaces/AI_inhaler/app_server/.env
grep -E "OPENAI_API_KEY|GOOGLE_API_KEY" /workspaces/AI_inhaler/app_server/.env
```

**체크리스트:**

- `.env` 파일이 `app_server/` 디렉토리에 존재하는지
- API 키 값 앞뒤에 공백이나 따옴표가 없는지
- API 키가 만료되지 않았는지

API 키 재발급: [OpenAI](https://platform.openai.com/api-keys) | [Google Gemini](https://makersuite.google.com/app/apikey)

### OpenCV 관련 오류 (libGL.so.1)

```
ImportError: libGL.so.1: cannot open shared object file
```

`opencv-python` 대신 `opencv-python-headless`를 사용하세요:

```bash
pip uninstall opencv-python
pip install opencv-python-headless>=4.10.0,<5.0.0
```

> 이 프로젝트는 GUI 기능을 사용하지 않으므로 `opencv-python-headless`로 충분합니다.

### 프로세스가 정리되지 않는 경우

```bash
# --stop 옵션 사용 (권장)
./start_AI_inhaler.sh --stop

# 수동 강제 종료
pkill -9 -f api_server.py
pkill -9 -f "python.*http.server.*8080"
rm -f .server_pids
```

### 다중 사용자 환경 문제

**분석이 대기 상태에서 진행되지 않는 경우:**

```bash
curl http://localhost:8000/api/stats
```

- `currentAnalyses`가 `maxConcurrentAnalyses`(기본 5)에 도달했는지 확인
- 다른 분석이 완료되면 자동으로 시작됨

**프로세스 타임아웃 오류:**

- 기본 30분 초과 시 발생. `api_server.py`의 `PROCESS_TIMEOUT` 값 조정
- LLM API 120초 timeout + 연속 3회 에러 중단이 적용되어 무한 대기는 방지됨
- 또는 비디오 길이를 줄이거나 분석 로직 최적화 고려

**LLM API 연속 오류로 분석이 조기 종료되는 경우:**

- 로그에 `API 오류 (3/3)` 또는 `연속 API 오류 한도 도달` 메시지 확인
- API 키가 유효하고 사용 한도가 남아있는지 확인 (`app_server/.env`)
- LLM API 서비스 상태 확인: [OpenAI Status](https://status.openai.com/) | [Google Cloud Status](https://status.cloud.google.com/)
- 네트워크 연결 상태 확인 (10초 내 연결 수립 실패 시 timeout)

**디스크 공간 부족:**

```bash
# 24시간 이상 된 파일 수동 삭제
find uploads/ -type f -mtime +1 -delete
```

- `CLEANUP_OLD_FILES_DURATION` 값을 줄여 정리 주기 단축 가능

### 컨테이너 관련 문제

**컨테이너를 찾을 수 없는 경우:**

`start_AI_inhaler.sh`가 자동으로 새 컨테이너를 생성합니다. `.devcontainer/devcontainer.json` 파일이 올바른지 확인하세요.

**포트 매핑이 설정되지 않은 경우:**

스크립트가 자동으로 컨테이너를 재시작하여 포트 매핑을 설정합니다.

---

## 참고 정보

### 프로젝트 구조

```
/workspaces/AI_inhaler/
├── start_AI_inhaler.sh          # 호스트 통합 실행 스크립트
├── start_inside_container.sh    # 컨테이너 내부 실행 스크립트
├── requirements.txt             # Python 패키지 의존성
├── USAGE_GUIDE.md               # 이 문서
├── app_server/                  # 백엔드 서버
│   ├── api_server.py            # FastAPI 서버
│   ├── app_main.py              # 통합 분석 애플리케이션
│   ├── test_api_server.py       # API 테스트 스크립트
│   └── .env                     # API 키 설정 파일
├── webUX/                       # 프론트엔드 웹 UI
├── app_pMDI_type1/              # pMDI 타입1 분석 모듈
├── app_pMDI_type2/              # pMDI 타입2 분석 모듈
├── app_DPI_type1/               # DPI 타입1 분석 모듈
├── app_DPI_type2/               # DPI 타입2 분석 모듈
├── app_DPI_type3/               # DPI 타입3 분석 모듈
├── app_SMI_type1/               # SMI 타입1 분석 모듈
├── uploads/                     # 업로드된 비디오 파일
├── logs/                        # 서버 로그 파일
│   ├── backend.log
│   └── frontend.log
└── .devcontainer/
    └── devcontainer.json        # 컨테이너 설정 파일
```

### OpenCV (opencv-python-headless)

이 프로젝트는 `opencv-python-headless`를 사용합니다:

- 서버 환경(디스플레이 없음)에 최적화
- GUI 의존성(`libGL.so.1` 등) 없이 동작
- 모든 플랫폼(macOS, Linux, WSL)에서 동일하게 작동
- `cv2.imshow()` 등 GUI 기능은 사용 불가 (현재 코드에서 미사용)

---

## 라이선스 및 저작권

이 문서는 AI 흡입기 분석 시스템의 사용 가이드입니다.
