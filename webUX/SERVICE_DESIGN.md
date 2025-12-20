# 전남대학교 흡입기 사용 AI 진단 - 웹 UX 설계서

## 1. 개요

### 1.1 목적
- 사용자가 흡입기 사용 비디오를 업로드하고 AI 분석 결과를 확인할 수 있는 웹 인터페이스 제공
- LangGraph 기반 Multi-Agent 시스템(`main_langgraph_251109.py`)과 연동

### 1.2 개발환경
- **Frontend**: HTML5, CSS3, TypeScript
- **Backend 연동**: Python FastAPI/Flask (예정)
- **비디오 처리**: HTML5 Video API
- **차트/시각화**: Chart.js 또는 Plotly.js
- **파일 업로드**: HTML5 File API

### 1.3 타겟 브라우저
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

---

## 2. 전체 레이아웃 구조

### 2.1 화면 구성

```
┌─────────────────────────────────────────────────────────┐
│  Header: 전남대학교 흡입기 사용 AI 진단                    │
├─────────────────────────────────────────────────────────┤
│  Menu Bar: [1. 기기 선택] [2. 파일] [3. 분석] [4. 저장]   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│                     Main Section                          │
│            (콘텐츠 영역 - 동적 변경)                       │
│                                                           │
│                                                           │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 화면 크기
- **데스크톱**: 1280px ~ 1920px (반응형)
- **태블릿**: 768px ~ 1024px
- **모바일**: 최소 지원 안함 (향후 확장)

---

## 3. 상세 컴포넌트 설계

### 3.1 Header Section

```typescript
interface HeaderProps {
  title: string;
  subtitle?: string;
  logo?: string;
}
```

**디자인 요소:**
- 배경색: `#009944` (전남대 메인 컬러)
- 제목: 40px, 굵게, 흰색
- 부제: 18px, 밝은 회색
- 높이: 80px
- 중앙 정렬

---

### 3.2 Menu Bar Section

#### 3.2.1 버튼 레이아웃

```html
<div class="menu-bar">
  <button id="deviceSelect" class="menu-btn">
    1. 기기 선택 <span class="dropdown-icon">▼</span>
  </button>
  <button id="fileUpload" class="menu-btn">2. 파일</button>
  <button id="analyze" class="menu-btn" disabled>3. 분석</button>
  <button id="save" class="menu-btn" disabled>4. 저장</button>
</div>
```

**디자인 요소:**
- 배경색: `#f5f5f5`
- 버튼 크기: 180px × 50px
- 버튼 간격: 20px
- 버튼 배경: `#ffffff`, 테두리 `#ddd`
- Hover 효과: 배경 `#e8f4f8`, 테두리 `#0066cc`
- Disabled 상태: 배경 `#f0f0f0`, 텍스트 `#999999`
- 높이: 70px

#### 3.2.2 기기 선택 Dropdown

```typescript
interface DeviceType {
  id: string;
  name: string;
  description: string;
}

const devices: DeviceType[] = [
  { id: "DPI", name: "DPI", description: "Dry Powder Inhaler (건조분말흡입기)" },
  { id: "pMDI", name: "pMDI", description: "Pressurized Metered Dose Inhaler (정량분무흡입기)" },
  { id: "SMI", name: "SMI", description: "Soft Mist Inhaler (연무흡입기)" }
];
```

**드롭다운 디자인:**
- 위치: 버튼 바로 아래
- 너비: 300px
- 각 항목: 이름 + 설명
- 선택 시: 체크마크 표시, 배경색 강조

---

### 3.3 Main Section

#### 3.3.1 초기 상태 (Idle)

```html
<div class="main-section state-idle">
  <div class="placeholder">
    <i class="icon-upload"></i>
    <h2>흡입기 사용 비디오를 업로드하세요</h2>
    <p>지원 형식: MP4, MOV, AVI, MKV</p>
    <p>최대 크기: 500MB</p>
  </div>
</div>
```

#### 3.3.2 기기 선택 후 상태

```html
<div class="device-info">
  <h3>선택된 기기</h3>
  <div class="device-badge">
    <span class="device-type">pMDI</span>
    <span class="device-name">정량분무흡입기</span>
  </div>
</div>
```

**디자인:**
- 왼쪽 상단에 배치
- 배지 스타일: 둥근 모서리, 파란색 배경
- 크기: 자동 크기, 최소 200px

#### 3.3.3 파일 업로드 후 상태

```html
<div class="video-preview">
  <div class="video-container">
    <video id="videoPlayer" controls>
      <source src="..." type="video/mp4">
    </video>
    <div class="video-info">
      <p>파일명: <strong id="fileName">...</strong></p>
      <p>재생시간: <strong id="duration">...</strong></p>
      <p>크기: <strong id="fileSize">...</strong></p>
      <p>해상도: <strong id="resolution">...</strong></p>
    </div>
  </div>
  <div class="thumbnail">
    <img id="videoThumbnail" src="..." alt="Video Thumbnail">
  </div>
</div>
```

**디자인:**
- 비디오 플레이어: 최대 너비 800px, 16:9 비율 유지
- 썸네일: 200px × 113px (16:9)
- 정보: 테이블 형식, 왼쪽 정렬
- 배치: 비디오(왼쪽) + 정보(오른쪽)

**MOV 파일 재생 개선 (v1.1.0):**
- `preload="metadata"` 속성 추가로 썸네일 미리 로드
- `playsinline` 속성으로 인라인 재생 지원
- `video.load()` 호출로 MOV 파일 강제 로드하여 썸네일 표시 보장

**파일 검증:**
```typescript
interface VideoValidation {
  isValid: boolean;
  error?: string;
  metadata?: {
    duration: number;
    width: number;
    height: number;
    size: number;
    type: string;
  };
}

function validateVideoFile(file: File): VideoValidation {
  const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'];
  
  if (!validTypes.includes(file.type)) {
    return {
      isValid: false,
      error: "동영상 파일을 선택하여 주십시오."
    };
  }
  
  if (file.size > 500 * 1024 * 1024) { // 500MB
    return {
      isValid: false,
      error: "파일 크기가 너무 큽니다. (최대 500MB)"
    };
  }
  
  return { isValid: true };
}
```

#### 3.3.4 분석 진행 중 상태

```html
<div class="analysis-progress">
  <h3>분석 진행 중...</h3>
  
  <!-- 진행률 표시 -->
  <div class="progress-bar">
    <div class="progress-fill" style="width: 45%"></div>
    <span class="progress-text">45%</span>
  </div>
  
  <!-- 현재 단계 표시 -->
  <div class="current-stage">
    <p>현재 단계: <strong id="currentStage">VideoAnalyzer 실행 중 (2/3)</strong></p>
    <p>예상 소요 시간: <strong id="estimatedTime">약 3분</strong></p>
  </div>
  
  <!-- Agent 로그 -->
  <div class="agent-logs">
    <h4>처리 로그</h4>
    <ul id="logList">
      <li class="log-success">✓ VideoProcessor: 비디오 메타데이터 추출 완료</li>
      <li class="log-progress">⟳ VideoAnalyzer (gpt-4o-mini): 분석 중...</li>
      <li class="log-pending">⋯ VideoAnalyzer (gpt-4o): 대기 중</li>
      <li class="log-pending">⋯ Reporter: 대기 중</li>
    </ul>
  </div>
</div>
```

**디자인:**
- 진행률 바: 너비 100%, 높이 30px, 파란색 애니메이션
- 로그: 최대 높이 300px, 스크롤 가능
- 상태별 아이콘 색상: 성공(녹색), 진행(파란색), 대기(회색)

#### 3.3.5 분석 결과 표시 상태

```html
<div class="analysis-results">
  <h3>분석 결과</h3>
  
  <!-- 요약 정보 -->
  <div class="summary-section">
    <div class="summary-card">
      <h4>총점</h4>
      <div class="score-display">
        <span class="score-value">11</span>
        <span class="score-max">/13</span>
      </div>
      <div class="score-percentage">85%</div>
    </div>
    
    <div class="summary-card">
      <h4>사용 모델</h4>
      <p id="modelInfo">gpt-4o-mini × 2, gpt-4o × 1</p>
    </div>
    
    <div class="summary-card">
      <h4>분석 시간</h4>
      <p id="analysisTime">3분 24초</p>
    </div>
  </div>
  
  <!-- 기준 시점 (v1.1.0: UI에서 숨김 처리) -->
  <div class="reference-times" style="display: none;">
    <h4>기준 시점 (Reference Times)</h4>
    <table class="results-table">
      <thead>
        <tr>
          <th>항목</th>
          <th>시간 (초)</th>
          <th>설명</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>inhalerIN</td>
          <td class="time-value">2.5</td>
          <td>흡입기가 처음 보이는 시점</td>
        </tr>
        <tr>
          <td>faceONinhaler</td>
          <td class="time-value">8.3</td>
          <td>흡입기를 입에 대는 시점</td>
        </tr>
        <tr>
          <td>inhalerOUT</td>
          <td class="time-value">18.7</td>
          <td>흡입기가 사라지는 시점</td>
        </tr>
      </tbody>
    </table>
  </div>
  
  <!-- 참고: 기준 시점은 내부 데이터로 유지되며, CSV 파일에는 포함됩니다 -->
  
  <!-- 행동 단계 분석 결과 (v1.1.0: 컴팩트 버전) -->
  <div class="action-steps">
    <h4>행동 단계 분석 (13단계)</h4>
    <div class="action-list">
      <!-- 각 행동에 대한 카드 -->
      <div class="action-card" data-result="pass">
        <div class="action-header">
          <span class="action-number">1</span>
          <h5 class="action-name">앉거나 서 있기</h5>
          <span class="action-result pass">통과</span>
        </div>
        <div class="action-body">
          <p class="action-description">사용자가 바르게 앉거나 서 있는지 확인</p>
          <div class="action-details">
            <span class="detail-item">시간: 1.2초</span>
            <span class="detail-item">신뢰도: 92%</span>
          </div>
        </div>
      </div>
      
      <div class="action-card" data-result="fail">
        <div class="action-header">
          <span class="action-number">2</span>
          <h5 class="action-name">커버 제거</h5>
          <span class="action-result fail">실패</span>
        </div>
        <div class="action-body">
          <p class="action-description">마우스피스 커버를 제거하는지 확인</p>
          <div class="action-details">
            <span class="detail-item">시간: 미감지</span>
            <span class="detail-item">신뢰도: 45%</span>
          </div>
        </div>
      </div>
      
      <!-- ... 나머지 11개 행동 단계 ... -->
    </div>
  </div>
  
  <!-- v1.1.0 변경사항:
       - 카드 간격 축소 (gap: spacing-lg → spacing-sm)
       - 패딩 축소 (header/body padding 감소)
       - 폰트 크기 축소 (더 컴팩트한 표시)
       - 숫자 배지 크기 축소 (32px → 28px)
  -->
  
  <!-- 시각화 차트 (v1.1.0: UI에서 숨김 처리) -->
  <div class="visualization" style="display: none;">
    <h4>타임라인 시각화</h4>
    <div id="timelineChart" class="chart-container"></div>
  </div>
  
  <!-- 참고: 타임라인 차트는 내부적으로 생성되지만 UI에서는 표시하지 않습니다 -->
</div>
```

**디자인:**
- 요약 카드: 3열 그리드, 카드 스타일
- 테이블: 스트라이프 배경, 호버 효과
- 행동 카드 (v1.1.0 컴팩트 버전): 
  - 통과: 녹색 테두리, 체크 아이콘
  - 실패: 빨간색 테두리, X 아이콘
  - 그리드: 2열 (데스크톱), 1열 (모바일)
  - 축소된 간격과 패딩으로 더 많은 정보를 한 화면에 표시
- 차트: Plotly.js 사용, 높이 600px (UI에서 숨김)

---

## 4. 데이터 구조

### 4.1 PromptBank 기반 행동 단계

```typescript
interface ActionStep {
  id: string;
  order: number;
  name: string;
  description: string;
  time: number[];
  score: number[];  // 0 or 1
  confidenceScore: [number, number][];  // [time, confidence]
  result: 'pass' | 'fail' | 'unknown';
}

const actionSteps: ActionStep[] = [
  {
    id: 'sit_stand',
    order: 1,
    name: '앉거나 서 있기',
    description: '사용자가 바르게 앉거나 서 있는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'remove_cover',
    order: 2,
    name: '커버 제거',
    description: '마우스피스 커버를 제거하는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'inspect_mouthpiece',
    order: 3,
    name: '마우스피스 점검',
    description: '마우스피스에 이물질이 있는지 점검',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'shake_inhaler',
    order: 4,
    name: '흡입기 흔들기',
    description: '흡입기를 충분히 흔들고 있는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'hold_inhaler',
    order: 5,
    name: '흡입기를 똑바로 잡기',
    description: '흡입기를 올바르게 잡고 있는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'load_dose',
    order: 6,
    name: '약물 로딩',
    description: '커버를 제거하여 약물을 로딩하는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'exhale_before',
    order: 7,
    name: '흡입 전 날숨',
    description: '흡입기에서 멀리 떨어져 숨을 내쉬는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'seal_lips',
    order: 8,
    name: '마우스피스에 입 대기',
    description: '마우스피스를 입에 제대로 물고 있는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'inhale_deeply',
    order: 9,
    name: '깊게 흡입',
    description: '흡입기에서 깊게 숨을 들이마시는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'remove_inhaler',
    order: 10,
    name: '흡입기 제거',
    description: '숨을 참으면서 흡입기를 입에서 제거하는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'hold_breath',
    order: 11,
    name: '숨 참기',
    description: '약물 흡수를 위해 숨을 참고 있는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'exhale_after',
    order: 12,
    name: '흡입 후 날숨',
    description: '흡입기에서 멀리 떨어져 숨을 내쉬는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  },
  {
    id: 'replace_cover',
    order: 13,
    name: '커버 재장착',
    description: '마우스피스 커버를 다시 닫는지 확인',
    time: [],
    score: [],
    confidenceScore: [],
    result: 'unknown'
  }
];
```

### 4.2 분석 결과 데이터

```typescript
interface AnalysisResult {
  status: 'idle' | 'uploading' | 'analyzing' | 'completed' | 'error';
  deviceType: 'DPI' | 'pMDI' | 'SMI' | null;
  videoInfo: {
    fileName: string;
    duration: number;
    size: number;
    resolution: string;
    thumbnail: string;
  } | null;
  referenceTimes: {
    inhalerIN: number;
    faceONinhaler: number;
    inhalerOUT: number;
  } | null;
  actionSteps: ActionStep[];
  summary: {
    totalSteps: number;
    passedSteps: number;
    failedSteps: number;
    score: number;  // percentage
  } | null;
  modelInfo: {
    models: string[];
    analysisTime: number;  // seconds
  } | null;
  errors: string[];
}
```

---

## 5. API 연동 설계

### 5.1 Backend API Endpoints (예정)

```typescript
// 1. 비디오 업로드
POST /api/video/upload
Content-Type: multipart/form-data
Body: {
  file: File,
  deviceType: 'DPI' | 'pMDI' | 'SMI'
}
Response: {
  videoId: string,
  thumbnail: string,
  metadata: VideoMetadata
}

// 2. 분석 시작
POST /api/analysis/start
Body: {
  videoId: string,
  llmModels: string[]  // e.g., ["gpt-4o-mini", "gpt-4o"]
}
Response: {
  analysisId: string,
  estimatedTime: number
}

// 3. 분석 상태 조회 (폴링 또는 WebSocket)
GET /api/analysis/status/{analysisId}
Response: {
  status: 'pending' | 'processing' | 'completed' | 'error',
  progress: number,  // 0-100
  currentStage: string,
  logs: string[]
}

// 4. 분석 결과 조회
GET /api/analysis/result/{analysisId}
Response: AnalysisResult

// 5. 결과 다운로드
GET /api/analysis/download/{analysisId}?format=csv
Response: CSV file
```

### 5.2 WebSocket 연결 (실시간 진행 상태)

```typescript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:8000/ws/analysis/{analysisId}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'progress':
      updateProgressBar(data.progress);
      break;
    case 'log':
      appendLog(data.message, data.level);
      break;
    case 'stage':
      updateCurrentStage(data.stage);
      break;
    case 'completed':
      loadResults(data.result);
      break;
    case 'error':
      showError(data.error);
      break;
  }
};
```

---

## 6. 사용자 플로우

### 6.1 전체 플로우

```
[시작]
  ↓
[1. 기기 선택]
  ↓
[기기 정보 표시]
  ↓
[2. 파일 업로드]
  ↓
[파일 검증]
  ↓ (성공)
[비디오 미리보기 + 썸네일 표시]
  ↓
[3. 분석 버튼 활성화]
  ↓
[분석 시작]
  ↓
[진행 상태 표시 (실시간)]
  ├─ VideoProcessor
  ├─ VideoAnalyzer × N
  └─ Reporter
  ↓
[분석 완료]
  ↓
[결과 표시]
  ├─ 요약 정보
  ├─ 기준 시점
  ├─ 행동 단계 결과
  └─ 시각화 차트
  ↓
[4. 저장 버튼 활성화]
  ↓
[CSV 다운로드]
  ↓
[종료]
```

### 6.2 에러 처리 플로우

```typescript
// 파일 업로드 오류
if (!validateVideoFile(file).isValid) {
  showErrorMessage('동영상 파일을 선택하여 주십시오.');
  return;
}

// 분석 중 오류
if (analysisStatus === 'error') {
  showErrorModal({
    title: '분석 오류',
    message: '비디오 분석 중 오류가 발생했습니다.',
    details: errorDetails,
    actions: [
      { label: '다시 시도', handler: retryAnalysis },
      { label: '닫기', handler: closeModal }
    ]
  });
}

// 네트워크 오류
if (networkError) {
  showErrorMessage('네트워크 연결을 확인해주세요.');
  // 자동 재시도 로직
  retryWithBackoff();
}
```

---

## 7. CSV 다운로드 형식

### 7.1 CSV 구조

```csv
분석 정보,값
분석 ID,abc123-def456
기기 유형,pMDI
파일명,test_video.mp4
재생시간,25.3초
분석 모델,"gpt-4o-mini, gpt-4o-mini, gpt-4o"
분석 일시,2024-11-14 10:30:45

기준 시점,시간(초)
흡입기 등장 (inhalerIN),2.5
입에 대기 (faceONinhaler),8.3
흡입기 사라짐 (inhalerOUT),18.7

행동 단계,결과,시간(초),신뢰도(%)
1. 앉거나 서 있기,통과,1.2,92
2. 커버 제거,실패,-,45
3. 마우스피스 점검,통과,3.5,88
4. 흡입기 흔들기,통과,4.2,91
5. 흡입기를 똑바로 잡기,통과,5.1,94
6. 약물 로딩,통과,6.3,89
7. 흡입 전 날숨,통과,7.8,87
8. 마우스피스에 입 대기,통과,8.3,95
9. 깊게 흡입,통과,9.5,93
10. 흡입기 제거,통과,11.2,90
11. 숨 참기,통과,12.8,86
12. 흡입 후 날숨,통과,15.3,88
13. 커버 재장착,통과,17.9,91

요약,값
총 단계 수,13
통과 단계,12
실패 단계,1
점수,92%
```

### 7.2 CSV 생성 함수

```typescript
function generateCSV(result: AnalysisResult): string {
  const rows: string[] = [];
  
  // 분석 정보
  rows.push('분석 정보,값');
  rows.push(`기기 유형,${result.deviceType}`);
  rows.push(`파일명,${result.videoInfo.fileName}`);
  rows.push(`재생시간,${result.videoInfo.duration}초`);
  rows.push(`분석 모델,"${result.modelInfo.models.join(', ')}"`);
  rows.push(`분석 일시,${new Date().toLocaleString('ko-KR')}`);
  rows.push('');
  
  // 기준 시점
  rows.push('기준 시점,시간(초)');
  rows.push(`흡입기 등장 (inhalerIN),${result.referenceTimes.inhalerIN}`);
  rows.push(`입에 대기 (faceONinhaler),${result.referenceTimes.faceONinhaler}`);
  rows.push(`흡입기 사라짐 (inhalerOUT),${result.referenceTimes.inhalerOUT}`);
  rows.push('');
  
  // 행동 단계
  rows.push('행동 단계,결과,시간(초),신뢰도(%)');
  result.actionSteps.forEach((step) => {
    const timeStr = step.time.length > 0 ? step.time[0].toString() : '-';
    const confidenceStr = step.confidenceScore.length > 0 
      ? (step.confidenceScore[0][1] * 100).toFixed(0) 
      : '-';
    rows.push(`${step.order}. ${step.name},${step.result === 'pass' ? '통과' : '실패'},${timeStr},${confidenceStr}`);
  });
  rows.push('');
  
  // 요약
  rows.push('요약,값');
  rows.push(`총 단계 수,${result.summary.totalSteps}`);
  rows.push(`통과 단계,${result.summary.passedSteps}`);
  rows.push(`실패 단계,${result.summary.failedSteps}`);
  rows.push(`점수,${result.summary.score}%`);
  
  return rows.join('\n');
}

function downloadCSV(result: AnalysisResult): void {
  const csv = generateCSV(result);
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', `inhaler_analysis_${Date.now()}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

---

## 8. 상태 관리

### 8.1 State Machine

```typescript
type AppState = 
  | 'IDLE'                // 초기 상태
  | 'DEVICE_SELECTED'     // 기기 선택 완료
  | 'FILE_UPLOADED'       // 파일 업로드 완료
  | 'ANALYZING'           // 분석 진행 중
  | 'COMPLETED'           // 분석 완료
  | 'ERROR';              // 오류 발생

interface StateTransition {
  from: AppState;
  to: AppState;
  action: string;
  guard?: () => boolean;
}

const transitions: StateTransition[] = [
  { from: 'IDLE', to: 'DEVICE_SELECTED', action: 'SELECT_DEVICE' },
  { from: 'DEVICE_SELECTED', to: 'FILE_UPLOADED', action: 'UPLOAD_FILE', guard: validateFile },
  { from: 'FILE_UPLOADED', to: 'ANALYZING', action: 'START_ANALYSIS' },
  { from: 'ANALYZING', to: 'COMPLETED', action: 'ANALYSIS_SUCCESS' },
  { from: 'ANALYZING', to: 'ERROR', action: 'ANALYSIS_FAILED' },
  { from: 'ERROR', to: 'FILE_UPLOADED', action: 'RETRY' },
  { from: 'COMPLETED', to: 'IDLE', action: 'RESET' }
];
```

### 8.2 버튼 활성화 로직

```typescript
function updateButtonStates(state: AppState): void {
  const buttons = {
    device: document.getElementById('deviceSelect'),
    file: document.getElementById('fileUpload'),
    analyze: document.getElementById('analyze'),
    save: document.getElementById('save')
  };
  
  switch (state) {
    case 'IDLE':
      buttons.device.disabled = false;
      buttons.file.disabled = true;
      buttons.analyze.disabled = true;
      buttons.save.disabled = true;
      break;
      
    case 'DEVICE_SELECTED':
      buttons.device.disabled = false;
      buttons.file.disabled = false;
      buttons.analyze.disabled = true;
      buttons.save.disabled = true;
      break;
      
    case 'FILE_UPLOADED':
      buttons.device.disabled = false;
      buttons.file.disabled = false;
      buttons.analyze.disabled = false;
      buttons.save.disabled = true;
      break;
      
    case 'ANALYZING':
      buttons.device.disabled = true;
      buttons.file.disabled = true;
      buttons.analyze.disabled = true;
      buttons.save.disabled = true;
      break;
      
    case 'COMPLETED':
      buttons.device.disabled = false;
      buttons.file.disabled = false;
      buttons.analyze.disabled = false;
      buttons.save.disabled = false;
      break;
      
    case 'ERROR':
      buttons.device.disabled = false;
      buttons.file.disabled = false;
      buttons.analyze.disabled = false;
      buttons.save.disabled = true;
      break;
  }
}
```

---

## 9. 시각화 (Plotly.js)

### 9.1 타임라인 차트

```typescript
function createTimelineChart(result: AnalysisResult): void {
  const traces = [];
  
  // 기준 시점 표시 (세로선)
  const refTimes = result.referenceTimes;
  traces.push({
    x: [refTimes.inhalerIN, refTimes.inhalerIN],
    y: [0, 13],
    mode: 'lines',
    name: 'inhalerIN',
    line: { color: 'blue', dash: 'dash', width: 2 }
  });
  
  traces.push({
    x: [refTimes.faceONinhaler, refTimes.faceONinhaler],
    y: [0, 13],
    mode: 'lines',
    name: 'faceONinhaler',
    line: { color: 'green', dash: 'dash', width: 2 }
  });
  
  traces.push({
    x: [refTimes.inhalerOUT, refTimes.inhalerOUT],
    y: [0, 13],
    mode: 'lines',
    name: 'inhalerOUT',
    line: { color: 'red', dash: 'dash', width: 2 }
  });
  
  // 행동 단계 표시 (산점도)
  const xValues = [];
  const yValues = [];
  const colors = [];
  const text = [];
  
  result.actionSteps.forEach((step, index) => {
    if (step.time.length > 0) {
      step.time.forEach((t, i) => {
        xValues.push(t);
        yValues.push(step.order);
        colors.push(step.score[i] === 1 ? 'green' : 'red');
        text.push(`${step.name}<br>시간: ${t}초<br>신뢰도: ${(step.confidenceScore[i][1] * 100).toFixed(0)}%`);
      });
    }
  });
  
  traces.push({
    x: xValues,
    y: yValues,
    mode: 'markers',
    type: 'scatter',
    name: '행동 단계',
    marker: {
      size: 12,
      color: colors,
      symbol: 'circle'
    },
    text: text,
    hoverinfo: 'text'
  });
  
  const layout = {
    title: '흡입기 사용 타임라인',
    xaxis: {
      title: '시간 (초)',
      range: [0, result.videoInfo.duration]
    },
    yaxis: {
      title: '행동 단계',
      tickvals: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
      ticktext: result.actionSteps.map(s => s.name)
    },
    height: 600,
    showlegend: true
  };
  
  Plotly.newPlot('timelineChart', traces, layout);
}
```

---

## 10. 향후 개선 사항

### 10.1 Phase 2 (단기)
- [ ] 실시간 비디오 프레임 하이라이트 (특정 시점 표시)
- [ ] 모바일 반응형 지원
- [ ] 다국어 지원 (한국어/영어)
- [ ] 분석 이력 관리 (로컬 스토리지)
- [ ] 프린트 기능 (PDF 출력)

### 10.2 Phase 3 (중기)
- [ ] 여러 비디오 동시 분석 (배치 처리)
- [ ] 사용자 인증 및 권한 관리
- [ ] 비디오 편집 기능 (트림, 회전)
- [ ] 커스텀 보고서 템플릿
- [ ] 통계 대시보드 (누적 분석 결과)

### 10.3 Phase 4 (장기)
- [ ] AI 모델 선택 UI (사용자가 직접 모델 조합 선택)
- [ ] 실시간 비디오 스트림 분석 (웹캠)
- [ ] 협업 기능 (결과 공유, 댓글)
- [ ] REST API 문서 자동 생성
- [ ] 성능 모니터링 대시보드

---

## 11. 프로젝트 구조 (예상)

```
webUX/
├── index.html                  # 메인 HTML
├── css/
│   ├── main.css                # 전역 스타일
│   ├── components/
│   │   ├── header.css
│   │   ├── menu.css
│   │   ├── main-section.css
│   │   └── results.css
│   └── utils/
│       ├── reset.css
│       └── variables.css       # CSS 변수 (색상, 폰트 등)
├── ts/
│   ├── main.ts                 # 앱 진입점
│   ├── types/
│   │   ├── analysis.ts         # 타입 정의
│   │   └── state.ts
│   ├── components/
│   │   ├── DeviceSelector.ts
│   │   ├── FileUploader.ts
│   │   ├── AnalysisProgress.ts
│   │   └── ResultsViewer.ts
│   ├── services/
│   │   ├── api.ts              # API 호출
│   │   ├── websocket.ts        # WebSocket 연결
│   │   └── csv.ts              # CSV 생성
│   └── utils/
│       ├── validation.ts       # 파일 검증
│       ├── formatter.ts        # 데이터 포맷팅
│       └── chart.ts            # 차트 생성
├── assets/
│   ├── images/
│   │   └── logo.png
│   └── icons/
├── dist/                       # 빌드 결과물
└── design.md                   # 이 문서
```

---

## 12. 변경 이력

### v1.1.0 (2024.11.15) - UI 개선

#### 변경사항
1. **MOV 파일 재생 개선**
   - `FileUploader.ts`: MOV 파일 썸네일 표시 및 재생 지원 강화
   - `preload="metadata"`, `playsinline` 속성 추가
   - `video.load()` 호출로 강제 로드

2. **UI 레이아웃 최적화**
   - **기준 시점 섹션**: UI에서 숨김 (`display: none`)
     - 내부 데이터는 유지되며 CSV 출력에 포함
   - **행동 단계 분석**: 더 컴팩트한 디스플레이
     - 카드 간격: `var(--spacing-lg)` → `var(--spacing-sm)`
     - 헤더/바디 패딩 축소
     - 폰트 크기 축소: `font-size-md` → `font-size-sm`, `font-size-sm` → `font-size-xs`
     - 숫자 배지: 32px → 28px
   - **타임라인 차트**: UI에서 숨김 (`display: none`)
     - 내부적으로 생성되지만 화면에 표시하지 않음

3. **영향받은 파일**
   - `index.html`: 섹션에 `display: none` 스타일 추가
   - `css/components/results.css`: 컴팩트 스타일링 적용
   - `ts/components/FileUploader.ts`: MOV 파일 처리 개선

#### 목적
- 사용자에게 핵심 정보(요약 + 행동 단계)만 집중해서 보여주기
- 더 많은 행동 단계를 한 화면에 표시하여 스크롤 최소화
- 모든 데이터는 내부적으로 유지되어 CSV 다운로드 시 포함됨

### v1.0.0 (2024.11.14) - 초기 릴리스
- 기본 UI 구현
- 시뮬레이션 모드
- CSV 내보내기 기능

---

**마지막 업데이트**: 2024.11.15  
**버전**: 1.1.0 (UI 개선)  
**작성자**: BrianTLee
