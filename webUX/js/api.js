// API Client Module
// 백엔드 API 서버와 통신하는 모듈

const API_BASE_URL = 'http://localhost:8000/api';

class APIClient {
    /**
     * 서버 상태 확인
     * @returns {Promise<Object>} 서버 정보
     */
    async checkServerHealth() {
        try {
            const response = await fetch('http://localhost:8000/');
            if (!response.ok) {
                throw new Error(`서버 응답 오류: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            throw new Error(`서버 연결 실패: ${error.message}`);
        }
    }

    /**
     * 비디오 파일 업로드
     * @param {File} file - 업로드할 비디오 파일
     * @returns {Promise<Object>} 업로드 응답 (videoId, metadata)
     */
    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/video/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text().catch(() => '');
                let errorMessage = '비디오 업로드에 실패했습니다.';
                
                if (response.status === 404) {
                    errorMessage = 'API 서버를 찾을 수 없습니다. 서버 주소를 확인하세요.';
                } else if (response.status === 500) {
                    errorMessage = '서버 오류가 발생했습니다. 서버 로그를 확인하세요.';
                } else if (errorText) {
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorMessage = errorJson.detail || errorMessage;
                    } catch {
                        errorMessage = errorText || errorMessage;
                    }
                }
                
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            if (error.message) {
                throw error;
            }
            throw new Error(`업로드 중 오류 발생: ${error.message}`);
        }
    }

    /**
     * 분석 시작
     * @param {string} videoId - 업로드된 비디오 ID
     * @param {string} deviceType - 디바이스 타입
     * @param {boolean} saveIndividualReport - 개별 리포트 저장 여부
     * @returns {Promise<Object>} 분석 시작 응답 (analysisId, estimatedTime)
     */
    async startAnalysis(videoId, deviceType, saveIndividualReport = true) {
        try {
            const response = await fetch(`${API_BASE_URL}/analysis/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    videoId,
                    deviceType,
                    saveIndividualReport
                })
            });

            if (!response.ok) {
                const errorText = await response.text().catch(() => '');
                let errorMessage = '분석 시작에 실패했습니다.';
                
                if (errorText) {
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorMessage = errorJson.detail || errorMessage;
                    } catch {
                        errorMessage = errorText || errorMessage;
                    }
                }
                
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            if (error.message) {
                throw error;
            }
            throw new Error(`분석 시작 중 오류 발생: ${error.message}`);
        }
    }

    /**
     * 분석 상태 조회
     * @param {string} analysisId - 분석 ID
     * @returns {Promise<Object>} 분석 상태 (status, progress, current_stage, logs, error)
     */
    async getAnalysisStatus(analysisId) {
        try {
            const response = await fetch(`${API_BASE_URL}/analysis/status/${analysisId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('분석 작업을 찾을 수 없습니다.');
                }
                throw new Error(`상태 조회 실패: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.message) {
                throw error;
            }
            throw new Error(`상태 조회 중 오류 발생: ${error.message}`);
        }
    }

    /**
     * 분석 결과 조회
     * @param {string} analysisId - 분석 ID
     * @returns {Promise<Object>} 분석 결과
     */
    async getAnalysisResult(analysisId) {
        try {
            const response = await fetch(`${API_BASE_URL}/analysis/result/${analysisId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('분석 작업을 찾을 수 없습니다.');
                } else if (response.status === 400) {
                    throw new Error('분석이 아직 완료되지 않았습니다.');
                } else if (response.status === 500) {
                    throw new Error('분석 결과가 없습니다.');
                }
                throw new Error(`결과 조회 실패: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.message) {
                throw error;
            }
            throw new Error(`결과 조회 중 오류 발생: ${error.message}`);
        }
    }

    /**
     * 결과 다운로드 (JSON)
     * @param {string} analysisId - 분석 ID
     * @param {string} format - 다운로드 형식 (json)
     * @returns {Promise<Blob>} 다운로드 파일
     */
    async downloadResult(analysisId, format = 'json') {
        try {
            const response = await fetch(`${API_BASE_URL}/analysis/download/${analysisId}?format=${format}`);

            if (!response.ok) {
                throw new Error('결과 다운로드에 실패했습니다.');
            }

            return await response.blob();
        } catch (error) {
            if (error.message) {
                throw error;
            }
            throw new Error(`다운로드 중 오류 발생: ${error.message}`);
        }
    }

    /**
     * 서버 설정 정보 조회
     * @returns {Promise<Object>} 설정 정보 (llmModels, version)
     */
    async getConfig() {
        try {
            const response = await fetch(`${API_BASE_URL}/config`);
            if (!response.ok) {
                throw new Error(`설정 조회 실패: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            throw new Error(`설정 조회 중 오류 발생: ${error.message}`);
        }
    }
}

// Export for use in other modules
export default APIClient;

