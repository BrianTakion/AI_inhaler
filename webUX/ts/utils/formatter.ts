// Data Formatting Utilities

export function formatTime(seconds: number): string {
  if (seconds < 0 || isNaN(seconds)) return '-';
  return seconds.toFixed(1);
}

export function formatPercentage(value: number): string {
  if (value < 0 || isNaN(value)) return '-%';
  return `${Math.round(value)}%`;
}

export function formatDateTime(date: Date): string {
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

export function formatDurationSeconds(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}초`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  
  if (remainingSeconds === 0) {
    return `${minutes}분`;
  }
  
  return `${minutes}분 ${remainingSeconds}초`;
}

export function estimateAnalysisTime(videoDuration: number): string {
  // Rough estimation: 10x video duration
  const estimatedSeconds = videoDuration * 10;
  return `약 ${formatDurationSeconds(estimatedSeconds)}`;
}

