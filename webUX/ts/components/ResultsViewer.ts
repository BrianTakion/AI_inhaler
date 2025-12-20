// Results Viewer Component

import { AnalysisResult, ActionStep } from '../types/analysis.js';
import { formatTime, formatPercentage, formatDurationSeconds } from '../utils/formatter.js';
import { createTimelineChart } from '../utils/chart.js';

export class ResultsViewer {
  constructor() {}

  public displayResults(result: AnalysisResult): void {
    this.displaySummary(result);
    this.displayReferenceTimes(result);
    this.displayActionSteps(result);
    this.displayChart(result);
  }

  private displaySummary(result: AnalysisResult): void {
    if (!result.summary) return;

    const scoreValue = document.getElementById('scoreValue') as HTMLElement;
    const scorePercentage = document.getElementById('scorePercentage') as HTMLElement;
    const modelInfo = document.getElementById('modelInfo') as HTMLElement;
    const analysisTime = document.getElementById('analysisTime') as HTMLElement;

    scoreValue.textContent = result.summary.passedSteps.toString();
    scorePercentage.textContent = formatPercentage(result.summary.score);

    if (result.modelInfo) {
      modelInfo.textContent = result.modelInfo.models.join(' × ');
      analysisTime.textContent = formatDurationSeconds(result.modelInfo.analysisTime);
    }
  }

  private displayReferenceTimes(result: AnalysisResult): void {
    if (!result.referenceTimes) return;

    const tbody = document.getElementById('referenceTimesBody') as HTMLElement;
    const timeValues = tbody.querySelectorAll('.time-value');

    if (timeValues.length >= 3) {
      timeValues[0].textContent = formatTime(result.referenceTimes.inhalerIN);
      timeValues[1].textContent = formatTime(result.referenceTimes.faceONinhaler);
      timeValues[2].textContent = formatTime(result.referenceTimes.inhalerOUT);
    }
  }

  private displayActionSteps(result: AnalysisResult): void {
    const actionList = document.getElementById('actionList') as HTMLElement;
    actionList.innerHTML = '';

    result.actionSteps.forEach(step => {
      const card = this.createActionCard(step);
      actionList.appendChild(card);
    });
  }

  private createActionCard(step: ActionStep): HTMLElement {
    const card = document.createElement('div');
    card.className = 'action-card';
    card.setAttribute('data-result', step.result);

    const header = document.createElement('div');
    header.className = 'action-header';

    const number = document.createElement('span');
    number.className = 'action-number';
    number.textContent = step.order.toString();

    const name = document.createElement('h5');
    name.className = 'action-name';
    name.textContent = step.name;

    const resultBadge = document.createElement('span');
    resultBadge.className = `action-result ${step.result}`;
    resultBadge.textContent = this.getResultText(step.result);

    header.appendChild(number);
    header.appendChild(name);
    header.appendChild(resultBadge);

    const body = document.createElement('div');
    body.className = 'action-body';

    const description = document.createElement('p');
    description.className = 'action-description';
    description.textContent = step.description;

    const details = document.createElement('div');
    details.className = 'action-details';

    const timeItem = document.createElement('span');
    timeItem.className = 'detail-item';
    const timeValue = step.time.length > 0 ? formatTime(step.time[0]) : '미감지';
    timeItem.textContent = `시간: ${timeValue}초`;

    const confidenceItem = document.createElement('span');
    confidenceItem.className = 'detail-item';
    const confidence = step.confidenceScore.length > 0 
      ? Math.round(step.confidenceScore[0][1] * 100)
      : 0;
    confidenceItem.textContent = `신뢰도: ${confidence}%`;

    details.appendChild(timeItem);
    details.appendChild(confidenceItem);

    body.appendChild(description);
    body.appendChild(details);

    card.appendChild(header);
    card.appendChild(body);

    return card;
  }

  private getResultText(result: ActionStep['result']): string {
    switch (result) {
      case 'pass': return '통과';
      case 'fail': return '실패';
      case 'unknown': return '알 수 없음';
      default: return '-';
    }
  }

  private displayChart(result: AnalysisResult): void {
    try {
      createTimelineChart(result);
    } catch (error) {
      console.error('Failed to create chart:', error);
    }
  }

  public clear(): void {
    const actionList = document.getElementById('actionList') as HTMLElement;
    actionList.innerHTML = '';

    const chartContainer = document.getElementById('timelineChart') as HTMLElement;
    chartContainer.innerHTML = '';
  }
}

