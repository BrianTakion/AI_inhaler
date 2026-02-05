// Main Application
// 메인 애플리케이션 로직

import APIClient from './api.js';
import CSVExporter from './utils/csvExporter.js';

class InhalerAnalysisApp {
    constructor() {
        this.api = new APIClient();
        this.csvExporter = new CSVExporter();
        
        // 상태 관리
        this.selectedDevice = null;
        this.uploadedFile = null;
        this.videoId = null;
        this.analysisId = null;
        this.analysisResult = null;
        this.statusPollInterval = null;
        this.progressInterval = null; // 프로그레스 바 자동 증가용
        this.analysisStartTime = null; // 분석 시작 시간
        this.progressUpdateInterval = null; // 진행 중 로그 업데이트용
        
        // LLM 모델 정보 (백엔드에서 조회)
        this.llmModels = [];
        
        this.init();
    }
    
    /**
     * 초기화
     */
    async init() {
        this.setupEventListeners();
        // [FIX] 페이지 로드 시 자동 초기화 — 사용자 수동 초기화에 의존하지 않고
        // 브라우저 back/forward 캐시(bfcache)에서 복원된 stale 상태를 방지.
        this.resetAll();
        await this.loadServerConfig();
        this.checkServerConnection();
    }
    
    /**
     * 서버 설정 정보 로드
     */
    async loadServerConfig() {
        try {
            const config = await this.api.getConfig();
            this.llmModels = config.llmModels || [];
        } catch (error) {
            console.error('서버 설정 조회 실패:', error);
            // 서버 조회 실패 시 빈 배열로 설정 (UI에서 "-"로 표시됨)
            this.llmModels = [];
        }
    }
    
    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 기기 선택 버튼
        document.getElementById('deviceSelectBtn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDeviceDropdown();
        });
        
        // 드롭다운 외부 클릭 시 닫기
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('deviceDropdown');
            const btn = document.getElementById('deviceSelectBtn');
            if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
        
        // 드롭다운 아이템 클릭
        document.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const deviceId = item.dataset.deviceId;
                this.selectDevice(deviceId);
                document.getElementById('deviceDropdown').classList.add('hidden');
            });
        });
        
        // 파일 업로드 버튼
        document.getElementById('fileUploadBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        // 파일 선택
        document.getElementById('fileInput').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
            // [FIX] iPhone Safari에서 같은 파일을 다시 선택할 수 있도록 value 초기화.
            // value를 초기화하지 않으면 동일 파일 선택 시 change 이벤트가 발생하지 않음.
            e.target.value = '';
        });
        
        // 분석 시작 버튼
        document.getElementById('startAnalysisBtn').addEventListener('click', () => {
            this.startAnalysis();
        });
        
        // 결과 저장 버튼
        document.getElementById('saveResultBtn').addEventListener('click', () => {
            this.saveResults();
        });

        // 초기화 버튼
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetAll();
        });

        // 에러 모달 닫기
        document.getElementById('errorCloseBtn').addEventListener('click', () => {
            document.getElementById('errorModal').classList.add('hidden');
        });
    }
    
    /**
     * 기기 선택 드롭다운 토글
     */
    toggleDeviceDropdown() {
        const dropdown = document.getElementById('deviceDropdown');
        dropdown.classList.toggle('hidden');
    }
    
    /**
     * 기기 선택
     * @param {string} deviceId - 디바이스 ID
     */
    selectDevice(deviceId) {
        this.selectedDevice = deviceId;
        const btn = document.getElementById('deviceSelectBtn');
        btn.textContent = `기기 선택: ${deviceId} ▼`;
        this.updateButtonStates();
    }
    
    /**
     * 파일 선택 및 업로드
     * @param {File} file - 선택된 파일
     */
    async handleFileSelect(file) {
        if (!file) return;
        
        // 파일 검증
        if (!this.validateFile(file)) {
            this.showError('파일 오류', '지원하지 않는 파일 형식이거나 파일 크기가 너무 큽니다.\n지원 형식: MP4, MOV, AVI, MKV\n최대 크기: 500MB');
            return;
        }
        
        // 업로드 프롬프트 영역 숨기기
        const uploadPrompt = document.getElementById('uploadPrompt');
        if (uploadPrompt) {
            uploadPrompt.classList.add('hidden');
        }
        
        // 파일 정보 표시 (업로드 전)
        this.displayFileInfo(file);
        
        // 비디오 스냅샷 표시
        this.displayVideoSnapshot(file);
        
        try {
            // 업로드 시작 UI
            this.showUploadProgress();
            
            // 파일 업로드
            const response = await this.api.uploadVideo(file);
            
            this.uploadedFile = file;
            this.videoId = response.videoId;
            
            // 업로드 성공 UI
            this.showUploadSuccess(file, response.metadata);
            this.updateButtonStates();
        } catch (error) {
            console.error('파일 업로드 오류:', error);
            this.showError('파일 업로드 실패', error.message || '파일을 업로드할 수 없습니다.');
            this.hideUploadInfo();
            this.hideFileInfo();
            this.hideVideoSnapshot();
            
            // 업로드 프롬프트 영역 다시 표시
            const uploadPrompt = document.getElementById('uploadPrompt');
            if (uploadPrompt) {
                uploadPrompt.classList.remove('hidden');
            }
        }
    }
    
    /**
     * 분석 시작
     */
    async startAnalysis() {
        if (!this.selectedDevice || !this.videoId) {
            this.showError('오류', '기기와 파일을 먼저 선택해주세요.');
            return;
        }

        // [FIX] 기존 타이머/폴링 정리 (이전 분석에서 남은 상태 방지)
        this.stopStatusPolling();

        // [FIX] 분석 진행 중 중복 클릭 방지
        const startBtn = document.getElementById('startAnalysisBtn');
        startBtn.disabled = true;

        // [FIX] 프로그레스 바를 0%로 초기화 (이전 분석의 100% 값이 남아있는 문제 방지)
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressStage = document.getElementById('progressStage');
        if (progressFill) progressFill.style.width = '0%';
        if (progressPercent) progressPercent.textContent = '0%';
        if (progressStage) progressStage.textContent = '처리 중...';

        try {
            // 분석 시작 시간 기록
            this.analysisStartTime = new Date();

            // 분석 로그 초기화 및 시작 시간 표시
            this.clearAnalysisLogs();
            const startTimeStr = this.analysisStartTime.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            this.addLog(`시작시간: ${startTimeStr}`);

            // 분석 정보 표시
            this.showAnalysisInfo();

            // 프로그레스 바 자동 증가 시작 (3초마다)
            this.startProgressAutoUpdate();

            // 진행 중 로그 업데이트 시작 (10초마다)
            this.startProgressLogUpdate();

            // 분석 시작 API 호출
            const response = await this.api.startAnalysis(
                this.videoId,
                this.selectedDevice,
                true  // saveIndividualReport
            );

            this.analysisId = response.analysisId;

            // 상태 폴링 시작
            this.startStatusPolling();
        } catch (error) {
            console.error('분석 시작 오류:', error);
            this.showError('분석 시작 실패', error.message || '분석을 시작할 수 없습니다.');
            this.stopProgressAutoUpdate();
            this.stopProgressLogUpdate();
            // [FIX] 오류 시 버튼 다시 활성화
            startBtn.disabled = !(this.selectedDevice && this.videoId);
        }
    }
    
    /**
     * 프로그레스 바 자동 증가 (3초마다)
     */
    startProgressAutoUpdate() {
        let currentProgress = 0;
        
        this.progressInterval = setInterval(() => {
            if (currentProgress < 95) { // 95%까지만 자동 증가
                currentProgress += 1;
                const progressFill = document.getElementById('progressFill');
                const progressPercent = document.getElementById('progressPercent');
                const progressStage = document.getElementById('progressStage');
                
                if (progressFill && progressPercent) {
                    progressFill.style.width = `${currentProgress}%`;
                    progressPercent.textContent = `${currentProgress}%`;
                }
                if (progressStage && !progressStage.textContent.includes('완료')) {
                    progressStage.textContent = '처리 중...';
                }
            }
        }, 7000); // 7초마다
    }
    
    /**
     * 프로그레스 바 자동 증가 중지
     */
    stopProgressAutoUpdate() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    /**
     * 진행 중 로그 업데이트 (10초마다)
     */
    startProgressLogUpdate() {
        this.progressUpdateInterval = setInterval(() => {
            if (this.analysisStartTime) {
                const elapsed = Math.floor((new Date() - this.analysisStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                const timeStr = `${minutes}분 ${seconds}초`;
                this.addLog(`진행 중: ${timeStr}`);
            }
        }, 10000); // 10초마다
    }
    
    /**
     * 진행 중 로그 업데이트 중지
     */
    stopProgressLogUpdate() {
        if (this.progressUpdateInterval) {
            clearInterval(this.progressUpdateInterval);
            this.progressUpdateInterval = null;
        }
    }
    
    /**
     * 분석 상태 폴링 시작
     */
    startStatusPolling() {
        const NORMAL_POLL_INTERVAL = 2000;   // 정상 폴링 간격: 2초
        const SLOW_POLL_INTERVAL = 5000;     // 헬스체크 통과 후 폴링 간격: 5초
        const MAX_POLL_DURATION_MS = 40 * 60 * 1000; // 전체 폴링 타임아웃: 40분
        const MAX_CONSECUTIVE_ERRORS = 30;   // 연속 오류 상한: 30회 (60초)
        const MAX_HEALTH_CHECK_FAILS = 3;    // 헬스체크 연속 실패 상한 (일시적 끊김 내성 강화)
        const NETWORK_WARNING_THRESHOLD = 5; // 네트워크 경고 표시 기준: 연속 5회 오류
        const pollStartTime = Date.now();
        let consecutiveErrors = 0;
        let healthCheckFailCount = 0;
        let currentPollInterval = NORMAL_POLL_INTERVAL;

        const poll = async () => {
            // 전체 타임아웃 검사
            if (Date.now() - pollStartTime > MAX_POLL_DURATION_MS) {
                this.stopStatusPolling();
                this.hideNetworkWarning();
                this.updateButtonStates();
                this.showError('분석 시간 초과',
                    '서버 응답 대기 시간이 초과되었습니다. 페이지를 새로고침한 후 다시 시도해주세요.');
                return;
            }

            try {
                const status = await this.api.getAnalysisStatus(this.analysisId);
                consecutiveErrors = 0;
                healthCheckFailCount = 0;
                currentPollInterval = NORMAL_POLL_INTERVAL;
                this.hideNetworkWarning();

                // 프로그레스 바 업데이트 (서버에서 받은 실제 진행률 사용)
                this.updateProgressBar(status.progress, status.current_stage);

                if (status.status === 'completed') {
                    this.stopStatusPolling();
                    this.stopProgressAutoUpdate();
                    this.stopProgressLogUpdate();
                    await this.loadAnalysisResult();
                } else if (status.status === 'error') {
                    this.stopStatusPolling();
                    this.stopProgressAutoUpdate();
                    this.stopProgressLogUpdate();
                    this.updateButtonStates();
                    this.showError('분석 오류', status.error || '알 수 없는 오류가 발생했습니다.');
                } else {
                    this.statusPollInterval = setTimeout(poll, currentPollInterval);
                }
            } catch (error) {
                console.error('상태 조회 오류:', error);

                // 404 "분석 작업을 찾을 수 없습니다" → 서버 재시작으로 데이터 유실
                if (error.message && error.message.includes('분석 작업을 찾을 수 없습니다')) {
                    this.stopStatusPolling();
                    this.hideNetworkWarning();
                    this.updateButtonStates();
                    this.showError('분석 데이터 유실',
                        '서버가 재시작되어 분석 데이터가 유실되었습니다. 다시 분석을 시작해주세요.');
                    return;
                }

                consecutiveErrors++;

                // 네트워크 불안정 경고 표시 (비침습적)
                if (consecutiveErrors >= NETWORK_WARNING_THRESHOLD) {
                    this.showNetworkWarning('네트워크 연결이 불안정합니다. 자동으로 재시도 중...');
                }

                // 오류 유형에 따라 허용 한도를 차등 적용
                // 타임아웃은 서버가 바쁜 것일 수 있으므로 ×1.5 배 더 관대하게 처리
                const isTimeout = error.message && error.message.includes('시간이 초과');
                const effectiveMaxErrors = isTimeout ?
                    Math.floor(MAX_CONSECUTIVE_ERRORS * 1.5) : MAX_CONSECUTIVE_ERRORS;

                if (consecutiveErrors >= effectiveMaxErrors) {
                    // 서버 헬스체크 수행
                    console.log(`연속 오류 상한 도달 (${consecutiveErrors}/${effectiveMaxErrors}), 서버 헬스체크 수행...`);
                    const isServerAlive = await this.api.checkHealth();

                    if (isServerAlive) {
                        // 서버는 살아있음 → 카운터 리셋, 느린 간격으로 계속 폴링
                        console.log('서버 헬스체크 통과, 폴링 계속 (간격: 5초)');
                        consecutiveErrors = 0;
                        healthCheckFailCount = 0;
                        currentPollInterval = SLOW_POLL_INTERVAL;
                        this.statusPollInterval = setTimeout(poll, currentPollInterval);
                    } else {
                        // 서버 헬스체크 실패
                        healthCheckFailCount++;
                        console.log(`서버 헬스체크 실패 (${healthCheckFailCount}/${MAX_HEALTH_CHECK_FAILS})`);

                        if (healthCheckFailCount >= MAX_HEALTH_CHECK_FAILS) {
                            // 3회 연속 헬스체크 실패 → 최종 오류
                            this.stopStatusPolling();
                            this.hideNetworkWarning();
                            this.updateButtonStates();
                            this.showError('서버 연결 오류',
                                '서버와의 연결이 끊어졌습니다. 페이지를 새로고침한 후 다시 시도해주세요.');
                            return;
                        }

                        // 아직 재시도 기회 남음 → 카운터 리셋, 점진적 대기 후 계속
                        consecutiveErrors = 0;
                        const backoffMs = 3000 * healthCheckFailCount;
                        currentPollInterval = SLOW_POLL_INTERVAL;
                        this.statusPollInterval = setTimeout(poll, backoffMs);
                    }
                } else {
                    this.statusPollInterval = setTimeout(poll, currentPollInterval);
                }
            }
        };

        // 첫 폴링 시작
        poll();
    }
    
    /**
     * 상태 폴링 중지
     */
    stopStatusPolling() {
        if (this.statusPollInterval) {
            clearTimeout(this.statusPollInterval);
            this.statusPollInterval = null;
        }
        this.stopProgressAutoUpdate();
        this.stopProgressLogUpdate();
    }

    /**
     * 전체 초기화
     * 모든 상태, 타이머, UI를 초기 상태로 되돌림.
     * 분석 진행 중이거나 완료 후 새로운 분석을 시작할 때 사용.
     */
    resetAll() {
        // 1. 모든 타이머/폴링 중지
        this.stopStatusPolling();

        // 2. 앱 상태 초기화
        this.selectedDevice = null;
        this.uploadedFile = null;
        this.videoId = null;
        this.analysisId = null;
        this.analysisResult = null;
        this.analysisStartTime = null;

        // 3. 파일 입력 초기화
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';

        // 4. 비디오 스냅샷 blob URL 해제 (메모리 정리)
        const videoSnapshotSource = document.getElementById('videoSnapshotSource');
        if (videoSnapshotSource && videoSnapshotSource.src) {
            URL.revokeObjectURL(videoSnapshotSource.src);
            videoSnapshotSource.src = '';
        }

        // 5. UI 영역 초기화 (업로드 영역만 표시)
        document.getElementById('uploadArea').classList.remove('hidden');
        document.getElementById('analysisArea').classList.add('hidden');
        document.getElementById('resultArea').classList.add('hidden');

        // 6. 업로드 프롬프트 복원
        const uploadPrompt = document.getElementById('uploadPrompt');
        if (uploadPrompt) uploadPrompt.classList.remove('hidden');

        // 7. 업로드 정보/파일 정보/스냅샷 숨기기
        document.getElementById('uploadedFileInfo').classList.add('hidden');
        document.getElementById('fileInfoDisplay').classList.add('hidden');
        document.getElementById('videoSnapshotDisplay').classList.add('hidden');

        // 8. 프로그레스 바 초기화
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressStage = document.getElementById('progressStage');
        if (progressFill) progressFill.style.width = '0%';
        if (progressPercent) progressPercent.textContent = '0%';
        if (progressStage) progressStage.textContent = '처리 중...';

        // 9. 분석 로그 초기화
        this.clearAnalysisLogs();

        // 10. 기기 선택 버튼 텍스트 복원
        document.getElementById('deviceSelectBtn').textContent = '1. 기기 선택 ▼';

        // 11. 에러 모달 닫기
        document.getElementById('errorModal').classList.add('hidden');

        // 12. 버튼 상태 초기화
        this.updateButtonStates();
    }

    /**
     * 분석 결과 로드
     */
    async loadAnalysisResult() {
        try {
            const result = await this.api.getAnalysisResult(this.analysisId);
            this.analysisResult = result;
            
            // 결과 표시
            this.displayResults(result);
            this.updateButtonStates();
        } catch (error) {
            console.error('결과 로드 오류:', error);
            this.showError('결과 로드 실패', error.message || '분석 결과를 불러올 수 없습니다.');
        }
    }
    
    /**
     * 결과 표시
     * @param {Object} result - 분석 결과
     */
    displayResults(result) {
        // 결과 영역 표시
        document.getElementById('resultArea').classList.remove('hidden');
        document.getElementById('analysisArea').classList.add('hidden');
        document.getElementById('uploadArea').classList.add('hidden');
        
        // 비디오 정보 - 원본 파일명 사용
        if (result.videoInfo) {
            // 원본 파일명 표시 (업로드된 파일의 원본 이름)
            const originalFileName = this.uploadedFile ? this.uploadedFile.name : (result.videoInfo.fileName || '-');
            document.getElementById('resultFileName').textContent = originalFileName;
            document.getElementById('resultDuration').textContent = `${(result.videoInfo.duration || 0).toFixed(1)}초`;
            document.getElementById('resultResolution').textContent = result.videoInfo.resolution || '-';
            document.getElementById('resultFrameCount').textContent = result.videoInfo.frameCount || '-';
        }
        
        // 요약 정보
        if (result.summary) {
            document.getElementById('summaryTotal').textContent = result.summary.totalSteps || 0;
            document.getElementById('summaryPassed').textContent = result.summary.passedSteps || 0;
            document.getElementById('summaryFailed').textContent = result.summary.failedSteps || 0;
            document.getElementById('summaryScore').textContent = `${(result.summary.score || 0).toFixed(1)}%`;
        }
        
        // 모델 정보
        if (result.modelInfo) {
            const models = result.modelInfo.models || [];
            document.getElementById('modelNames').textContent = models.join(', ');
            
            // 분석에 소요된 경과시간 계산 (분석 시작 시간부터 현재까지)
            let elapsedTime = 0;
            if (this.analysisStartTime) {
                elapsedTime = Math.floor((new Date() - this.analysisStartTime) / 1000);
            } else {
                // 분석 시작 시간이 없으면 서버에서 받은 시간 사용
                elapsedTime = result.modelInfo.analysisTime || 0;
            }
            const minutes = Math.floor(elapsedTime / 60);
            const seconds = elapsedTime % 60;
            document.getElementById('modelTime').textContent = `${minutes}분 ${seconds}초`;
        }
        
        // 최종 종합 기술
        const finalSummaryContent = document.getElementById('finalSummaryContent');
        if (result.finalSummary && result.finalSummary.trim()) {
            finalSummaryContent.textContent = result.finalSummary;
        } else {
            finalSummaryContent.textContent = '종합 기술 정보가 없습니다.';
        }
        
        // 개별 Agent 시각화 HTML 파일 경로
        this.displayIndividualHtmlPaths(result.individualHtmlPaths || []);
        
        // 행동 단계
        this.displayActionSteps(result.actionSteps || []);
    }
    
    /**
     * 행동 단계 표시 (컴팩트한 수직 형식)
     * @param {Array} actionSteps - 행동 단계 배열
     */
    displayActionSteps(actionSteps) {
        const container = document.getElementById('actionStepsList');
        container.innerHTML = '';
        
        actionSteps.forEach(step => {
            // 컴팩트한 형식: "1. sit_stand: 통과"
            const stepItem = document.createElement('div');
            stepItem.className = 'text-sm py-1';
            
            const order = step.order || '';
            const name = step.name || '';
            const result = step.result === 'pass' ? '통과' : '실패';
            
            stepItem.innerHTML = `
                <span class="font-semibold text-gray-700">${order}.</span>
                <span class="text-gray-900 ml-1">${name}:</span>
                <span class="ml-2 font-semibold ${step.result === 'pass' ? 'text-green-600' : 'text-red-600'}">${result}</span>
            `;
            
            container.appendChild(stepItem);
        });
    }
    
    /**
     * 개별 Agent 시각화 HTML 파일 경로 표시
     * @param {Array} htmlPaths - HTML 파일 경로 배열
     */
    displayIndividualHtmlPaths(htmlPaths) {
        const container = document.getElementById('individualHtmlPathsList');
        const section = document.getElementById('resultIndividualHtmlPaths');
        
        if (!htmlPaths || htmlPaths.length === 0) {
            // HTML 경로가 없으면 섹션 숨기기
            if (section) {
                section.classList.add('hidden');
            }
            return;
        }
        
        // HTML 경로가 있으면 섹션 표시
        if (section) {
            section.classList.remove('hidden');
        }
        
        container.innerHTML = '';
        
        htmlPaths.forEach((htmlPath, index) => {
            const pathItem = document.createElement('div');
            pathItem.className = 'py-2 border-b border-gray-200 last:border-b-0';
            
            pathItem.innerHTML = `
                <span class="font-semibold text-gray-700">${index + 1}.</span>
                <span class="text-gray-900 ml-2 font-mono text-xs break-all">${this.escapeHtml(htmlPath)}</span>
            `;
            
            container.appendChild(pathItem);
        });
    }
    
    /**
     * 분석 정보 표시
     */
    showAnalysisInfo() {
        document.getElementById('infoDevice').textContent = this.selectedDevice || '-';
        document.getElementById('infoFile').textContent = this.uploadedFile ? this.uploadedFile.name : '-';
        
        // 에이전트 정보 표시
        const agentText = this.llmModels && this.llmModels.length > 0 
            ? this.llmModels.join(', ') 
            : '-';
        document.getElementById('infoAgent').textContent = agentText;
        
        // 분석 영역 표시
        document.getElementById('analysisArea').classList.remove('hidden');
        document.getElementById('uploadArea').classList.add('hidden');
        document.getElementById('resultArea').classList.add('hidden');
    }
    
    /**
     * 프로그레스 바 업데이트
     * @param {number} progress - 진행률 (0-100)
     * @param {string} stage - 현재 단계
     */
    updateProgressBar(progress, stage) {
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressStage = document.getElementById('progressStage');
        
        // 서버에서 받은 진행률이 더 높으면 업데이트
        if (progressFill && progressPercent) {
            const currentWidth = parseInt(progressFill.style.width) || 0;
            if (progress > currentWidth) {
                progressFill.style.width = `${progress}%`;
                progressPercent.textContent = `${progress}%`;
            }
        }
        
        // 단계 정보 업데이트 (분석 초기화 중... 제외)
        if (progressStage && stage && !stage.includes('초기화')) {
            progressStage.textContent = stage;
        }
    }
    
    /**
     * 분석 로그 초기화
     */
    clearAnalysisLogs() {
        const container = document.getElementById('logsContainer');
        container.innerHTML = '';
    }
    
    /**
     * 로그 추가 (타임스탬프 없이)
     * @param {string} message - 로그 메시지
     */
    addLog(message) {
        const container = document.getElementById('logsContainer');
        const logEntry = document.createElement('p');
        logEntry.className = 'log-entry info';
        logEntry.textContent = message;
        container.appendChild(logEntry);
        container.scrollTop = container.scrollHeight;
    }
    
    /**
     * 분석 로그 업데이트
     * @param {Array} logs - 로그 배열
     */
    updateAnalysisLogs(logs) {
        const container = document.getElementById('logsContainer');
        
        if (!logs || logs.length === 0) {
            return;
        }
        
        // 기존 로그는 유지하고 새로운 로그만 추가
        // 최근 20개 로그만 표시
        const recentLogs = logs.slice(-20);
        recentLogs.forEach(log => {
            // 이미 표시된 로그인지 확인 (간단한 중복 체크)
            const existingLogs = Array.from(container.children).map(el => el.textContent);
            if (!existingLogs.includes(this.escapeHtml(log))) {
                const logEntry = document.createElement('p');
                const logClass = log.includes('오류') || log.includes('실패') 
                    ? 'log-entry error' 
                    : log.includes('완료') || log.includes('성공')
                    ? 'log-entry success'
                    : 'log-entry info';
                logEntry.className = logClass;
                logEntry.textContent = this.escapeHtml(log);
                container.appendChild(logEntry);
            }
        });
        
        // 스크롤을 맨 아래로
        container.scrollTop = container.scrollHeight;
    }
    
    /**
     * 업로드 진행 표시
     */
    showUploadProgress() {
        const info = document.getElementById('uploadedFileInfo');
        info.classList.remove('hidden');
        document.getElementById('uploadedFileName').textContent = '업로드 중...';
        document.getElementById('uploadedFileSize').textContent = '';
    }
    
    /**
     * 업로드 성공 표시
     * @param {File} file - 업로드된 파일
     * @param {Object} metadata - 파일 메타데이터
     */
    showUploadSuccess(file, metadata) {
        const info = document.getElementById('uploadedFileInfo');
        info.classList.remove('hidden');
        document.getElementById('uploadedFileName').textContent = file.name;
        document.getElementById('uploadedFileSize').textContent = this.formatFileSize(file.size);
    }
    
    /**
     * 업로드 정보 숨기기
     */
    hideUploadInfo() {
        document.getElementById('uploadedFileInfo').classList.add('hidden');
    }
    
    /**
     * 파일 정보 표시
     * @param {File} file - 파일 객체
     */
    displayFileInfo(file) {
        const fileInfoDisplay = document.getElementById('fileInfoDisplay');
        fileInfoDisplay.classList.remove('hidden');
        
        document.getElementById('fileInfoName').textContent = file.name || '-';
        document.getElementById('fileInfoSize').textContent = this.formatFileSize(file.size);
        document.getElementById('fileInfoType').textContent = file.type || '-';
        
        // 마지막 수정 시간
        const lastModified = new Date(file.lastModified);
        const formattedDate = lastModified.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        document.getElementById('fileInfoModified').textContent = formattedDate;
    }
    
    /**
     * 비디오 스냅샷 표시
     * @param {File} file - 비디오 파일 객체
     */
    displayVideoSnapshot(file) {
        const videoSnapshotDisplay = document.getElementById('videoSnapshotDisplay');
        const videoSnapshot = document.getElementById('videoSnapshot');
        const videoSnapshotSource = document.getElementById('videoSnapshotSource');
        
        // 기존 URL 해제 (메모리 누수 방지)
        if (videoSnapshotSource.src) {
            URL.revokeObjectURL(videoSnapshotSource.src);
        }
        
        // 비디오 URL 생성
        const videoUrl = URL.createObjectURL(file);
        videoSnapshotSource.src = videoUrl;
        videoSnapshot.load();
        
        // 비디오가 로드되면 첫 프레임 표시
        videoSnapshot.addEventListener('loadedmetadata', () => {
            videoSnapshot.currentTime = 0.1; // 첫 프레임으로 이동
        }, { once: true });
        
        videoSnapshotDisplay.classList.remove('hidden');
    }
    
    /**
     * 비디오 스냅샷 숨기기
     */
    hideVideoSnapshot() {
        const videoSnapshotDisplay = document.getElementById('videoSnapshotDisplay');
        const videoSnapshot = document.getElementById('videoSnapshot');
        const videoSnapshotSource = document.getElementById('videoSnapshotSource');
        
        // URL 해제 (메모리 누수 방지)
        if (videoSnapshotSource.src) {
            URL.revokeObjectURL(videoSnapshotSource.src);
            videoSnapshotSource.src = '';
        }
        
        videoSnapshotDisplay.classList.add('hidden');
    }
    
    /**
     * 파일 정보 숨기기
     */
    hideFileInfo() {
        document.getElementById('fileInfoDisplay').classList.add('hidden');
    }
    
    /**
     * 결과 저장 (CSV)
     */
    saveResults() {
        if (!this.analysisResult) {
            this.showError('오류', '저장할 결과가 없습니다.');
            return;
        }
        
        try {
            this.csvExporter.export(
                this.analysisResult,
                this.selectedDevice,
                this.uploadedFile
            );
        } catch (error) {
            console.error('결과 저장 오류:', error);
            this.showError('저장 실패', error.message || '결과를 저장할 수 없습니다.');
        }
    }
    
    /**
     * 버튼 상태 업데이트
     */
    updateButtonStates() {
        const startBtn = document.getElementById('startAnalysisBtn');
        const saveBtn = document.getElementById('saveResultBtn');
        
        startBtn.disabled = !(this.selectedDevice && this.videoId);
        saveBtn.disabled = !this.analysisResult;
    }
    
    /**
     * 파일 검증
     * @param {File} file - 검증할 파일
     * @returns {boolean} 검증 결과
     */
    validateFile(file) {
        const validTypes = [
            'video/mp4',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska'
        ];
        const maxSize = 500 * 1024 * 1024; // 500MB
        
        if (!validTypes.includes(file.type)) {
            return false;
        }
        
        if (file.size > maxSize) {
            return false;
        }
        
        return true;
    }
    
    /**
     * 서버 연결 확인
     */
    async checkServerConnection() {
        try {
            await this.api.checkServerHealth();
            console.log('서버 연결 성공');
        } catch (error) {
            console.warn('서버 연결 실패:', error);
            // 서버가 아직 시작되지 않았을 수 있으므로 에러를 표시하지 않음
        }
    }
    
    /**
     * 네트워크 불안정 경고 표시 (비침습적 배너)
     * @param {string} message - 경고 메시지
     */
    showNetworkWarning(message) {
        const warningEl = document.getElementById('networkWarning');
        const textEl = document.getElementById('networkWarningText');
        if (warningEl && textEl) {
            textEl.textContent = message;
            warningEl.classList.remove('hidden');
        }
    }

    /**
     * 네트워크 경고 숨기기
     */
    hideNetworkWarning() {
        const warningEl = document.getElementById('networkWarning');
        if (warningEl) {
            warningEl.classList.add('hidden');
        }
    }

    /**
     * 에러 표시
     * @param {string} title - 에러 제목
     * @param {string} message - 에러 메시지
     */
    showError(title, message) {
        document.getElementById('errorTitle').textContent = title;
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorModal').classList.remove('hidden');
    }
    
    /**
     * HTML 이스케이프
     * @param {string} text - 이스케이프할 텍스트
     * @returns {string} 이스케이프된 텍스트
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

// DOM이 로드되면 애플리케이션 시작
document.addEventListener('DOMContentLoaded', () => {
    new InhalerAnalysisApp();
});

