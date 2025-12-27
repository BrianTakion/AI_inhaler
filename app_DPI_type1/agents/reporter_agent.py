#!/usr/bin/env python
# coding: utf-8

"""
Reporter Agent
분석 결과를 취합하고 시각화합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv
from .state import VideoAnalysisState

# app_server 모듈 경로 추가 (상위 2단계 디렉토리)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..'))
from app_server import class_MultimodalLLM_QA_251107 as mLLM

# .env 파일 로드 (app_server 디렉토리)
app_server_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app_server')
env_path = os.path.join(app_server_dir, ".env")
load_dotenv(dotenv_path=env_path)

# class_PromptBank_DPI_type1 import
import class_PromptBank_DPI_type1 as PB


class ReporterAgent:
    """
    리포팅 전담 Agent
    - 결과 취합
    - Plotly 그래프 생성
    - JSON/CSV 리포트 출력
    """
    
    # Reference 순서 정의 (밑에서 위로)
    REFERENCE_ORDER = ['inhalerIN', 'faceONinhaler', 'inhalerOUT']
    
    # 액션 순서 정의 (밑에서 위로)
    ACTION_ORDER = [
        'sit_stand', 'load_dose', 'inspect_mouthpiece', 
        'hold_inhaler', 
        'exhale_before', 'seal_lips', 'inhale_deeply',
        'remove_inhaler', 'hold_breath', 'exhale_after'
    ]
    
    # Action Key별 취합 규칙 정의
    ACTION_AGGREGATION_RULES = {
        'sit_stand': 'majority',        # 과반수가 True일 때만 True
        'load_dose': 'majority',        # 과반수가 True일 때만 True
        'inspect_mouthpiece': 'all',    # 모두 True일 때만 True
        'hold_inhaler': 'majority',     # 과반수가 True일 때만 True
        'exhale_before': 'all',         # 모두 True일 때만 True
        'seal_lips': 'majority',        # 과반수가 True일 때만 True
        'inhale_deeply': 'majority',    # 과반수가 True일 때만 True
        'remove_inhaler': 'any',        # 한 개라도 True일 때면 True
        'hold_breath': 'any',           # 한 개라도 True일 때면 True
        'exhale_after': 'majority'      # 과반수가 True일 때만 True
    }
    
    def __init__(self):
        self.name = "ReporterAgent"
    
    def process(self, state: VideoAnalysisState) -> VideoAnalysisState:
        """
        최종 리포트 생성 (개별 agent 판정 → 복수 agent 판정)
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        try:
            state["agent_logs"].append({
                "agent": self.name,
                "action": "start_reporting",
                "message": "리포트 생성 시작 (개별 agent 판정 → 복수 agent 판정)"
            })
            
            model_results = state.get("model_results", {})
            if not model_results:
                raise ValueError("모델 결과가 없습니다.")
            
            num_models = len(model_results)
            print(f"\n[{self.name}] {num_models}개 모델 결과 처리 중...")
            
            video_info = state["video_info"]
            save_individual_report_flag = state.get("save_individual_report", False)
            timestamp_suffix = datetime.now().strftime("%m%d_%H%M")
            
            # 1. 각 agent에 대해 개별 판정 규칙 적용
            individual_agent_decisions = {}
            for model_id, result in model_results.items():
                reference_times = result.get("reference_times", {})
                promptbank_data = result.get("promptbank_data", {})
                
                # 개별 agent 판정 규칙 적용
                decisions = self._apply_individual_agent_rule(reference_times, promptbank_data)
                individual_agent_decisions[model_id] = decisions
                
                print(f"[{self.name}] {model_id} 개별 판정 완료")
                
                # 2. 개별 agent 시각화 생성 (save_individual_report_flag가 True일 때만)
                if save_individual_report_flag:
                    visualization_fig = self._create_individual_agent_visualization(
                        model_id=model_id,
                        model_name=model_id,
                        reference_times=reference_times,
                        promptbank_data=promptbank_data,
                        video_info=video_info,
                        individual_decisions=decisions
                    )
                    
                    if visualization_fig:
                        # HTML 파일로 저장
                        html_filename = f"visualization_{model_id}_{video_info['video_name']}_{timestamp_suffix}.html"
                        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), html_filename)
                        visualization_fig.write_html(html_path)
                        
                        print(f"[{self.name}] {model_id} 시각화 HTML 파일 저장됨:")
                        print(f"  파일 경로: {html_path}")
            
            # 3. 복수 agent 판정 규칙 적용
            final_decisions = self._apply_multi_agent_rule(individual_agent_decisions)
            print(f"[{self.name}] 복수 agent 판정 완료")
            
            # 4. 최종 리포트 생성
            final_report = self._create_final_report(
                state, individual_agent_decisions, final_decisions
            )
            state["final_report"] = final_report
            
            # individual_agent_decisions를 state에 저장 (참고용)
            state["individual_agent_decisions"] = individual_agent_decisions
            
            state["status"] = "completed"
            
            state["agent_logs"].append({
                "agent": self.name,
                "action": "reporting_complete",
                "message": "리포트 생성 완료"
            })
            
            print(f"\n[{self.name}] 최종 리포트 생성 완료")
            
        except Exception as e:
            error_msg = f"[{self.name}] 리포트 생성 중 오류: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "error"
            print(error_msg)
            import traceback
            traceback.print_exc()
        
        return state
    
    def _apply_aggregation_rule(self, scores: list, rule: str) -> int:
        """
        취합 규칙에 따라 최종 score 결정
        
        Args:
            scores: 각 모델의 score 리스트 (0 또는 1)
            rule: 'majority', 'all', 'any' 중 하나
        
        Returns:
            0 또는 1
        """
        if not scores:
            return 0
        
        true_count = sum(1 for s in scores if s >= 0.5)  # True인 개수
        total_count = len(scores)
        
        if rule == 'majority':
            # 과반수: True 개수 >= 전체의 50%
            return 1 if true_count >= total_count / 2 else 0
        elif rule == 'all':
            # 모두: 모든 모델이 True
            return 1 if true_count == total_count else 0
        elif rule == 'any':
            # 한 개라도: 하나라도 True면 True
            return 1 if true_count > 0 else 0
        else:
            # 기본값: 과반수 규칙
            return 1 if true_count >= total_count / 2 else 0
    
    def _apply_individual_agent_rule(self, reference_times: dict, promptbank_data: dict) -> dict:
        """
        개별 agent의 시계열 데이터에 구간별 판정 규칙 적용
        
        Args:
            reference_times: 개별 agent의 reference_times
            promptbank_data: 개별 agent의 promptbank_data
            
        Returns:
            {action_key: 0 or 1} - 각 action_key별 단일 TRUE/FALSE 값
        """
        decisions = {}
        
        # 1. 기준 시간 추출 (없으면 -1)
        T_in = reference_times.get('inhalerIN', -1)
        T_face = reference_times.get('faceONinhaler', -1)
        T_out = reference_times.get('inhalerOUT', -1)
        
        # 데이터 가져오기
        actions_data = promptbank_data.get("check_action_step_DPI_type1", {})
        
        # 모든 키에 대해 기본값 0으로 초기화
        all_keys = set(self.ACTION_ORDER) | set(actions_data.keys())
        for key in all_keys:
            decisions[key] = 0

        # Helper: 특정 Action의 Time, Score 리스트 가져오기
        def get_time_scores(action_key):
            if action_key not in actions_data:
                return [], []
            data = actions_data[action_key]
            times = data.get('time', [])
            scores = data.get('score', [])
            return times, scores

        # Helper: 특정 구간 내의 데이터 필터링
        def filter_in_range(times, scores, start_t, end_t):
            filtered_scores = []
            filtered_times = []
            for t, s in zip(times, scores):
                if start_t <= t <= end_t:
                    filtered_scores.append(s)
                    filtered_times.append(t)
            return filtered_times, filtered_scores

        # Helper: T_face 시점과 그 직전 시점 데이터 확인
        def check_at_point_and_prev(action_key, target_time, condition='OR'):
            times, scores = get_time_scores(action_key)
            if not times or target_time < 0:
                return 0
            
            # target_time 이하인 인덱스들 찾기
            valid_indices = [i for i, t in enumerate(times) if t <= target_time]
            if not valid_indices:
                return 0
            
            last_idx = valid_indices[-1] # target_time 직전(포함) 가장 늦은 시간
            
            target_scores = [scores[last_idx]]
            if last_idx > 0:
                target_scores.append(scores[last_idx - 1])
            
            bool_scores = [s >= 0.5 for s in target_scores]
            
            if condition == 'AND':
                # 데이터가 하나만 있으면 하나만으로 판단, 두 개면 둘 다 True여야 함
                return 1 if all(bool_scores) else 0
            else: # OR
                return 1 if any(bool_scores) else 0

        # Helper: T_face 시점과 그 직후 시점 데이터 확인
        def check_at_point_and_next(action_key, target_time, condition='OR'):
            times, scores = get_time_scores(action_key)
            if not times or target_time < 0:
                return 0
            
            # target_time 이상인 인덱스들 찾기
            valid_indices = [i for i, t in enumerate(times) if t >= target_time]
            if not valid_indices:
                return 0
            
            first_idx = valid_indices[0] # target_time 직후(포함) 가장 빠른 시간
            
            target_scores = [scores[first_idx]]
            if first_idx < len(scores) - 1:
                target_scores.append(scores[first_idx + 1])
            
            bool_scores = [s >= 0.5 for s in target_scores]
            
            if condition == 'AND':
                # 데이터가 하나만 있으면 하나만으로 판단, 두 개면 둘 다 True여야 함
                return 1 if all(bool_scores) else 0
            else: # OR
                return 1 if any(bool_scores) else 0

        # --- 판단 로직 적용 ---
        
        # 1. T_face 시점 및 직전 시점
        if T_face >= 0:
            decisions['sit_stand'] = check_at_point_and_prev('sit_stand', T_face, 'AND')
            decisions['inspect_mouthpiece'] = check_at_point_and_prev('inspect_mouthpiece', T_face, 'OR')
            decisions['hold_inhaler'] = check_at_point_and_prev('hold_inhaler', T_face, 'OR')
        
        # 2. T_in ~ T_face 구간
        if T_in >= 0 and T_face >= 0 and T_in <= T_face:
            for key in ['load_dose']:
                times, scores = get_time_scores(key)
                _, f_scores = filter_in_range(times, scores, T_in, T_face)
                if any(s >= 0.5 for s in f_scores):
                    decisions[key] = 1
        
        # 3. T_face ~ T_out 구간
        if T_face >= 0 and T_out >= 0 and T_face <= T_out:
            # T_face ~ T_out 구간
            times, scores = get_time_scores('seal_lips')
            _, f_scores = filter_in_range(times, scores, T_face, T_out)
            if any(s >= 0.5 for s in f_scores):
                decisions['seal_lips'] = 1
            
            # 단순 존재 여부 (구간 내 하나라도 score ≥ 0.5이면 성공)
            # remove_inhaler, exhale_after: T_face ~ T_out 구간
            for key in ['remove_inhaler', 'exhale_after']:
                times, scores = get_time_scores(key)
                _, f_scores = filter_in_range(times, scores, T_face, T_out)
                if any(s >= 0.5 for s in f_scores):
                    decisions[key] = 1
        
        # exhale_before: T_in ~ T_out 구간
        if T_in >= 0 and T_out >= 0 and T_in <= T_out:
            times, scores = get_time_scores('exhale_before')
            _, f_scores = filter_in_range(times, scores, T_in, T_out)
            if any(s >= 0.5 for s in f_scores):
                decisions['exhale_before'] = 1
            
            # inhale_deeply: T_face ~ T_out 구간에서 (seal_lips and inhale_deeply)
            id_times, id_scores = get_time_scores('inhale_deeply')
            sl_times, sl_scores = get_time_scores('seal_lips')
            
            found_deeply = False
            # T_face ~ T_out 구간 내에서 inhale_deeply와 seal_lips가 모두 TRUE인 시점 확인
            for t_id, s_id in zip(id_times, id_scores):
                if T_face <= t_id <= T_out and s_id >= 0.5:
                    # seal_lips도 같은 시점(또는 매우 가까운 시점, 0.2초 오차)에서 True인지 확인
                    for t_sl, s_sl in zip(sl_times, sl_scores):
                        if T_face <= t_sl <= T_out and s_sl >= 0.5:
                                if abs(t_sl - t_id) < 0.2:
                                    found_deeply = True
                                    break
                        if found_deeply:
                            break
            
            if found_deeply:
                decisions['inhale_deeply'] = 1

            # hold_breath: 2sec 연속
            hb_times, hb_scores = get_time_scores('hold_breath')
            f_times, f_scores = filter_in_range(hb_times, hb_scores, T_face, T_out)
            
            consecutive_start = -1
            max_duration = 0
            for t, s in zip(f_times, f_scores):
                if s >= 0.5:
                    if consecutive_start < 0:
                        consecutive_start = t
                    duration = t - consecutive_start
                    if duration > max_duration:
                        max_duration = duration
                else:
                    consecutive_start = -1
            
            if max_duration >= 2.0:
                decisions['hold_breath'] = 1
                
        return decisions
    
    def _apply_multi_agent_rule(self, individual_agent_decisions: dict) -> dict:
        """
        개별 agent 판정 결과에 복수 agent 판정 규칙 적용
        
        Args:
            individual_agent_decisions: {model_id: {action_key: 0 or 1}}
            
        Returns:
            {action_key: 0 or 1} - 최종 판정 결과
        """
        final_decisions = {}
        
        # 모든 action_key 수집
        all_action_keys = set()
        for model_id, decisions in individual_agent_decisions.items():
            all_action_keys.update(decisions.keys())
        
        # 각 action_key에 대해 복수 agent 판정 규칙 적용
        for action_key in all_action_keys:
            # 모든 agent의 판정 결과 수집
            agent_scores = []
            for model_id, decisions in individual_agent_decisions.items():
                if action_key in decisions:
                    agent_scores.append(decisions[action_key])
            
            # 해당 action_key의 취합 규칙 가져오기
            rule = self.ACTION_AGGREGATION_RULES.get(action_key, 'majority')
            
            # 복수 agent 판정 규칙 적용
            final_decisions[action_key] = self._apply_aggregation_rule(agent_scores, rule)
        
        return final_decisions
    
    def _evaluate_decisions(self, reference_times_avg: dict, promptbank_data_avg: dict) -> dict:
        """
        Reference Time을 기준으로 각 Action Step의 성공 여부(Decision)를 최종 판단
        (레거시 메서드 - 호환성을 위해 유지하되 사용하지 않음)
        """
        decisions = {}
        
        # 1. 기준 시간 추출 (없으면 -1)
        T_in = reference_times_avg.get('inhalerIN', -1)
        T_face = reference_times_avg.get('faceONinhaler', -1)
        T_out = reference_times_avg.get('inhalerOUT', -1)
        
        # 데이터 가져오기
        actions_data = promptbank_data_avg.get("check_action_step_DPI_type1", {})
    
    def _generate_final_summary(self, action_decisions: dict, action_analysis: dict) -> str:
        """
        FAIL 항목에 대한 종합 기술 생성 (OpenAI GPT-4.1 사용)
        
        Args:
            action_decisions: 최종 판단 결과
            action_analysis: 행동 분석 상세 정보
            
        Returns:
            종합 기술 문자열 (실패 시 빈 문자열 또는 기본 메시지)
        """
        try:
            # FAIL 항목 확인
            fail_actions = [key for key, val in action_decisions.items() if val == 0]
            
            if not fail_actions:
                return "모든 항목이 성공적으로 수행되었습니다."
            
            # 프롬프트 생성
            system_prompt, user_prompt = PB.PromptBank.get_fail_summary_prompt(
                action_decisions, action_analysis
            )
            
            if system_prompt is None or user_prompt is None:
                return "종합 기술 생성 실패: 프롬프트 생성 오류"
            
            # 환경 변수에서 OpenAI API 키 직접 읽기
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return "종합 기술 생성 실패: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다."
            
            # OpenAI GPT-4.1 호출
            print(f"\n[{self.name}] FAIL 항목 종합 기술 생성 중 (GPT-4.1 사용)...")
            mllm = mLLM.multimodalLLM(llm_name="gpt-4.1", api_key=openai_api_key)
            summary = mllm.query_answer_chatGPT(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_path=None,
                image_array=None,
                max_output_tokens=2000,
                temperature=0.3
            )
            
            if summary and len(summary.strip()) > 0:
                print(f"[{self.name}] 종합 기술 생성 완료")
                return summary.strip()
            else:
                return "종합 기술 생성 실패: 응답이 비어있습니다."
                
        except Exception as e:
            error_msg = f"종합 기술 생성 중 오류: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            import traceback
            traceback.print_exc()
            return f"종합 기술 생성 실패: {error_msg}"
    
    def _create_final_report(self, state: VideoAnalysisState, 
                            individual_agent_decisions: dict, 
                            final_decisions: dict) -> dict:
        """
        최종 리포트 생성
        
        Args:
            state: 현재 상태
            individual_agent_decisions: {model_id: {action_key: 0 or 1}}
            final_decisions: {action_key: 0 or 1} - 최종 판정 결과
        """
        video_info = state["video_info"]
        model_results = state.get("model_results", {})
        
        # 모든 agent의 시계열 데이터를 통합하여 action_analysis 생성
        action_analysis = {}
        all_action_keys = set()
        
        # 모든 action_key 수집
        for model_id, result in model_results.items():
            promptbank_data = result.get("promptbank_data", {})
            check_action = promptbank_data.get("check_action_step_DPI_type1", {})
            all_action_keys.update(check_action.keys())
        
        # 각 action_key에 대해 모든 agent의 데이터 통합
        for action_key in all_action_keys:
            all_yes_times = []
            all_no_times = []
            all_confidence = {}
            action_description = None
            
            for model_id, result in model_results.items():
                promptbank_data = result.get("promptbank_data", {})
                check_action = promptbank_data.get("check_action_step_DPI_type1", {})
                
                if action_key in check_action:
                    action_data = check_action[action_key]
                    if action_description is None:
                        action_description = action_data.get('action', '')
                    
                    times = action_data.get('time', [])
                    scores = action_data.get('score', [])
                    confidences = dict(action_data.get('confidence_score', []))
                    
                    for time_val, score_val in zip(times, scores):
                        if score_val == 1:
                            all_yes_times.append(time_val)
                        else:
                            all_no_times.append(time_val)
                        
                        if time_val in confidences:
                            # 여러 agent의 confidence가 있으면 평균 계산
                            if time_val not in all_confidence:
                                all_confidence[time_val] = []
                            all_confidence[time_val].append(confidences[time_val])
            
            # confidence 평균 계산
            avg_confidence = {}
            for time_val, conf_list in all_confidence.items():
                avg_confidence[time_val] = sum(conf_list) / len(conf_list) if conf_list else 0.5
            
            action_analysis[action_key] = {
                'action_description': action_description or '',
                'detected_times': sorted(set(all_yes_times)),
                'not_detected_times': sorted(set(all_no_times)),
                'confidence': avg_confidence,
                'total_detections': len(set(all_yes_times))
            }
        
        # 최종 종합 기술 생성
        final_summary = self._generate_final_summary(
            final_decisions, action_analysis
        )
        
        return {
            "video_info": video_info,
            "action_analysis": action_analysis,
            "action_decisions": final_decisions,
            "individual_agent_decisions": individual_agent_decisions,
            "final_summary": final_summary,
            "action_order": self.ACTION_ORDER,
            "summary": {
                "total_actions_detected": sum(
                    1 for action in action_analysis.values() 
                    if action['total_detections'] > 0
                ),
                "analysis_duration": video_info["play_time"]
            }
        }
    
    def _create_individual_agent_visualization(self, model_id: str, model_name: str, 
                                             reference_times: dict, promptbank_data: dict,
                                             video_info: dict, individual_decisions: dict = None):
        """
        개별 agent의 시계열 데이터 시각화 생성
        
        Args:
            model_id: agent 식별자
            model_name: agent 이름
            reference_times: 개별 agent의 reference_times
            promptbank_data: 개별 agent의 promptbank_data
            video_info: 비디오 정보
            individual_decisions: 개별 agent 판정 결과 (선택적)
            
        Returns:
            Plotly Figure 객체
        """
        try:
            if not promptbank_data:
                print(f"[{self.name}] {model_id}의 PromptBank 데이터가 없습니다.")
                return None
            
            search_reference_time = promptbank_data.get("search_reference_time", {})
            check_action_step_DPI_type1 = promptbank_data.get("check_action_step_DPI_type1", {})
            
            # 모든 키와 y 위치 설정 (REFERENCE_ORDER, ACTION_ORDER 순서 적용, 밑에서 위로)
            reference_keys = list(search_reference_time.keys())
            action_keys = list(check_action_step_DPI_type1.keys())
            
            # REFERENCE_ORDER에 따라 reference_keys 정렬
            ordered_reference_keys = []
            for ref in self.REFERENCE_ORDER:
                if ref in reference_keys:
                    ordered_reference_keys.append(ref)
            
            # REFERENCE_ORDER에 없는 reference_keys도 추가
            for key in reference_keys:
                if key not in ordered_reference_keys:
                    ordered_reference_keys.append(key)
            
            # ACTION_ORDER에 따라 action_keys 정렬
            ordered_action_keys = []
            for action in self.ACTION_ORDER:
                if action in action_keys:
                    ordered_action_keys.append(action)
            
            # ACTION_ORDER에 없는 action_keys도 추가
            for key in action_keys:
                if key not in ordered_action_keys:
                    ordered_action_keys.append(key)
            
            # 전체 순서: reference_keys + action_keys (밑에서 위로)
            ordered_keys = ordered_reference_keys + ordered_action_keys
            
            # y 위치 할당 (밑에서 위로)
            y_positions = {key: i * 0.1 for i, key in enumerate(ordered_keys)}
            
            # Action Decision 가져오기 및 Y축 라벨 생성
            action_decisions = individual_decisions or {}
            y_tick_text = []
            for key in ordered_keys:
                if key in action_decisions:
                    y_tick_text.append(f"{key}({action_decisions[key]})")
                else:
                    y_tick_text.append(key)
            
            play_time = video_info["play_time"]
            min_time, max_time = -1.0, play_time
            
            # Figure 생성
            fig = go.Figure()
            
            # 스트라이프 그리기
            for key, y_pos in y_positions.items():
                if key in reference_keys:
                    color = "blue"
                    opacity = 0.3
                else:
                    color = "gray"
                    opacity = 0.3
                
                fig.add_shape(
                    type="line",
                    x0=0, y0=y_pos, x1=1, y1=y_pos,
                    xref="paper", yref="y",
                    line=dict(color=color, width=10),
                    opacity=opacity
                )
            
            # Reference time 수직선 및 점 추가
            reference_times = []
            reference_y_pos = []
            reference_texts = []
            
            for key, value in search_reference_time.items():
                if value['reference_time'] >= 0:
                    y_pos = y_positions[key]
                    
                    # 수직선
                    fig.add_shape(
                        type="line",
                        x0=value['reference_time'], y0=min(y_positions.values()) - 0.05,
                        x1=value['reference_time'], y1=max(y_positions.values()) + 0.05,
                        line=dict(color="blue", width=1.5),
                        opacity=0.7
                    )
                    
                    reference_times.append(value['reference_time'])
                    reference_y_pos.append(y_pos)
                    reference_texts.append(f"{value['reference_time']:.1f}s")
            
            # Reference time 점들
            if reference_times:
                fig.add_trace(go.Scatter(
                    x=reference_times,
                    y=reference_y_pos,
                    mode='markers+text',
                    marker=dict(size=12, color='blue'),
                    text=reference_texts,
                    textposition="top center",
                    textfont=dict(size=9, color='blue'),
                    name='Reference Time',
                    showlegend=False,
                    hovertemplate='Reference Time: %{x:.1f}s<extra></extra>'
                ))
            
            # Action step 점들 추가
            action_times_filled = []
            action_y_pos_filled = []
            action_keys_filled = []
            action_confidence_filled = []
            action_times_empty = []
            action_y_pos_empty = []
            action_keys_empty = []
            action_confidence_empty = []
            
            # Confidence 딕셔너리 생성
            confidence_dict = {}
            for key, value in check_action_step_DPI_type1.items():
                if value['confidence_score']:
                    confidence_dict[key] = {time: conf for time, conf in value['confidence_score']}
            
            for key, value in check_action_step_DPI_type1.items():
                if value['time']:
                    y_pos = y_positions[key]
                    for time_val, score_val in zip(value['time'], value['score']):
                        time_val = float(time_val)
                        confidence_val = confidence_dict.get(key, {}).get(time_val, 0.5)
                        
                        if score_val == 1:
                            action_times_filled.append(time_val)
                            action_y_pos_filled.append(y_pos)
                            action_keys_filled.append(key)
                            action_confidence_filled.append(confidence_val)
                        elif score_val == 0:
                            action_times_empty.append(time_val)
                            action_y_pos_empty.append(y_pos)
                            action_keys_empty.append(key)
                            action_confidence_empty.append(confidence_val)
            
            # Score=1인 점들
            if action_times_filled:
                fig.add_trace(go.Scatter(
                    x=action_times_filled,
                    y=action_y_pos_filled,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=action_confidence_filled,  # Confidence 값으로 내부 색상 설정
                        colorscale='Greens',
                        cmin=0.0,
                        cmax=1.0,
                        symbol='circle',
                        colorbar=dict(
                            title="Confidence<br>(Score=1)",
                            x=1.02,
                            y=0.75,
                            len=0.4,
                            thickness=15
                        ),
                        line=dict(
                            width=1,
                            color=action_confidence_filled,  # 테두리도 Confidence로 설정
                            colorscale='Greens',
                            cmin=0.0,
                            cmax=1.0
                        )
                    ),
                    name='Action Steps (Score=1)',
                    showlegend=False,
                    hovertemplate='%{text}<br>Time: %{x:.1f}s<br>Score: 1<br>Confidence: %{marker.color:.2f}<extra></extra>',
                    text=action_keys_filled
                ))
            
            # Score=0인 점들
            if action_times_empty:
                fig.add_trace(go.Scatter(
                    x=action_times_empty,
                    y=action_y_pos_empty,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=action_confidence_empty,  # Confidence 값으로 내부 색상 설정
                        colorscale='Reds',
                        cmin=0.0,
                        cmax=1.0,
                        symbol='circle',  # 채워진 원으로 변경 (내부 색상 보이도록)
                        colorbar=dict(
                            title="Confidence<br>(Score=0)",
                            x=1.02,
                            y=0.25,
                            len=0.4,
                            thickness=15
                        ),
                        line=dict(
                            width=1,  # 테두리 두께를 Score=1과 동일하게 조정
                            color=action_confidence_empty,  # 테두리도 Confidence로 설정
                            colorscale='Reds',
                            cmin=0.0,
                            cmax=1.0
                        )
                    ),
                    name='Action Steps (Score=0)',
                    showlegend=False,
                    hovertemplate='%{text}<br>Time: %{x:.1f}s<br>Score: 0<br>Confidence: %{marker.color:.2f}<extra></extra>',
                    text=action_keys_empty
                ))
            
            # 레이아웃 설정
            fig.update_layout(
                title={
                    'text': f'[Individual Agent] Visualization: Reference Time and Action Steps, {model_name}',
                    'x': 0.5,
                    'font': {'size': 14, 'family': 'Arial'}
                },
                xaxis=dict(
                    title='time (sec)',
                    gridcolor='rgba(0,0,0,0.3)',
                    gridwidth=1,
                    range=[min_time, max_time],
                    showgrid=True
                ),
                yaxis=dict(
                    title='event',
                    tickmode='array',
                    tickvals=list(y_positions.values()),
                    ticktext=y_tick_text,
                    gridcolor='rgba(0,0,0,0.1)',
                    gridwidth=1
                ),
                plot_bgcolor='white',
                width=1000,
                height=600,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            print(f"시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_visualization(self, state: VideoAnalysisState):
        """Plotly 시각화 생성 (여러 모델의 평균값 기반) - 레거시 메서드 (사용하지 않음)"""
        try:
            promptbank_data_avg = state.get("promptbank_data_avg")
            if not promptbank_data_avg:
                print("평균 PromptBank 데이터가 없습니다.")
                return None
            
            video_info = state["video_info"]
            llm_name = state.get("llm_name", "Multiple Models (Average)")
            
            search_reference_time = promptbank_data_avg["search_reference_time"]
            check_action_step_DPI_type1 = promptbank_data_avg["check_action_step_DPI_type1"]
            
            # 모든 키와 y 위치 설정 (REFERENCE_ORDER, ACTION_ORDER 순서 적용, 밑에서 위로)
            reference_keys = list(search_reference_time.keys())
            action_keys = list(check_action_step_DPI_type1.keys())
            
            # REFERENCE_ORDER에 따라 reference_keys 정렬
            ordered_reference_keys = []
            for ref in self.REFERENCE_ORDER:
                if ref in reference_keys:
                    ordered_reference_keys.append(ref)
            
            # REFERENCE_ORDER에 없는 reference_keys도 추가
            for key in reference_keys:
                if key not in ordered_reference_keys:
                    ordered_reference_keys.append(key)
            
            # ACTION_ORDER에 따라 action_keys 정렬
            ordered_action_keys = []
            for action in self.ACTION_ORDER:
                if action in action_keys:
                    ordered_action_keys.append(action)
            
            # ACTION_ORDER에 없는 action_keys도 추가
            for key in action_keys:
                if key not in ordered_action_keys:
                    ordered_action_keys.append(key)
            
            # 전체 순서: reference_keys + action_keys (밑에서 위로)
            ordered_keys = ordered_reference_keys + ordered_action_keys
            
            # y 위치 할당 (밑에서 위로)
            y_positions = {key: i * 0.1 for i, key in enumerate(ordered_keys)}
            
            # Action Decision 가져오기 및 Y축 라벨 생성
            action_decisions = state.get("final_report", {}).get("action_decisions", {})
            y_tick_text = []
            for key in ordered_keys:
                if key in action_decisions:
                    y_tick_text.append(f"{key}({action_decisions[key]})")
                else:
                    y_tick_text.append(key)
            
            play_time = video_info["play_time"]
            min_time, max_time = -1.0, play_time
            
            # Figure 생성
            fig = go.Figure()
            
            # 스트라이프 그리기
            for key, y_pos in y_positions.items():
                if key in reference_keys:
                    color = "blue"
                    opacity = 0.3
                else:
                    color = "gray"
                    opacity = 0.3
                
                fig.add_shape(
                    type="line",
                    x0=0, y0=y_pos, x1=1, y1=y_pos,
                    xref="paper", yref="y",
                    line=dict(color=color, width=10),
                    opacity=opacity
                )
            
            # Reference time 수직선 및 점 추가
            reference_times = []
            reference_y_pos = []
            reference_texts = []
            
            for key, value in search_reference_time.items():
                if value['reference_time'] >= 0:
                    y_pos = y_positions[key]
                    
                    # 수직선
                    fig.add_shape(
                        type="line",
                        x0=value['reference_time'], y0=min(y_positions.values()) - 0.05,
                        x1=value['reference_time'], y1=max(y_positions.values()) + 0.05,
                        line=dict(color="blue", width=1.5),
                        opacity=0.7
                    )
                    
                    reference_times.append(value['reference_time'])
                    reference_y_pos.append(y_pos)
                    reference_texts.append(f"{value['reference_time']:.1f}s")
            
            # Reference time 점들
            if reference_times:
                fig.add_trace(go.Scatter(
                    x=reference_times,
                    y=reference_y_pos,
                    mode='markers+text',
                    marker=dict(size=12, color='blue'),
                    text=reference_texts,
                    textposition="top center",
                    textfont=dict(size=9, color='blue'),
                    name='Reference Time',
                    showlegend=False,
                    hovertemplate='Reference Time: %{x:.1f}s<extra></extra>'
                ))
            
            # Action step 점들 추가
            action_times_filled = []
            action_y_pos_filled = []
            action_keys_filled = []
            action_confidence_filled = []
            action_times_empty = []
            action_y_pos_empty = []
            action_keys_empty = []
            action_confidence_empty = []
            
            # Confidence 딕셔너리 생성
            confidence_dict = {}
            for key, value in check_action_step_DPI_type1.items():
                if value['confidence_score']:
                    confidence_dict[key] = {time: conf for time, conf in value['confidence_score']}
            
            for key, value in check_action_step_DPI_type1.items():
                if value['time']:
                    y_pos = y_positions[key]
                    for time_val, score_val in zip(value['time'], value['score']):
                        time_val = float(time_val)
                        confidence_val = confidence_dict.get(key, {}).get(time_val, 0.5)
                        
                        if score_val == 1:
                            action_times_filled.append(time_val)
                            action_y_pos_filled.append(y_pos)
                            action_keys_filled.append(key)
                            action_confidence_filled.append(confidence_val)
                        elif score_val == 0:
                            action_times_empty.append(time_val)
                            action_y_pos_empty.append(y_pos)
                            action_keys_empty.append(key)
                            action_confidence_empty.append(confidence_val)
            
            # Score=1인 점들
            if action_times_filled:
                fig.add_trace(go.Scatter(
                    x=action_times_filled,
                    y=action_y_pos_filled,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=action_confidence_filled,  # Confidence 값으로 내부 색상 설정
                        colorscale='Greens',
                        cmin=0.0,
                        cmax=1.0,
                        symbol='circle',
                        colorbar=dict(
                            title="Confidence<br>(Score=1)",
                            x=1.02,
                            y=0.75,
                            len=0.4,
                            thickness=15
                        ),
                        line=dict(
                            width=1,
                            color=action_confidence_filled,  # 테두리도 Confidence로 설정
                            colorscale='Greens',
                            cmin=0.0,
                            cmax=1.0
                        )
                    ),
                    name='Action Steps (Score=1)',
                    showlegend=False,
                    hovertemplate='%{text}<br>Time: %{x:.1f}s<br>Score: 1<br>Confidence: %{marker.color:.2f}<extra></extra>',
                    text=action_keys_filled
                ))
            
            # Score=0인 점들
            if action_times_empty:
                fig.add_trace(go.Scatter(
                    x=action_times_empty,
                    y=action_y_pos_empty,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=action_confidence_empty,  # Confidence 값으로 내부 색상 설정
                        colorscale='Reds',
                        cmin=0.0,
                        cmax=1.0,
                        symbol='circle',  # 채워진 원으로 변경 (내부 색상 보이도록)
                        colorbar=dict(
                            title="Confidence<br>(Score=0)",
                            x=1.02,
                            y=0.25,
                            len=0.4,
                            thickness=15
                        ),
                        line=dict(
                            width=1,  # 테두리 두께를 Score=1과 동일하게 조정
                            color=action_confidence_empty,  # 테두리도 Confidence로 설정
                            colorscale='Reds',
                            cmin=0.0,
                            cmax=1.0
                        )
                    ),
                    name='Action Steps (Score=0)',
                    showlegend=False,
                    hovertemplate='%{text}<br>Time: %{x:.1f}s<br>Score: 0<br>Confidence: %{marker.color:.2f}<extra></extra>',
                    text=action_keys_empty
                ))
            
            # 레이아웃 설정
            fig.update_layout(
                title={
                    'text': f'[Multi-Agent] Visualization: Reference Time and Action Steps, {llm_name}',
                    'x': 0.5,
                    'font': {'size': 14, 'family': 'Arial'}
                },
                xaxis=dict(
                    title='time (sec)',
                    gridcolor='rgba(0,0,0,0.3)',
                    gridwidth=1,
                    range=[min_time, max_time],
                    showgrid=True
                ),
                yaxis=dict(
                    title='event',
                    tickmode='array',
                    tickvals=list(y_positions.values()),
                    ticktext=y_tick_text,
                    gridcolor='rgba(0,0,0,0.1)',
                    gridwidth=1
                ),
                plot_bgcolor='white',
                width=1000,
                height=600,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            print(f"시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    

