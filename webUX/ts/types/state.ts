// State Management Types

export type AppState = 
  | 'IDLE'                // 초기 상태
  | 'DEVICE_SELECTED'     // 기기 선택 완료
  | 'FILE_UPLOADED'       // 파일 업로드 완료
  | 'ANALYZING'           // 분석 진행 중
  | 'COMPLETED'           // 분석 완료
  | 'ERROR';              // 오류 발생

export interface StateTransition {
  from: AppState;
  to: AppState;
  action: string;
  guard?: () => boolean;
}

export interface AppStateData {
  currentState: AppState;
  deviceType: 'DPI' | 'pMDI' | 'SMI' | null;
  videoFile: File | null;
  analysisId: string | null;
}

export interface ButtonStates {
  device: boolean;
  file: boolean;
  analyze: boolean;
  save: boolean;
}

