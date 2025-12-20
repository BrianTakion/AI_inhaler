// Analysis Progress Component

import { LogEntry, ProgressUpdate } from '../types/analysis.js';

export class AnalysisProgress {
  private progressFill: HTMLElement;
  private progressText: HTMLElement;
  private currentStage: HTMLElement;
  private estimatedTime: HTMLElement;
  private logList: HTMLElement;

  constructor() {
    this.progressFill = document.getElementById('progressFill') as HTMLElement;
    this.progressText = document.getElementById('progressText') as HTMLElement;
    this.currentStage = document.getElementById('currentStage') as HTMLElement;
    this.estimatedTime = document.getElementById('estimatedTime') as HTMLElement;
    this.logList = document.getElementById('logList') as HTMLElement;
  }

  public updateProgress(progress: number): void {
    const clampedProgress = Math.max(0, Math.min(100, progress));
    this.progressFill.style.width = `${clampedProgress}%`;
    this.progressText.textContent = `${Math.round(clampedProgress)}%`;
  }

  public updateStage(stage: string): void {
    this.currentStage.textContent = stage;
  }

  public updateEstimatedTime(time: string): void {
    this.estimatedTime.textContent = time;
  }

  public update(update: ProgressUpdate): void {
    this.updateProgress(update.progress);
    this.updateStage(update.currentStage);
    this.updateEstimatedTime(update.estimatedTime);
  }

  public addLog(log: LogEntry): void {
    const li = document.createElement('li');
    li.className = `log-${log.level}`;
    
    const icon = this.getLogIcon(log.level);
    li.textContent = `${icon} ${log.message}`;
    
    this.logList.appendChild(li);
    
    // Auto-scroll to bottom
    this.logList.scrollTop = this.logList.scrollHeight;
  }

  public addLogMessage(message: string, level: LogEntry['level'] = 'info'): void {
    this.addLog({
      message,
      level,
      timestamp: new Date()
    });
  }

  private getLogIcon(level: LogEntry['level']): string {
    switch (level) {
      case 'success': return '✓';
      case 'progress': return '⟳';
      case 'pending': return '⋯';
      case 'error': return '✗';
      case 'info': return 'ℹ';
      default: return '•';
    }
  }

  public clearLogs(): void {
    this.logList.innerHTML = '';
  }

  public reset(): void {
    this.updateProgress(0);
    this.updateStage('초기화 중...');
    this.updateEstimatedTime('계산 중...');
    this.clearLogs();
  }
}

