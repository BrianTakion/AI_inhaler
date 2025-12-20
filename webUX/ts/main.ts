// Main Application Entry Point

import { DeviceSelector } from './components/DeviceSelector.js';
import { FileUploader } from './components/FileUploader.js';
import { AnalysisProgress } from './components/AnalysisProgress.js';
import { ResultsViewer } from './components/ResultsViewer.js';
import { AppState, ButtonStates } from './types/state.js';
import { AnalysisResult, DeviceType, VideoMetadata, ActionStep } from './types/analysis.js';
import { downloadCSV } from './services/csv.js';
import { estimateAnalysisTime } from './utils/formatter.js';

class InhalerAnalysisApp {
  private currentState: AppState = 'IDLE';
  private deviceSelector: DeviceSelector;
  private fileUploader: FileUploader;
  private analysisProgress: AnalysisProgress;
  private resultsViewer: ResultsViewer;
  
  private selectedDevice: DeviceType | null = null;
  private uploadedFile: File | null = null;
  private videoMetadata: VideoMetadata | null = null;
  private analysisResult: AnalysisResult | null = null;

  // UI Elements
  private buttons = {
    device: document.getElementById('deviceSelect') as HTMLButtonElement,
    file: document.getElementById('fileUpload') as HTMLButtonElement,
    analyze: document.getElementById('analyze') as HTMLButtonElement,
    save: document.getElementById('save') as HTMLButtonElement
  };

  private states = {
    idle: document.getElementById('idleState') as HTMLElement,
    deviceInfo: document.getElementById('deviceInfoState') as HTMLElement,
    videoPreview: document.getElementById('videoPreviewState') as HTMLElement,
    analyzing: document.getElementById('analyzingState') as HTMLElement,
    results: document.getElementById('resultsState') as HTMLElement,
    error: document.getElementById('errorState') as HTMLElement
  };

  constructor() {
    this.deviceSelector = new DeviceSelector();
    this.fileUploader = new FileUploader();
    this.analysisProgress = new AnalysisProgress();
    this.resultsViewer = new ResultsViewer();
    
    this.init();
  }

  private init(): void {
    this.setupEventListeners();
    this.updateUI();
  }

  private setupEventListeners(): void {
    // Device selection
    this.deviceSelector.onSelect((device) => {
      this.handleDeviceSelected(device);
    });

    // File upload
    this.fileUploader.onUpload((file, metadata) => {
      this.handleFileUploaded(file, metadata);
    });

    this.fileUploader.onError((error) => {
      this.showError('파일 업로드 오류', error);
    });

    // Analysis button
    this.buttons.analyze.addEventListener('click', () => {
      this.startAnalysis();
    });

    // Save button
    this.buttons.save.addEventListener('click', () => {
      this.saveResults();
    });

    // Modal close
    const modal = document.getElementById('errorModal') as HTMLElement;
    const modalClose = document.getElementById('modalClose') as HTMLElement;
    const closeBtn = modal.querySelector('.close') as HTMLElement;
    
    modalClose?.addEventListener('click', () => {
      modal.style.display = 'none';
    });
    
    closeBtn?.addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }

  private handleDeviceSelected(device: DeviceType): void {
    this.selectedDevice = device;
    this.currentState = 'DEVICE_SELECTED';
    
    // Update device info display
    const deviceType = document.getElementById('selectedDeviceType') as HTMLElement;
    const deviceName = document.getElementById('selectedDeviceName') as HTMLElement;
    deviceType.textContent = device.id;
    deviceName.textContent = device.description;
    
    this.updateUI();
  }

  private handleFileUploaded(file: File, metadata: VideoMetadata): void {
    this.uploadedFile = file;
    this.videoMetadata = metadata;
    this.currentState = 'FILE_UPLOADED';
    this.updateUI();
  }

  private startAnalysis(): void {
    if (!this.uploadedFile || !this.selectedDevice || !this.videoMetadata) {
      this.showError('오류', '기기와 파일을 먼저 선택해주세요.');
      return;
    }

    this.currentState = 'ANALYZING';
    this.updateUI();

    // Reset progress
    this.analysisProgress.reset();
    this.analysisProgress.addLogMessage('분석을 시작합니다...', 'info');

    // Simulate analysis (In production, this would use API + WebSocket)
    this.simulateAnalysis();
  }

  private simulateAnalysis(): void {
    // This is a simulation. In production, use real API calls and WebSocket
    const duration = this.videoMetadata?.duration || 20;
    
    this.analysisProgress.updateEstimatedTime(estimateAnalysisTime(duration));
    
    const stages = [
      { progress: 10, stage: 'VideoProcessor: 비디오 메타데이터 추출 중...', delay: 500 },
      { progress: 30, stage: 'VideoAnalyzer (gpt-4o-mini): 1차 분석 중...', delay: 2000 },
      { progress: 60, stage: 'VideoAnalyzer (gpt-4o-mini): 2차 분석 중...', delay: 2000 },
      { progress: 85, stage: 'VideoAnalyzer (gpt-4o): 최종 분석 중...', delay: 2000 },
      { progress: 95, stage: 'Reporter: 보고서 생성 중...', delay: 1000 },
      { progress: 100, stage: '분석 완료', delay: 500 }
    ];

    let currentStageIndex = 0;

    const processNextStage = () => {
      if (currentStageIndex >= stages.length) {
        this.completeAnalysis();
        return;
      }

      const stage = stages[currentStageIndex];
      this.analysisProgress.updateProgress(stage.progress);
      this.analysisProgress.updateStage(stage.stage);
      
      if (currentStageIndex > 0) {
        const prevStage = stages[currentStageIndex - 1];
        this.analysisProgress.addLogMessage(`✓ ${prevStage.stage}`, 'success');
      }

      currentStageIndex++;
      setTimeout(processNextStage, stage.delay);
    };

    processNextStage();
  }

  private completeAnalysis(): void {
    this.analysisProgress.addLogMessage('분석이 완료되었습니다!', 'success');
    
    // Generate mock analysis result
    this.analysisResult = this.generateMockResult();
    
    this.currentState = 'COMPLETED';
    this.updateUI();
    
    // Display results
    this.resultsViewer.displayResults(this.analysisResult);
  }

  private generateMockResult(): AnalysisResult {
    const actionSteps: ActionStep[] = [
      {
        id: 'sit_stand', order: 1, name: '앉거나 서 있기',
        description: '사용자가 바르게 앉거나 서 있는지 확인',
        time: [1.2], score: [1], confidenceScore: [[1.2, 0.92]], result: 'pass'
      },
      {
        id: 'remove_cover', order: 2, name: '커버 제거',
        description: '마우스피스 커버를 제거하는지 확인',
        time: [], score: [0], confidenceScore: [], result: 'fail'
      },
      {
        id: 'inspect_mouthpiece', order: 3, name: '마우스피스 점검',
        description: '마우스피스에 이물질이 있는지 점검',
        time: [3.5], score: [1], confidenceScore: [[3.5, 0.88]], result: 'pass'
      },
      {
        id: 'shake_inhaler', order: 4, name: '흡입기 흔들기',
        description: '흡입기를 충분히 흔들고 있는지 확인',
        time: [4.2], score: [1], confidenceScore: [[4.2, 0.91]], result: 'pass'
      },
      {
        id: 'hold_inhaler', order: 5, name: '흡입기를 똑바로 잡기',
        description: '흡입기를 올바르게 잡고 있는지 확인',
        time: [5.1], score: [1], confidenceScore: [[5.1, 0.94]], result: 'pass'
      },
      {
        id: 'load_dose', order: 6, name: '약물 로딩',
        description: '커버를 제거하여 약물을 로딩하는지 확인',
        time: [6.3], score: [1], confidenceScore: [[6.3, 0.89]], result: 'pass'
      },
      {
        id: 'exhale_before', order: 7, name: '흡입 전 날숨',
        description: '흡입기에서 멀리 떨어져 숨을 내쉬는지 확인',
        time: [7.8], score: [1], confidenceScore: [[7.8, 0.87]], result: 'pass'
      },
      {
        id: 'seal_lips', order: 8, name: '마우스피스에 입 대기',
        description: '마우스피스를 입에 제대로 물고 있는지 확인',
        time: [8.3], score: [1], confidenceScore: [[8.3, 0.95]], result: 'pass'
      },
      {
        id: 'inhale_deeply', order: 9, name: '깊게 흡입',
        description: '흡입기에서 깊게 숨을 들이마시는지 확인',
        time: [9.5], score: [1], confidenceScore: [[9.5, 0.93]], result: 'pass'
      },
      {
        id: 'remove_inhaler', order: 10, name: '흡입기 제거',
        description: '숨을 참으면서 흡입기를 입에서 제거하는지 확인',
        time: [11.2], score: [1], confidenceScore: [[11.2, 0.90]], result: 'pass'
      },
      {
        id: 'hold_breath', order: 11, name: '숨 참기',
        description: '약물 흡수를 위해 숨을 참고 있는지 확인',
        time: [12.8], score: [1], confidenceScore: [[12.8, 0.86]], result: 'pass'
      },
      {
        id: 'exhale_after', order: 12, name: '흡입 후 날숨',
        description: '흡입기에서 멀리 떨어져 숨을 내쉬는지 확인',
        time: [15.3], score: [1], confidenceScore: [[15.3, 0.88]], result: 'pass'
      },
      {
        id: 'replace_cover', order: 13, name: '커버 재장착',
        description: '마우스피스 커버를 다시 닫는지 확인',
        time: [17.9], score: [1], confidenceScore: [[17.9, 0.91]], result: 'pass'
      }
    ];

    const passedSteps = actionSteps.filter(s => s.result === 'pass').length;
    const failedSteps = actionSteps.filter(s => s.result === 'fail').length;

    return {
      status: 'completed',
      deviceType: this.selectedDevice?.id || null,
      videoInfo: this.videoMetadata,
      referenceTimes: {
        inhalerIN: 2.5,
        faceONinhaler: 8.3,
        inhalerOUT: 18.7
      },
      actionSteps,
      summary: {
        totalSteps: 13,
        passedSteps,
        failedSteps,
        score: (passedSteps / 13) * 100
      },
      modelInfo: {
        models: ['gpt-4o-mini', 'gpt-4o-mini', 'gpt-4o'],
        analysisTime: 204  // 3분 24초
      },
      errors: []
    };
  }

  private saveResults(): void {
    if (!this.analysisResult) {
      this.showError('오류', '저장할 분석 결과가 없습니다.');
      return;
    }

    try {
      const filename = `inhaler_analysis_${this.selectedDevice?.id}_${Date.now()}.csv`;
      downloadCSV(this.analysisResult, filename);
      this.showSuccess('결과가 성공적으로 저장되었습니다.');
    } catch (error) {
      console.error('Save error:', error);
      this.showError('저장 오류', '결과 저장 중 오류가 발생했습니다.');
    }
  }

  private updateUI(): void {
    this.updateButtonStates();
    this.updateVisibleState();
  }

  private updateButtonStates(): void {
    const states: Record<AppState, ButtonStates> = {
      'IDLE': {
        device: false,
        file: true,
        analyze: true,
        save: true
      },
      'DEVICE_SELECTED': {
        device: false,
        file: false,
        analyze: true,
        save: true
      },
      'FILE_UPLOADED': {
        device: false,
        file: false,
        analyze: false,
        save: true
      },
      'ANALYZING': {
        device: true,
        file: true,
        analyze: true,
        save: true
      },
      'COMPLETED': {
        device: false,
        file: false,
        analyze: false,
        save: false
      },
      'ERROR': {
        device: false,
        file: false,
        analyze: false,
        save: true
      }
    };

    const buttonStates = states[this.currentState];
    this.buttons.device.disabled = buttonStates.device;
    this.buttons.file.disabled = buttonStates.file;
    this.buttons.analyze.disabled = buttonStates.analyze;
    this.buttons.save.disabled = buttonStates.save;
  }

  private updateVisibleState(): void {
    // Hide all states
    Object.values(this.states).forEach(state => {
      state.style.display = 'none';
    });

    // Show appropriate states based on current state
    switch (this.currentState) {
      case 'IDLE':
        this.states.idle.style.display = 'flex';
        break;
        
      case 'DEVICE_SELECTED':
        this.states.idle.style.display = 'flex';
        this.states.deviceInfo.style.display = 'block';
        break;
        
      case 'FILE_UPLOADED':
        this.states.deviceInfo.style.display = 'block';
        this.states.videoPreview.style.display = 'block';
        break;
        
      case 'ANALYZING':
        this.states.analyzing.style.display = 'block';
        break;
        
      case 'COMPLETED':
        this.states.results.style.display = 'block';
        break;
        
      case 'ERROR':
        this.states.error.style.display = 'flex';
        break;
    }
  }

  private showError(title: string, message: string): void {
    const modal = document.getElementById('errorModal') as HTMLElement;
    const modalTitle = document.getElementById('modalTitle') as HTMLElement;
    const modalMessage = document.getElementById('modalMessage') as HTMLElement;
    
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    modal.style.display = 'flex';
  }

  private showSuccess(message: string): void {
    // Simple alert for success (can be improved with a custom modal)
    alert(message);
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new InhalerAnalysisApp();
});

