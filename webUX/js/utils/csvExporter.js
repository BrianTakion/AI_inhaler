// CSV Export Utility
// 분석 결과를 CSV 파일로 내보내는 유틸리티

class CSVExporter {
    /**
     * 분석 결과를 CSV 파일로 내보내기
     * @param {Object} result - 분석 결과 객체
     * @param {string} deviceType - 디바이스 타입
     * @param {File} file - 업로드된 파일
     */
    export(result, deviceType, file) {
        const rows = [];
        
        // 헤더
        rows.push(['항목', '값']);
        rows.push([]);
        
        // 기기 정보
        rows.push(['기기 선택', deviceType || '']);
        rows.push(['분석한 파일', file ? file.name : '']);
        rows.push([]);
        
        // 비디오 정보
        if (result.videoInfo) {
            rows.push(['비디오 정보']);
            rows.push(['파일명', result.videoInfo.fileName || '']);
            rows.push(['재생시간', `${result.videoInfo.duration || 0}초`]);
            rows.push(['해상도', result.videoInfo.resolution || '']);
            rows.push(['프레임 수', result.videoInfo.frameCount || '']);
            rows.push(['파일 크기', this.formatFileSize(result.videoInfo.size || 0)]);
            rows.push([]);
        }
        
        // 요약 정보
        if (result.summary) {
            rows.push(['요약 정보']);
            rows.push(['총 단계', result.summary.totalSteps || 0]);
            rows.push(['통과 단계', result.summary.passedSteps || 0]);
            rows.push(['실패 단계', result.summary.failedSteps || 0]);
            rows.push(['점수', `${(result.summary.score || 0).toFixed(1)}%`]);
            rows.push([]);
        }
        
        // 모델 정보
        if (result.modelInfo) {
            rows.push(['모델 정보']);
            rows.push(['사용 모델', result.modelInfo.models ? result.modelInfo.models.join(', ') : '']);
            rows.push(['분석 시간', `${result.modelInfo.analysisTime || 0}초`]);
            rows.push([]);
        }
        
        // 최종 종합 기술
        rows.push(['최종 종합 기술']);
        if (result.finalSummary) {
            const summaryLines = result.finalSummary.split('\n');
            summaryLines.forEach(line => {
                rows.push([line]);
            });
        } else {
            rows.push(['종합 기술 정보가 없습니다.']);
        }
        rows.push([]);
        
        // 행동 단계 상세
        rows.push(['행동 단계 상세']);
        rows.push(['순서', 'ID', '이름', '설명', '시간', '점수', '결과', '신뢰도']);
        
        if (result.actionSteps && result.actionSteps.length > 0) {
            result.actionSteps.forEach(step => {
                const timeStr = step.time && step.time.length > 0 
                    ? step.time.join(', ') 
                    : '미감지';
                const scoreStr = step.score && step.score.length > 0 
                    ? step.score.join(', ') 
                    : '0';
                const resultStr = step.result === 'pass' ? '통과' : '실패';
                const confidenceStr = step.confidenceScore && step.confidenceScore.length > 0
                    ? step.confidenceScore.map(c => `${c[0]}s:${(c[1] * 100).toFixed(0)}%`).join(', ')
                    : 'N/A';
                
                rows.push([
                    step.order || '',
                    step.id || '',
                    step.name || '',
                    step.description || '',
                    timeStr,
                    scoreStr,
                    resultStr,
                    confidenceStr
                ]);
            });
        }
        
        // CSV 문자열 생성
        const csvContent = rows.map(row => {
            return row.map(cell => {
                const cellStr = String(cell || '');
                // CSV 이스케이프: 쌍따옴표를 두 개로 변환
                const escaped = cellStr.replace(/"/g, '""');
                return `"${escaped}"`;
            }).join(',');
        }).join('\n');
        
        // BOM 추가 (한글 깨짐 방지)
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csvContent], { 
            type: 'text/csv;charset=utf-8;' 
        });
        
        // 다운로드
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        link.setAttribute('download', `inhaler_analysis_${deviceType || 'unknown'}_${timestamp}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // URL 해제
        setTimeout(() => URL.revokeObjectURL(url), 100);
    }
    
    /**
     * 파일 크기 포맷팅
     * @param {number} bytes - 바이트 수
     * @returns {string} 포맷된 파일 크기
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Export for use in other modules
export default CSVExporter;

