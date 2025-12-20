// File Uploader Component

import { validateVideoFile, formatFileSize, formatDuration } from '../utils/validation.js';
import { VideoMetadata, VideoValidation } from '../types/analysis.js';

export class FileUploader {
  private fileBtn: HTMLButtonElement;
  private fileInput: HTMLInputElement;
  private videoPlayer: HTMLVideoElement;
  private onUploadCallback?: (file: File, metadata: VideoMetadata) => void;
  private onErrorCallback?: (error: string) => void;

  constructor() {
    this.fileBtn = document.getElementById('fileUpload') as HTMLButtonElement;
    this.fileInput = document.getElementById('fileInput') as HTMLInputElement;
    this.videoPlayer = document.getElementById('videoPlayer') as HTMLVideoElement;
    this.init();
  }

  private init(): void {
    this.fileBtn.addEventListener('click', () => {
      this.fileInput.click();
    });

    this.fileInput.addEventListener('change', async (e) => {
      const target = e.target as HTMLInputElement;
      const file = target.files?.[0];
      if (file) {
        await this.handleFileUpload(file);
      }
    });
  }

  private async handleFileUpload(file: File): Promise<void> {
    try {
      const validation: VideoValidation = await validateVideoFile(file);

      if (!validation.isValid) {
        if (this.onErrorCallback) {
          this.onErrorCallback(validation.error || '파일 검증 실패');
        }
        return;
      }

      if (!validation.metadata) {
        if (this.onErrorCallback) {
          this.onErrorCallback('비디오 메타데이터를 읽을 수 없습니다.');
        }
        return;
      }

      // Display video
      this.displayVideo(file, validation.metadata);

      // Trigger callback
      if (this.onUploadCallback) {
        this.onUploadCallback(file, validation.metadata);
      }
    } catch (error) {
      console.error('File upload error:', error);
      if (this.onErrorCallback) {
        this.onErrorCallback('파일 업로드 중 오류가 발생했습니다.');
      }
    }
  }

  private displayVideo(file: File, metadata: VideoMetadata): void {
    // Set video source
    const url = URL.createObjectURL(file);
    this.videoPlayer.src = url;
    
    // Set video attributes for better MOV file support
    this.videoPlayer.preload = 'metadata';
    this.videoPlayer.setAttribute('playsinline', '');
    
    // Force load to ensure thumbnail displays for MOV files
    this.videoPlayer.load();

    // Update video info
    document.getElementById('fileName')!.textContent = metadata.fileName;
    document.getElementById('duration')!.textContent = formatDuration(metadata.duration);
    document.getElementById('fileSize')!.textContent = formatFileSize(metadata.size);
    document.getElementById('resolution')!.textContent = metadata.resolution;
  }

  public onUpload(callback: (file: File, metadata: VideoMetadata) => void): void {
    this.onUploadCallback = callback;
  }

  public onError(callback: (error: string) => void): void {
    this.onErrorCallback = callback;
  }

  public reset(): void {
    this.fileInput.value = '';
    this.videoPlayer.src = '';
    document.getElementById('fileName')!.textContent = '-';
    document.getElementById('duration')!.textContent = '-';
    document.getElementById('fileSize')!.textContent = '-';
    document.getElementById('resolution')!.textContent = '-';
  }
}

