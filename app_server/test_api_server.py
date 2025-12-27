#!/usr/bin/env python
# coding: utf-8

"""
API 서버 완전 분석 테스트
app_main.py의 설정을 기반으로 전체 분석 플로우를 테스트하고 최종 결과를 검증합니다.
"""

import requests
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

TEST_CONFIG = {
    "video_path": "/workspaces/AI_inhaler/app_server/test_clip.mp4",
    "device_type": "pMDI_type2",
    "save_individual_report": True
}

BASE_URL = "http://localhost:8000/api"
MAX_WAIT_TIME = 1800  # 최대 30분 대기
POLL_INTERVAL = 5  # 5초마다 상태 확인


class APIAnalysisTester:
    """API 서버 분석 테스트 클래스"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.video_id: Optional[str] = None
        self.analysis_id: Optional[str] = None
        self.final_result: Optional[Dict[str, Any]] = None
        
    def test_server_health(self) -> bool:
        """서버 상태 확인"""
        print("=" * 80)
        print("1. 서버 상태 확인")
        print("=" * 80)
        try:
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ 서버 실행 중: {data.get('message')} (v{data.get('version')})")
                return True
            else:
                print(f"✗ 서버 응답 오류: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 서버 연결 실패: {e}")
            print()
            print("해결 방법:")
            print("  1. 서버를 시작하세요:")
            print("     cd app_server")
            print("     python api_server.py")
            print()
            print("  2. 또는 백그라운드로 실행:")
            print("     cd app_server")
            print("     python api_server.py > /tmp/api_server.log 2>&1 &")
            print()
            print("  3. 서버가 실행 중인지 확인:")
            print("     curl http://localhost:8000/")
            return False
    
    def test_config(self) -> bool:
        """서버 설정 정보 조회 테스트"""
        print("\n" + "=" * 80)
        print("2. 서버 설정 정보 조회")
        print("=" * 80)
        try:
            response = requests.get(f"{self.base_url}/config", timeout=5)
            if response.status_code == 200:
                data = response.json()
                llm_models = data.get('llmModels', [])
                version = data.get('version', 'N/A')
                
                print(f"✓ 설정 정보 조회 성공")
                print(f"  버전: {version}")
                print(f"  LLM 모델: {llm_models}")
                
                # 검증: llmModels가 리스트이고 비어있지 않은지 확인
                if not isinstance(llm_models, list):
                    print(f"✗ LLM 모델 형식 오류: 리스트가 아닙니다.")
                    return False
                
                if len(llm_models) == 0:
                    print(f"✗ LLM 모델이 비어있습니다.")
                    return False
                
                print(f"✓ LLM 모델 검증 통과 ({len(llm_models)}개 모델)")
                return True
            else:
                print(f"✗ 설정 조회 실패: HTTP {response.status_code}")
                print(f"  응답: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 설정 조회 중 오류 발생: {e}")
            return False
    
    def test_video_upload(self, video_path: str) -> bool:
        """비디오 업로드 테스트"""
        print("\n" + "=" * 80)
        print("3. 비디오 업로드")
        print("=" * 80)
        
        if not Path(video_path).exists():
            print(f"✗ 비디오 파일을 찾을 수 없습니다: {video_path}")
            return False
        
        print(f"업로드할 파일: {Path(video_path).name}")
        print(f"파일 크기: {Path(video_path).stat().st_size / (1024*1024):.2f} MB")
        
        try:
            with open(video_path, 'rb') as f:
                files = {'file': (Path(video_path).name, f, 'video/quicktime')}
                response = requests.post(
                    f"{self.base_url}/video/upload",
                    files=files,
                    timeout=300  # 5분 타임아웃
                )
            
            if response.status_code == 200:
                data = response.json()
                self.video_id = data.get('videoId')
                print(f"✓ 비디오 업로드 성공")
                print(f"  Video ID: {self.video_id}")
                print(f"  파일명: {data.get('metadata', {}).get('fileName', 'N/A')}")
                print(f"  파일 크기: {data.get('metadata', {}).get('size', 0) / (1024*1024):.2f} MB")
                return True
            else:
                print(f"✗ 업로드 실패: HTTP {response.status_code}")
                print(f"  응답: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 업로드 중 오류 발생: {e}")
            return False
    
    def test_start_analysis(self, device_type: str, save_individual_report: bool) -> bool:
        """분석 시작 테스트"""
        print("\n" + "=" * 80)
        print("4. 분석 시작")
        print("=" * 80)
        
        if not self.video_id:
            print("✗ 비디오 ID가 없습니다. 먼저 업로드를 완료하세요.")
            return False
        
        # llmModels는 요청에 포함하지 않음 (api_server.py에서 FIXED_LLM_MODELS 사용)
        payload = {
            "videoId": self.video_id,
            "deviceType": device_type,
            "saveIndividualReport": save_individual_report
        }
        
        print(f"요청 파라미터:")
        print(f"  - Video ID: {self.video_id}")
        print(f"  - Device Type: {device_type}")
        print(f"  - Save Individual Report: {save_individual_report}")
        
        try:
            response = requests.post(
                f"{self.base_url}/analysis/start",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.analysis_id = data.get('analysisId')
                estimated_time = data.get('estimatedTime', 0)
                print(f"✓ 분석 시작 성공")
                print(f"  Analysis ID: {self.analysis_id}")
                print(f"  예상 소요 시간: {estimated_time}초 ({estimated_time/60:.1f}분)")
                return True
            else:
                print(f"✗ 분석 시작 실패: HTTP {response.status_code}")
                print(f"  응답: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 분석 시작 중 오류 발생: {e}")
            return False
    
    def monitor_analysis(self, max_wait: int = MAX_WAIT_TIME, poll_interval: int = POLL_INTERVAL) -> bool:
        """분석 진행 상태 모니터링"""
        print("\n" + "=" * 80)
        print("5. 분석 진행 상태 모니터링")
        print("=" * 80)
        print(f"최대 대기 시간: {max_wait}초 ({max_wait/60:.1f}분)")
        print(f"상태 확인 간격: {poll_interval}초")
        print()
        
        if not self.analysis_id:
            print("✗ Analysis ID가 없습니다.")
            return False
        
        start_time = time.time()
        last_progress = -1
        last_stage = ""
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                print(f"\n⚠ 최대 대기 시간({max_wait}초)을 초과했습니다.")
                return False
            
            try:
                response = requests.get(
                    f"{self.base_url}/analysis/status/{self.analysis_id}",
                    timeout=5
                )
                
                if response.status_code != 200:
                    print(f"\n✗ 상태 조회 실패: HTTP {response.status_code}")
                    return False
                
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 0)
                current_stage = data.get('current_stage', '')
                logs = data.get('logs', [])
                error = data.get('error')
                
                # 진행률이나 단계가 변경된 경우 출력
                if progress != last_progress or current_stage != last_stage:
                    elapsed_min = int(elapsed // 60)
                    elapsed_sec = int(elapsed % 60)
                    print(f"[{elapsed_min:02d}:{elapsed_sec:02d}] 상태: {status:12s} | 진행률: {progress:3d}% | {current_stage}")
                    last_progress = progress
                    last_stage = current_stage
                
                # 최근 로그 출력 (새로운 로그만)
                if logs:
                    for log in logs[-3:]:  # 최근 3개 로그
                        if log not in getattr(self, '_printed_logs', []):
                            print(f"  📝 {log}")
                            if not hasattr(self, '_printed_logs'):
                                self._printed_logs = []
                            self._printed_logs.append(log)
                
                if status == "completed":
                    print(f"\n✓ 분석 완료! (소요 시간: {int(elapsed)}초)")
                    return True
                elif status == "error":
                    print(f"\n✗ 분석 오류 발생")
                    if error:
                        print(f"  오류 메시지: {error}")
                    return False
                
            except Exception as e:
                print(f"\n⚠ 상태 조회 중 오류: {e}")
                # 오류가 발생해도 계속 시도
            
            time.sleep(poll_interval)
    
    def test_get_result(self) -> bool:
        """분석 결과 조회 및 검증"""
        print("\n" + "=" * 80)
        print("6. 분석 결과 조회 및 검증")
        print("=" * 80)
        
        if not self.analysis_id:
            print("✗ Analysis ID가 없습니다.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/analysis/result/{self.analysis_id}",
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"✗ 결과 조회 실패: HTTP {response.status_code}")
                print(f"  응답: {response.text}")
                return False
            
            self.final_result = response.json()
            print("✓ 결과 조회 성공")
            return True
            
        except Exception as e:
            print(f"✗ 결과 조회 중 오류 발생: {e}")
            return False
    
    def validate_result(self) -> bool:
        """결과 데이터 검증"""
        print("\n" + "=" * 80)
        print("7. 결과 데이터 검증")
        print("=" * 80)
        
        if not self.final_result:
            print("✗ 결과 데이터가 없습니다.")
            return False
        
        print("필수 필드 검증:")
        required_fields = [
            'status', 'deviceType', 'videoInfo', 'actionSteps', 
            'summary', 'modelInfo', 'errors', 'finalSummary'
        ]
        
        all_valid = True
        for field in required_fields:
            if field in self.final_result:
                print(f"  ✓ {field}: 존재")
            else:
                print(f"  ✗ {field}: 없음")
                all_valid = False
        
        # 상세 검증
        print("\n상세 데이터 검증:")
        
        # 1. 비디오 정보
        video_info = self.final_result.get('videoInfo', {})
        if video_info:
            print(f"  비디오 정보:")
            print(f"    - 파일명: {video_info.get('fileName', 'N/A')}")
            print(f"    - 재생시간: {video_info.get('duration', 0)}초")
            print(f"    - 총 프레임: {video_info.get('frameCount', 'N/A')}")
            print(f"    - 해상도: {video_info.get('resolution', 'N/A')}")
        
        # 2. 요약 정보
        summary = self.final_result.get('summary', {})
        if summary:
            print(f"  요약 정보:")
            print(f"    - 총 단계: {summary.get('totalSteps', 0)}")
            print(f"    - 통과: {summary.get('passedSteps', 0)}")
            print(f"    - 실패: {summary.get('failedSteps', 0)}")
            print(f"    - 점수: {summary.get('score', 0):.1f}%")
        
        # 3. 행동 단계
        action_steps = self.final_result.get('actionSteps', [])
        print(f"  행동 단계: {len(action_steps)}개")
        if action_steps:
            print(f"    첫 3개 단계:")
            for step in action_steps[:3]:
                print(f"      - {step.get('order')}. {step.get('name')}: {step.get('result')}")
        
        # 4. 최종 종합 기술
        final_summary = self.final_result.get('finalSummary', '')
        if final_summary:
            print(f"  최종 종합 기술: 있음 ({len(final_summary)}자)")
            # 첫 100자만 출력
            preview = final_summary[:100].replace('\n', ' ')
            print(f"    미리보기: {preview}...")
        else:
            print(f"  최종 종합 기술: 없음")
        
        # 5. 모델 정보
        model_info = self.final_result.get('modelInfo', {})
        if model_info:
            models = model_info.get('models', [])
            analysis_time = model_info.get('analysisTime', 0)
            print(f"  모델 정보:")
            print(f"    - 사용 모델: {', '.join(models)}")
            print(f"    - 분석 시간: {analysis_time}초")
        
        return all_valid
    
    def save_result(self, output_file: str = "test_analysis_result.json") -> bool:
        """결과를 파일로 저장"""
        if not self.final_result:
            return False
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.final_result, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 결과 저장 완료: {output_file}")
            return True
        except Exception as e:
            print(f"\n✗ 결과 저장 실패: {e}")
            return False
    
    def compare_with_main_app_output(self) -> bool:
        """app_main.py의 print_analysis_summary 출력과 비교"""
        print("\n" + "=" * 80)
        print("8. app_main.py 출력 형식과 비교")
        print("=" * 80)
        
        if not self.final_result:
            print("✗ 결과 데이터가 없습니다.")
            return False
        
        print("print_analysis_summary() 출력 내용과 비교:")
        print()
        
        # 1. 비디오 정보 비교
        video_info = self.final_result.get('videoInfo', {})
        print("[비디오 정보]")
        print(f"  파일명: {video_info.get('fileName', 'N/A')}")
        print(f"  재생시간: {video_info.get('duration', 0)}초")
        print(f"  총 프레임: {video_info.get('frameCount', 'N/A')}")
        print(f"  해상도: {video_info.get('resolution', 'N/A')}")
        print()
        
        # 2. 최종 판단 결과 (action_order 순서대로)
        action_steps = self.final_result.get('actionSteps', [])
        print("[최종 판단 결과]")
        for step in action_steps:
            result_str = "SUCCESS" if step.get('result') == 'pass' else "FAIL"
            score = step.get('score', [0])[0] if step.get('score') else 0
            print(f"  {step.get('name')}: {result_str} ({score})")
        print()
        
        # 3. 최종 종합 기술
        final_summary = self.final_result.get('finalSummary', '')
        print("[최종 종합 기술]")
        if final_summary:
            for line in final_summary.split('\n'):
                print(f"  {line}")
        else:
            print("  종합 기술 정보가 없습니다.")
        print()
        
        # 4. 개별 Agent 시각화 HTML 파일 경로
        individual_html_paths = self.final_result.get('individualHtmlPaths', [])
        if individual_html_paths:
            print("[개별 Agent 시각화 HTML 파일]")
            for idx, html_path in enumerate(individual_html_paths, 1):
                print(f"  {idx}. {html_path}")
            print()
        
        return True
    
    def run_full_test(self, config: Dict[str, Any]) -> bool:
        """전체 테스트 실행"""
        print("\n" + "=" * 80)
        print("API 서버 완전 분석 테스트 시작")
        print("=" * 80)
        print(f"테스트 설정:")
        print(f"  - 비디오: {Path(config['video_path']).name}")
        print(f"  - 디바이스 타입: {config['device_type']}")
        print(f"  - 개별 리포트 저장: {config['save_individual_report']}")
        print()
        
        # 1. 서버 상태 확인
        if not self.test_server_health():
            return False
        
        # 2. 서버 설정 정보 조회
        if not self.test_config():
            return False
        
        # 3. 비디오 업로드
        if not self.test_video_upload(config['video_path']):
            return False
        
        # 4. 분석 시작
        if not self.test_start_analysis(
            config['device_type'],
            config['save_individual_report']
        ):
            return False
        
        # 5. 분석 모니터링
        if not self.monitor_analysis():
            return False
        
        # 6. 결과 조회
        if not self.test_get_result():
            return False
        
        # 7. 결과 검증
        if not self.validate_result():
            return False
        
        # 8. app_main.py 출력 형식과 비교
        self.compare_with_main_app_output()
        
        # 9. 결과 저장
        self.save_result()
        
        print("\n" + "=" * 80)
        print("✓ 모든 테스트 완료!")
        print("=" * 80)
        
        return True


def main():
    """메인 함수"""
    tester = APIAnalysisTester()
    
    try:
        success = tester.run_full_test(TEST_CONFIG)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ 테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 테스트 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

