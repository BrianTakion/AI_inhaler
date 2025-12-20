// Analysis Types

export interface DeviceType {
  id: 'pMDI_type1' | 'pMDI_type2' | 'DPI_type1' | 'DPI_type2' | 'DPI_type3' | 'SMI_type1';
  name: string;
  description: string;
}

export interface VideoMetadata {
  fileName: string;
  duration: number;
  size: number;
  resolution: string;
  type: string;
  width: number;
  height: number;
}

export interface VideoValidation {
  isValid: boolean;
  error?: string;
  metadata?: VideoMetadata;
}

export interface ActionStep {
  id: string;
  order: number;
  name: string;
  description: string;
  time: number[];
  score: number[];  // 0 or 1
  confidenceScore: [number, number][];  // [time, confidence]
  result: 'pass' | 'fail' | 'unknown';
}

export interface ReferenceTimes {
  inhalerIN: number;
  faceONinhaler: number;
  inhalerOUT: number;
}

export interface AnalysisSummary {
  totalSteps: number;
  passedSteps: number;
  failedSteps: number;
  score: number;  // percentage
}

export interface ModelInfo {
  models: string[];
  analysisTime: number;  // seconds
}

export interface AnalysisResult {
  status: 'idle' | 'uploading' | 'analyzing' | 'completed' | 'error';
  deviceType: DeviceType['id'] | null;
  videoInfo: VideoMetadata | null;
  referenceTimes: ReferenceTimes | null;
  actionSteps: ActionStep[];
  summary: AnalysisSummary | null;
  modelInfo: ModelInfo | null;
  errors: string[];
}

export interface ProgressUpdate {
  progress: number;  // 0-100
  currentStage: string;
  estimatedTime: string;
}

export interface LogEntry {
  message: string;
  level: 'success' | 'progress' | 'pending' | 'error' | 'info';
  timestamp: Date;
}

