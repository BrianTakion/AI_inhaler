// CSV Generation Service

import { AnalysisResult } from '../types/analysis.js';
import { formatDateTime } from '../utils/formatter.js';

export function generateCSV(result: AnalysisResult): string {
  const rows: string[] = [];

  // 분석 정보
  rows.push('분석 정보,값');
  rows.push(`기기 유형,${result.deviceType || '-'}`);
  
  if (result.videoInfo) {
    rows.push(`파일명,${result.videoInfo.fileName}`);
    rows.push(`재생시간,${result.videoInfo.duration.toFixed(1)}초`);
    rows.push(`파일 크기,${(result.videoInfo.size / (1024 * 1024)).toFixed(2)}MB`);
    rows.push(`해상도,${result.videoInfo.resolution}`);
  }
  
  if (result.modelInfo) {
    rows.push(`분석 모델,"${result.modelInfo.models.join(', ')}"`);
  }
  
  rows.push(`분석 일시,${formatDateTime(new Date())}`);
  rows.push('');

  // 기준 시점
  if (result.referenceTimes) {
    rows.push('기준 시점,시간(초)');
    rows.push(`흡입기 등장 (inhalerIN),${result.referenceTimes.inhalerIN.toFixed(1)}`);
    rows.push(`입에 대기 (faceONinhaler),${result.referenceTimes.faceONinhaler.toFixed(1)}`);
    rows.push(`흡입기 사라짐 (inhalerOUT),${result.referenceTimes.inhalerOUT.toFixed(1)}`);
    rows.push('');
  }

  // 행동 단계
  rows.push('행동 단계,결과,시간(초),신뢰도(%)');
  result.actionSteps.forEach((step) => {
    const timeStr = step.time.length > 0 ? step.time[0].toFixed(1) : '-';
    const confidenceStr = step.confidenceScore.length > 0 
      ? (step.confidenceScore[0][1] * 100).toFixed(0) 
      : '-';
    const resultStr = step.result === 'pass' ? '통과' : step.result === 'fail' ? '실패' : '알 수 없음';
    rows.push(`${step.order}. ${step.name},${resultStr},${timeStr},${confidenceStr}`);
  });
  rows.push('');

  // 요약
  if (result.summary) {
    rows.push('요약,값');
    rows.push(`총 단계 수,${result.summary.totalSteps}`);
    rows.push(`통과 단계,${result.summary.passedSteps}`);
    rows.push(`실패 단계,${result.summary.failedSteps}`);
    rows.push(`점수,${result.summary.score.toFixed(0)}%`);
  }

  return rows.join('\n');
}

export function downloadCSV(result: AnalysisResult, filename?: string): void {
  const csv = generateCSV(result);
  
  // Add BOM for UTF-8 encoding (for proper Excel display)
  const blob = new Blob(['\ufeff' + csv], { 
    type: 'text/csv;charset=utf-8;' 
  });
  
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  const finalFilename = filename || `inhaler_analysis_${Date.now()}.csv`;
  
  link.setAttribute('href', url);
  link.setAttribute('download', finalFilename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

export function downloadJSON(result: AnalysisResult, filename?: string): void {
  const json = JSON.stringify(result, null, 2);
  
  const blob = new Blob([json], { 
    type: 'application/json;charset=utf-8;' 
  });
  
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  const finalFilename = filename || `inhaler_analysis_${Date.now()}.json`;
  
  link.setAttribute('href', url);
  link.setAttribute('download', finalFilename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

