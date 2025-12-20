// Video File Validation Utilities

import { VideoValidation } from '../types/analysis.js';

const VALID_TYPES = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska'
];

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

export function validateVideoFile(file: File): Promise<VideoValidation> {
  return new Promise((resolve) => {
    if (!VALID_TYPES.includes(file.type)) {
      resolve({
        isValid: false,
        error: "동영상 파일을 선택하여 주십시오. (지원 형식: MP4, MOV, AVI, MKV)"
      });
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      resolve({
        isValid: false,
        error: "파일 크기가 너무 큽니다. (최대 500MB)"
      });
      return;
    }

    // Extract video metadata
    const video = document.createElement('video');
    video.preload = 'metadata';

    video.onloadedmetadata = () => {
      window.URL.revokeObjectURL(video.src);
      resolve({
        isValid: true,
        metadata: {
          fileName: file.name,
          duration: video.duration,
          size: file.size,
          resolution: `${video.videoWidth} × ${video.videoHeight}`,
          type: file.type,
          width: video.videoWidth,
          height: video.videoHeight
        }
      });
    };

    video.onerror = () => {
      resolve({
        isValid: false,
        error: "동영상 파일을 읽을 수 없습니다."
      });
    };

    video.src = URL.createObjectURL(file);
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

