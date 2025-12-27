# AI 흡입기 분석 시스템 사용 가이드

이 문서는 AI 흡입기 분석 시스템의 주요 스크립트와 도구들의 사용법을 설명합니다.

---

## 1. app_main.py

### 개요
`app_main.py`는 통합 흡입기 비디오 분석 애플리케이션으로, 여러 디바이스 타입에 대해 통합적으로 분석을 수행합니다. 이 스크립트는 직접 실행하여 비디오 분석을 수행할 수 있습니다.

### 위치
```
app_server/app_main.py
```

### 사용법

#### 기본 실행
```bash
cd app_server
python app_main.py
```

#### 설정 변경
`app_main.py` 파일 내부의 `main()` 함수에서 다음 변수들을 수정할 수 있습니다:

```python
# 비디오 파일 경로
video_path = r"/workspaces/AI_inhaler/app_SMI_type1/video_source/SMI-6 Respimat.MOV"

# 디바이스 타입 선택
device_list = ['pMDI_type1', 'pMDI_type2', 'DPI_type1', 'DPI_type2', 'DPI_type3', 'SMI_type1']
device_type = device_list[5]  # 인덱스로 선택 (0~5)

# LLM 모델 설정
set_llm_models = ['gpt-4.1', 'gemini-2.5-pro']

# 개별 리포트 저장 여부
save_individual_report = True  # True: 저장, False: 저장하지 않기
```

#### 지원 디바이스 타입
- `pMDI_type1`: Suspension pressurized metered-dose inhaler
- `pMDI_type2`: Solution pressurized metered-dose inhaler
- `DPI_type1`: Multi-dose cap-opening dry powder inhaler
- `DPI_type2`: Multi-dose rotating/button-actuated dry powder inhaler
- `DPI_type3`: Single-dose capsule-based dry powder inhaler
- `SMI_type1`: Soft mist inhaler

#### 지원 LLM 모델
- OpenAI: `gpt-4.1`, `gpt-5-nano`, `gpt-5.1`, `gpt-5.2`
- Google: `gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3-pro-preview`

#### 환경 변수 설정
`.env` 파일에 API 키를 설정해야 합니다:

```bash
# app_server/.env 파일
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
```

#### 출력 결과
분석이 완료되면 다음 정보가 출력됩니다:
- 비디오 정보 (파일명, 재생시간, 프레임 수, 해상도)
- 최종 판단 결과 (각 행동 단계별 SUCCESS/FAIL)
- 최종 종합 기술

#### 예시 출력
```
================================================================================
디바이스 타입: SMI_type1
================================================================================

LLM 모델 초기화 (2개):
  1. gpt-4.1
  2. gemini-2.5-pro

분석할 비디오: /workspaces/AI_inhaler/app_SMI_type1/video_source/SMI-6 Respimat.MOV

✅ 분석이 성공적으로 완료되었습니다!

==================================================
=== 비디오 분석 결과 요약 ===
==================================================

[비디오 정보]
  파일명: SMI-6 Respimat.MOV
  재생시간: 45.2초
  총 프레임: 1356
  해상도: 1920x1080px

[최종 판단 결과]
  sit_stand: SUCCESS (1)
  remove_cover: SUCCESS (1)
  ...

[최종 종합 기술]
  환자는 흡입기를 올바르게 사용했습니다...
```

---

## 2. test_api_server.py

### 개요
`test_api_server.py`는 API 서버의 완전한 분석 플로우를 테스트하는 스크립트입니다. `app_main.py`의 설정을 기반으로 전체 분석 플로우를 테스트하고 최종 결과를 검증합니다.

### 위치
```
app_server/test_api_server.py
```

### 사용법

#### 기본 실행
```bash
cd app_server
python test_api_server.py
```

#### 사전 요구사항
API 서버가 실행 중이어야 합니다:
```bash
# 별도 터미널에서 API 서버 실행
cd app_server
python api_server.py
```

또는 `start.sh`를 사용하여 백엔드와 프론트엔드를 함께 실행할 수 있습니다 (자세한 내용은 아래 참조).

#### 테스트 설정 변경
`test_api_server.py` 파일 내부의 `TEST_CONFIG` 변수를 수정할 수 있습니다:

```python
TEST_CONFIG = {
    "video_path": "/workspaces/AI_inhaler/app_SMI_type1/video_source/SMI-6 Respimat.MOV",
    "device_type": "SMI_type1",
    "save_individual_report": True
}
```

#### 테스트 단계
스크립트는 다음 순서로 테스트를 수행합니다:

1. **서버 상태 확인**: API 서버가 실행 중인지 확인
2. **서버 설정 정보 조회**: `/api/config` 엔드포인트를 통해 LLM 모델 정보 조회
3. **비디오 업로드**: 테스트 비디오 파일을 서버에 업로드
4. **분석 시작**: 업로드된 비디오에 대한 분석 시작
5. **분석 진행 상태 모니터링**: 분석이 완료될 때까지 상태를 주기적으로 확인 (최대 30분)
6. **분석 결과 조회**: 완료된 분석 결과 조회
7. **결과 데이터 검증**: 필수 필드 및 데이터 형식 검증
8. **app_main.py 출력 형식과 비교**: `app_main.py`의 출력 형식과 비교
9. **결과 저장**: 테스트 결과를 `test_analysis_result.json` 파일로 저장

#### 예시 출력
```
================================================================================
API 서버 완전 분석 테스트 시작
================================================================================
테스트 설정:
  - 비디오: SMI-6 Respimat.MOV
  - 디바이스 타입: SMI_type1
  - 개별 리포트 저장: True

================================================================================
1. 서버 상태 확인
================================================================================
✓ 서버 실행 중: API Server is running (v1.0.0)

================================================================================
2. 서버 설정 정보 조회
================================================================================
✓ 설정 정보 조회 성공
  버전: 1.0.0
  LLM 모델: ['gpt-4.1', 'gemini-2.5-pro']
✓ LLM 모델 검증 통과 (2개 모델)

...

================================================================================
✓ 모든 테스트 완료!
================================================================================
```

#### 오류 처리
- 서버가 실행되지 않은 경우: 서버 시작 방법 안내 메시지 출력
- 타임아웃: 최대 대기 시간(30분) 초과 시 테스트 실패
- 분석 오류: 오류 메시지와 함께 테스트 실패

#### 결과 파일
테스트가 성공적으로 완료되면 `test_analysis_result.json` 파일이 생성됩니다.

---

## 3. start.sh

### 개요
`start.sh`는 백엔드 API 서버와 프론트엔드 웹 서버를 동시에 실행하는 스크립트입니다. WSL 환경에서 실행되며, 윈도우 브라우저에서 접속할 수 있도록 설정됩니다.

### 위치
```
start.sh (프로젝트 루트 디렉토리)
```

### 사용법

#### 기본 실행
```bash
./start.sh
```

또는

```bash
bash start.sh
```

#### 실행 권한 부여 (최초 1회)
```bash
chmod +x start.sh
```

#### 실행 과정
1. 기존 프로세스 정리: 실행 중인 API 서버 및 HTTP 서버 프로세스 종료
2. 백엔드 서버 시작: `app_server/api_server.py` 실행 (포트 8000)
3. 백엔드 서버 상태 확인: 서버가 정상적으로 시작되었는지 확인
4. 프론트엔드 서버 시작: `webUX` 디렉토리에서 Python HTTP 서버 실행 (포트 8080)
5. 프론트엔드 서버 상태 확인: 서버가 정상적으로 시작되었는지 확인
6. PID 파일 저장: 프로세스 ID를 `.server_pids` 파일에 저장

#### 서버 정보
- **백엔드 API**: http://localhost:8000
- **프론트엔드**: http://localhost:8080

#### WSL 환경에서 윈도우 브라우저 접속
스크립트 실행 시 WSL IP 주소가 출력됩니다:
```
WSL 환경에서 윈도우 브라우저 접속:
  - 프론트엔드: http://<WSL_IP>:8080
```

#### 로그 파일
- 백엔드 로그: `logs/backend.log`
- 프론트엔드 로그: `logs/frontend.log`

로그 확인:
```bash
# 백엔드 로그 실시간 확인
tail -f logs/backend.log

# 프론트엔드 로그 실시간 확인
tail -f logs/frontend.log
```

#### 서버 종료
- **Ctrl+C**: 스크립트 실행 중 Ctrl+C를 누르면 모든 서버가 종료됩니다
- **stop.sh**: 별도 터미널에서 `./stop.sh` 실행

#### 예시 출력
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
  - 프론트엔드: http://172.20.10.2:8080

로그 파일:
  - 백엔드: tail -f logs/backend.log
  - 프론트엔드: tail -f logs/frontend.log

서버를 종료하려면:
  - Ctrl+C를 누르거나
  - ./stop.sh 실행

==========================================
```

#### 주의사항
- 포트 8000과 8080이 이미 사용 중인 경우, 기존 프로세스가 자동으로 종료됩니다
- 서버 시작 실패 시 오류 메시지와 함께 스크립트가 종료됩니다

---

## 4. stop.sh

### 개요
`stop.sh`는 `start.sh`로 시작된 백엔드와 프론트엔드 서버를 종료하는 스크립트입니다.

### 위치
```
stop.sh (프로젝트 루트 디렉토리)
```

### 사용법

#### 기본 실행
```bash
./stop.sh
```

또는

```bash
bash stop.sh
```

#### 실행 권한 부여 (최초 1회)
```bash
chmod +x stop.sh
```

#### 종료 과정
1. PID 파일 확인: `.server_pids` 파일에서 저장된 프로세스 ID 확인
2. 프로세스 종료: PID 파일에 저장된 프로세스들을 종료
3. 추가 프로세스 정리:
   - `api_server.py` 프로세스 종료
   - `uvicorn.*api_server` 프로세스 종료
   - 포트 8080을 사용하는 HTTP 서버 프로세스 종료
4. PID 파일 삭제: `.server_pids` 파일 삭제

#### 예시 출력
```
==========================================
서버 종료 중...
==========================================

PID 파일에서 프로세스 확인 중...
프로세스 종료: PID 12345
프로세스 종료: PID 12346

추가 프로세스 정리 중...
  ✓ API 서버 프로세스 종료
  - Uvicorn 프로세스 없음
  ✓ 프론트엔드 서버 프로세스 종료

==========================================
✓ 서버가 종료되었습니다.
==========================================
```

#### 사용 시나리오
1. **정상 종료**: `start.sh`로 시작한 서버를 정상적으로 종료
2. **강제 종료**: 서버가 응답하지 않을 때 강제 종료
3. **정리 작업**: 시스템 재시작 전 모든 관련 프로세스 정리

#### 주의사항
- 실행 중인 서버가 없는 경우에도 오류 없이 종료됩니다
- PID 파일이 없는 경우, 프로세스 이름으로 검색하여 종료를 시도합니다

---

## 전체 워크플로우 예시

### 시나리오 1: 웹 인터페이스를 통한 분석
```bash
# 1. 서버 시작
./start.sh

# 2. 브라우저에서 접속
# http://localhost:8080 (또는 WSL IP:8080)

# 3. 웹 인터페이스에서 파일 업로드 및 분석 수행

# 4. 서버 종료
./stop.sh
```

### 시나리오 2: 직접 스크립트 실행
```bash
# 1. app_main.py 직접 실행
cd app_server
python app_main.py
```

### 시나리오 3: API 서버 테스트
```bash
# 1. API 서버 시작 (별도 터미널)
cd app_server
python api_server.py

# 2. 테스트 실행 (다른 터미널)
cd app_server
python test_api_server.py

# 3. API 서버 종료 (Ctrl+C)
```

### 시나리오 4: 통합 테스트
```bash
# 1. 서버 시작
./start.sh

# 2. API 테스트 (다른 터미널)
cd app_server
python test_api_server.py

# 3. 서버 종료
./stop.sh
```

---

## 문제 해결

### 서버가 시작되지 않는 경우
1. 포트가 이미 사용 중인지 확인:
   ```bash
   lsof -i:8000  # 백엔드 포트
   lsof -i:8080  # 프론트엔드 포트
   ```
2. 로그 파일 확인:
   ```bash
   tail -f logs/backend.log
   tail -f logs/frontend.log
   ```

### API 테스트가 실패하는 경우
1. API 서버가 실행 중인지 확인:
   ```bash
   curl http://localhost:8000/
   ```
2. 비디오 파일 경로가 올바른지 확인
3. 환경 변수(.env 파일)가 올바르게 설정되었는지 확인

### 프로세스가 종료되지 않는 경우
```bash
# 강제 종료
pkill -f api_server.py
pkill -f "python.*http.server.*8080"
lsof -ti:8080 | xargs kill -9
```

---

## 추가 정보

- 프로젝트 루트: `/workspaces/AI_inhaler`
- 백엔드 디렉토리: `app_server/`
- 프론트엔드 디렉토리: `webUX/`
- 로그 디렉토리: `logs/`
- PID 파일: `.server_pids` (프로젝트 루트)

