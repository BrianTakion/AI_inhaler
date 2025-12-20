# 전남대학교 흡입기 사용 AI 진단 - 웹 UX

AI 기반 흡입기 사용법 평가 시스템의 웹 인터페이스입니다.

## 📋 기능

- **기기 선택**: DPI, pMDI, SMI 세 가지 흡입기 유형 선택
- **비디오 업로드**: MP4, MOV, AVI, MKV 형식 지원 (최대 500MB)
  - MOV 파일 재생 및 썸네일 표시 지원 개선
- **실시간 분석**: AI 기반 13단계 행동 분석
- **결과 시각화**: 컴팩트한 행동 단계 분석 결과
- **데이터 내보내기**: CSV 형식으로 결과 다운로드

## 🛠️ 기술 스택

- **Frontend**: HTML5, CSS3, TypeScript
- **시각화**: Plotly.js
- **Backend 연동**: FastAPI/Flask (예정)

## 📁 프로젝트 구조

```
webUX/
├── index.html              # 메인 HTML
├── css/                    # 스타일시트
│   ├── utils/
│   │   ├── reset.css
│   │   └── variables.css
│   ├── components/
│   │   ├── header.css
│   │   ├── menu.css
│   │   ├── main-section.css
│   │   └── results.css
│   └── main.css
├── ts/                     # TypeScript 소스
│   ├── types/
│   │   ├── analysis.ts
│   │   └── state.ts
│   ├── components/
│   │   ├── DeviceSelector.ts
│   │   ├── FileUploader.ts
│   │   ├── AnalysisProgress.ts
│   │   └── ResultsViewer.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── csv.ts
│   ├── utils/
│   │   ├── validation.ts
│   │   ├── formatter.ts
│   │   └── chart.ts
│   └── main.ts
├── dist/                   # 컴파일된 JavaScript
├── assets/                 # 이미지 및 아이콘
├── package.json
├── tsconfig.json
└── service_design.md       # 설계 문서
```

## 🚀 시작하기

### 사전 요구사항

- **Node.js** 18.x 이상 및 npm
- **Python** 3.x (개발 서버용)

#### Node.js 설치 (Ubuntu/Debian)

```bash
# Node.js 20.x LTS 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

# 버전 확인
node --version  # v20.x.x
npm --version   # 10.x.x
```

### 1. 의존성 설치

```bash
npm install
```

### 2. TypeScript 컴파일

```bash
npm run build
```

또는 개발 중 자동 컴파일:

```bash
npm run watch
```

### 3. 개발 서버 실행

```bash
npm run serve
```
cd /workspace/webUX && python3 -m http.server 8080
브라우저에서 `http://localhost:8080`을 열어 확인하세요.

### 4. 빌드 및 실행 (한 번에)

```bash
npm run dev
```

### 5. Dev Container 사용 (권장)

프로젝트 루트에 `.devcontainer/devcontainer.json` 설정이 포함되어 있습니다.

**VS Code에서:**
1. Docker가 설치되어 있는지 확인
2. "Dev Containers" 확장 설치
3. `Ctrl+Shift+P` → "Dev Containers: Reopen in Container" 선택
4. 컨테이너가 자동으로 구성되며 모든 의존성이 설치됩니다

**수동 설치 (컨테이너 내부):**
```bash
# Python 의존성
pip install -r ../requirements.txt

# Node.js 의존성
cd webUX && npm install

# TypeScript 빌드
npm run build
```

## 📖 사용 방법

1. **기기 선택**: "1. 기기 선택" 버튼을 클릭하여 흡입기 유형을 선택합니다.
2. **파일 업로드**: "2. 파일" 버튼을 클릭하여 비디오 파일을 업로드합니다.
3. **분석 시작**: "3. 분석" 버튼을 클릭하여 AI 분석을 시작합니다.
4. **결과 확인**: 분석이 완료되면 자동으로 결과가 표시됩니다.
5. **결과 저장**: "4. 저장" 버튼을 클릭하여 CSV 파일로 결과를 다운로드합니다.

## 🔧 설정

### API 엔드포인트 변경

`ts/services/api.ts` 파일에서 `API_BASE_URL`을 수정하세요:

```typescript
const API_BASE_URL = 'http://your-api-server:8000/api';
```

### WebSocket 서버 변경

`ts/main.ts` 파일에서 WebSocket 연결 설정을 수정하세요.

## 📊 분석 결과 구조

분석 결과는 다음을 포함합니다:

- **요약 정보**: 총점, 사용 모델, 분석 시간
- **13단계 행동 분석**: 각 단계별 통과/실패 여부 및 신뢰도 (컴팩트 뷰)
- **기준 시점**: inhalerIN, faceONinhaler, inhalerOUT (내부 데이터로 저장, UI에서는 숨김)
- **타임라인 차트**: 시각화된 분석 결과 (내부 데이터로 저장, UI에서는 숨김)

## 🎨 디자인 시스템

CSS 변수를 사용하여 일관된 디자인을 유지합니다:

- **Primary Color**: #009944 (전남대 메인 컬러)
- **Typography**: 시스템 폰트 스택
- **Spacing**: 4px 기반 스페이싱 시스템
- **Border Radius**: 4px, 8px, 12px, 16px

## 🔄 상태 관리

앱은 다음 6가지 상태를 가집니다:

1. **IDLE**: 초기 상태
2. **DEVICE_SELECTED**: 기기 선택 완료
3. **FILE_UPLOADED**: 파일 업로드 완료
4. **ANALYZING**: 분석 진행 중
5. **COMPLETED**: 분석 완료
6. **ERROR**: 오류 발생

## 🧪 테스트

현재는 시뮬레이션 모드로 동작합니다. 실제 API 연동 시:

1. `ts/services/api.ts`의 함수들을 실제 API와 연동
2. `ts/main.ts`의 `simulateAnalysis()` 메서드를 실제 API 호출로 변경
3. WebSocket 연결 추가

## 📝 라이선스

MIT License

## 👤 작성자

BrianTLee

## 📅 버전 히스토리

- **v1.1.0** (2024-11-15): UI 개선 업데이트
  - MOV 파일 재생 및 썸네일 표시 개선
  - 행동 단계 분석 결과를 더 컴팩트하게 표시
  - 기준 시점 및 타임라인 차트 섹션 숨김 처리 (내부 데이터는 유지)
  
- **v1.0.0** (2024-11-14): 초기 릴리스
  - 기본 UI 구현
  - 시뮬레이션 모드
  - CSV 내보내기 기능

## 🔮 향후 계획

- [ ] 실제 Backend API 연동
- [ ] WebSocket 실시간 업데이트
- [ ] 모바일 반응형 지원
- [ ] 다국어 지원 (한국어/영어)
- [ ] 분석 이력 관리
- [ ] PDF 출력 기능

