// Chart Utilities using Plotly.js

import { AnalysisResult } from '../types/analysis.js';

declare const Plotly: any;

export function createTimelineChart(result: AnalysisResult): void {
  if (!result.referenceTimes || !result.videoInfo || !result.actionSteps) {
    console.error('Incomplete data for chart');
    return;
  }

  const traces: any[] = [];
  const refTimes = result.referenceTimes;

  // Reference time lines
  traces.push({
    x: [refTimes.inhalerIN, refTimes.inhalerIN],
    y: [0, 14],
    mode: 'lines',
    name: 'inhalerIN (흡입기 등장)',
    line: { color: '#0066cc', dash: 'dash', width: 2 },
    hoverinfo: 'name'
  });

  traces.push({
    x: [refTimes.faceONinhaler, refTimes.faceONinhaler],
    y: [0, 14],
    mode: 'lines',
    name: 'faceONinhaler (입에 대기)',
    line: { color: '#28a745', dash: 'dash', width: 2 },
    hoverinfo: 'name'
  });

  traces.push({
    x: [refTimes.inhalerOUT, refTimes.inhalerOUT],
    y: [0, 14],
    mode: 'lines',
    name: 'inhalerOUT (흡입기 사라짐)',
    line: { color: '#dc3545', dash: 'dash', width: 2 },
    hoverinfo: 'name'
  });

  // Action steps scatter plot
  const xValues: number[] = [];
  const yValues: number[] = [];
  const colors: string[] = [];
  const text: string[] = [];
  const sizes: number[] = [];

  result.actionSteps.forEach((step) => {
    if (step.time.length > 0) {
      step.time.forEach((t, i) => {
        xValues.push(t);
        yValues.push(step.order);
        colors.push(step.score[i] === 1 ? '#28a745' : '#dc3545');
        
        const confidence = step.confidenceScore[i] 
          ? (step.confidenceScore[i][1] * 100).toFixed(0) 
          : 'N/A';
        
        text.push(
          `${step.name}<br>` +
          `시간: ${t.toFixed(1)}초<br>` +
          `신뢰도: ${confidence}%<br>` +
          `결과: ${step.score[i] === 1 ? '통과' : '실패'}`
        );
        
        sizes.push(12);
      });
    }
  });

  traces.push({
    x: xValues,
    y: yValues,
    mode: 'markers',
    type: 'scatter',
    name: '행동 단계',
    marker: {
      size: sizes,
      color: colors,
      symbol: 'circle',
      line: {
        color: 'white',
        width: 2
      }
    },
    text: text,
    hoverinfo: 'text'
  });

  const layout = {
    title: {
      text: '흡입기 사용 타임라인',
      font: { size: 20, family: 'sans-serif' }
    },
    xaxis: {
      title: '시간 (초)',
      range: [0, result.videoInfo.duration],
      gridcolor: '#e0e0e0'
    },
    yaxis: {
      title: '행동 단계',
      tickvals: result.actionSteps.map(s => s.order),
      ticktext: result.actionSteps.map(s => `${s.order}. ${s.name}`),
      gridcolor: '#e0e0e0'
    },
    height: 600,
    showlegend: true,
    legend: {
      x: 1.05,
      y: 1
    },
    plot_bgcolor: '#ffffff',
    paper_bgcolor: '#ffffff',
    hovermode: 'closest'
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
  };

  Plotly.newPlot('timelineChart', traces, layout, config);
}

