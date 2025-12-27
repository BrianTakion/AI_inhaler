# AI 흡입기 분석 시스템 사용 가이드

이 문서는 AI 흡입기 분석 시스템의 주요 구성 요소들의 사용법을 설명합니다.

## 목차

1. [app_main.py - 통합 분석 애플리케이션](#app_mainpy---통합-분석-애플리케이션)
2. [api_server.py - FastAPI 백엔드 서버](#api_serverpy---fastapi-백엔드-서버)
3. [test_api_server.py - API 서버 테스트](#test_api_serverpy---api-서버-테스트)
4. [start.sh - 서버 시작 스크립트](#startsh---서버-시작-스크립트)
5. [stop.sh - 서버 종료 스크립트](#stopsh---서버-종료-스크립트)

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

`.env` 파일에 API 키를 설정해야 합니다:

```bash
# app_server/.env
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
```

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
  "logs": [
    "[10:30:15] 분석 시작",
    "[10:30:20] 비디오 로드 완료"
  ],
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
  "individualHtmlPaths": [
    "/path/to/agent1.html",
    "/path/to/agent2.html"
  ]
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

## start.sh - 서버 시작 스크립트

### 개요

`start.sh`는 백엔드 API 서버와 프론트엔드 웹 서버를 동시에 시작하는 스크립트입니다.

### 사용법

#### 1. 실행 권한 부여 (최초 1회)

```bash
chmod +x start.sh
```

#### 2. 서버 시작

```bash
./start.sh
```

### 실행 과정

1. **기존 프로세스 정리** - 실행 중인 서버 프로세스 종료
2. **백엔드 서버 시작** - `api_server.py` 실행 (포트 8000)
3. **백엔드 상태 확인** - 서버가 정상적으로 시작되었는지 확인
4. **프론트엔드 서버 시작** - Python HTTP 서버 실행 (포트 8080)
5. **프론트엔드 상태 확인** - 서버가 정상적으로 시작되었는지 확인

### 출력 예시

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

WSL 환경에서 윈도우 브라우저 접속:
  - 프론트엔드: http://192.168.1.100:8080

로그 파일:
  - 백엔드: tail -f /workspaces/AI_inhaler/logs/backend.log
  - 프론트엔드: tail -f /workspaces/AI_inhaler/logs/frontend.log

서버를 종료하려면:
  - Ctrl+C를 누르거나
  - ./stop.sh 실행

==========================================
```

### 주요 기능

- **자동 프로세스 정리**: 기존 실행 중인 서버 자동 종료
- **상태 확인**: 서버 시작 후 정상 동작 여부 확인
- **로그 파일**: 모든 로그를 `logs/` 디렉토리에 저장
- **PID 파일**: `.server_pids` 파일에 프로세스 ID 저장
- **WSL 지원**: WSL 환경에서 윈도우 브라우저 접속 정보 제공

### 로그 확인

```bash
# 백엔드 로그
tail -f logs/backend.log

# 프론트엔드 로그
tail -f logs/frontend.log
```

### 서버 종료

- **Ctrl+C**: 스크립트 실행 중 Ctrl+C로 종료
- **stop.sh 실행**: 별도 터미널에서 `./stop.sh` 실행

---

## stop.sh - 서버 종료 스크립트

### 개요

`stop.sh`는 실행 중인 백엔드와 프론트엔드 서버를 종료하는 스크립트입니다.

### 사용법

#### 1. 실행 권한 부여 (최초 1회)

```bash
chmod +x stop.sh
```

#### 2. 서버 종료

```bash
./stop.sh
```

### 실행 과정

1. **PID 파일 확인** - `.server_pids` 파일에서 프로세스 ID 읽기
2. **프로세스 종료** - 저장된 PID의 프로세스 종료
3. **추가 프로세스 정리** - 다음 프로세스들도 종료:
   - `api_server.py` 프로세스
   - `uvicorn.*api_server` 프로세스
   - 포트 8080을 사용하는 HTTP 서버 프로세스

### 출력 예시

```
==========================================
서버 종료 중...
==========================================

PID 파일에서 프로세스 확인 중...
프로세스 종료: PID 12345
프로세스 종료: PID 12346

추가 프로세스 정리 중...
  ✓ API 서버 프로세스 종료
  ✓ Uvicorn 프로세스 종료
  ✓ 프론트엔드 서버 프로세스 종료

==========================================
✓ 서버가 종료되었습니다.
==========================================
```

### 주요 기능

- **PID 파일 기반 종료**: `start.sh`로 시작한 프로세스 종료
- **추가 프로세스 정리**: PID 파일에 없는 프로세스도 자동 종료
- **포트 기반 종료**: 포트 8080을 사용하는 프로세스 종료

### 수동 종료 방법

스크립트가 작동하지 않는 경우:

```bash
# API 서버 종료
pkill -f api_server.py

# 포트 8080 사용 프로세스 종료
lsof -ti:8080 | xargs kill -9

# 또는 특정 PID 종료
kill <PID>
```

---

## 전체 워크플로우

### 1. 시스템 시작

```bash
# 서버 시작
./start.sh
```

### 2. 웹 브라우저에서 접속

- 로컬: http://localhost:8080
- WSL: http://{WSL_IP}:8080

### 3. 분석 수행

1. 기기 선택
2. 비디오 파일 업로드
3. 분석 시작
4. 결과 확인 및 저장

### 4. 시스템 종료

```bash
# 서버 종료
./stop.sh
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

3. API 키 설정 확인:
   ```bash
   cat app_server/.env
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

---

## 추가 정보

- 프로젝트 루트: `/workspaces/AI_inhaler`
- 백엔드 디렉토리: `app_server/`
- 프론트엔드 디렉토리: `webUX/`
- 업로드 디렉토리: `uploads/`
- 로그 디렉토리: `logs/`

---

## 라이선스 및 저작권

이 문서는 AI 흡입기 분석 시스템의 사용 가이드입니다.

