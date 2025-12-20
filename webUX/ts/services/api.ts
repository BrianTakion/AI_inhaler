// API Service (Backend 연동)

import { AnalysisResult, VideoMetadata } from '../types/analysis.js';

const API_BASE_URL = 'http://localhost:8000/api';

export interface UploadResponse {
  videoId: string;
  thumbnail: string;
  metadata: VideoMetadata;
}

export interface StartAnalysisResponse {
  analysisId: string;
  estimatedTime: number;
}

export interface AnalysisStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  currentStage: string;
  logs: string[];
}

export async function uploadVideo(
  file: File,
  deviceType: 'DPI' | 'pMDI' | 'SMI'
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('deviceType', deviceType);

  const response = await fetch(`${API_BASE_URL}/video/upload`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error('비디오 업로드에 실패했습니다.');
  }

  return response.json();
}

export async function startAnalysis(
  videoId: string,
  llmModels: string[]
): Promise<StartAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ videoId, llmModels })
  });

  if (!response.ok) {
    throw new Error('분석 시작에 실패했습니다.');
  }

  return response.json();
}

export async function getAnalysisStatus(
  analysisId: string
): Promise<AnalysisStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/status/${analysisId}`);

  if (!response.ok) {
    throw new Error('분석 상태 조회에 실패했습니다.');
  }

  return response.json();
}

export async function getAnalysisResult(
  analysisId: string
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/analysis/result/${analysisId}`);

  if (!response.ok) {
    throw new Error('분석 결과 조회에 실패했습니다.');
  }

  return response.json();
}

export async function downloadResult(
  analysisId: string,
  format: 'csv' | 'json' = 'csv'
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/analysis/download/${analysisId}?format=${format}`
  );

  if (!response.ok) {
    throw new Error('결과 다운로드에 실패했습니다.');
  }

  return response.blob();
}

