#!/usr/bin/env python
# coding: utf-8

"""
Video Analyzer Agent (Generic)
기준 시점 탐지와 행동 단계 분석을 통합하여 수행합니다.
동적으로 여러 LLM 모델을 지원합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import class_PromptBank_SMI_type1 as PB
from .state import VideoAnalysisState
from .video_processor_agent import VideoProcessorAgent


class VideoAnalyzerAgent:
    """
    비디오 분석 통합 Agent (Generic)
    
    주요 기능:
    1. 기준 시점 탐지
       - inhalerIN: 흡입기가 처음 나타나는 시각
       - faceONinhaler: 흡입기를 입에 대는 시각
       - inhalerOUT: 흡입기가 화면에서 사라지는 시각
    
    2. 행동 단계 분석
       - 개별 행동 인식
       - 신뢰도 평가
       - 시간대별 행동 매핑
    """
    
    def __init__(self, mllm, video_processor: VideoProcessorAgent, model_id: str, model_name: str):
        """
        Args:
            mllm: Multimodal LLM 인스턴스
            video_processor: VideoProcessorAgent 인스턴스
            model_id: 모델 고유 ID (예: "gpt-4o_0", "gpt-4o-mini_1")
            model_name: 모델 이름 (예: "gpt-4o", "gpt-4o-mini")
        """
        self.mllm = mllm
        self.video_processor = video_processor
        self.model_id = model_id
        self.model_name = model_name
        self.name = f"VideoAnalyzerAgent_{model_id}"
        self.promptbank = PB.PromptBank()
    
    def process(self, state: VideoAnalysisState) -> VideoAnalysisState:
        """
        기준 시점 탐지 및 행동 단계 분석을 수행
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        try:
            video_path = state["video_path"]
            video_info = state["video_info"]
            play_time = video_info["play_time"]
            
            state["agent_logs"].append({
                "agent": self.name,
                "action": "start_analysis",
                "message": f"비디오 분석 시작 (기준 시점 탐지 + 행동 분석) - {self.model_name}"
            })
            
            # ========================================
            # Part 1: 기준 시점 탐지
            # ========================================
            print(f"\n[{self.name}] 기준 시점 탐지 시작...")
            
            # 1. inhalerIN 탐지
            print(f"\n[{self.name}] inhalerIN 탐지 시작...")
            ref_time_in, q_answers_in = self._detect_inhaler_in(
                video_path, play_time, start_time=0.0
            )
            # PromptBank에 저장
            q_mapping_in = {'Q1': 'sit_stand'}
            self.promptbank.save_to_promptbank('inhalerIN', ref_time_in, q_answers_in, q_mapping_in)
            
            print(f"[{self.name}] inhalerIN 탐지 완료: {ref_time_in}초")
            
            # 2. faceONinhaler 탐지
            print(f"\n[{self.name}] faceONinhaler 탐지 시작...")
            ref_time_face, q_answers_face = self._detect_face_on_inhaler(
                video_path, play_time, start_time=ref_time_in
            )
            # PromptBank에 저장
            q_mapping_face = {
                'Q1': 'sit_stand',
                'Q2': 'load_dose',
                'Q3': 'remove_cover',
                'Q4': 'inspect_mouthpiece',
                'Q5': 'hold_inhaler',
                'Q6': 'exhale_before'
            }
            self.promptbank.save_to_promptbank('faceONinhaler', ref_time_face, q_answers_face, q_mapping_face)
            
            print(f"[{self.name}] faceONinhaler 탐지 완료: {ref_time_face}초")
            
            # 3. inhalerOUT 탐지
            print(f"\n[{self.name}] inhalerOUT 탐지 시작...")
            ref_time_out, q_answers_out = self._detect_inhaler_out(
                video_path, play_time, start_time=ref_time_face
            )
            # PromptBank에 저장
            q_mapping_out = {
                'Q1': 'exhale_before',
                'Q2': 'seal_lips',
                'Q3': 'inhale_deeply',
                'Q4': 'remove_inhaler',
                'Q5': 'hold_breath',
                'Q6': 'exhale_after'
            }
            self.promptbank.save_to_promptbank('inhalerOUT', ref_time_out, q_answers_out, q_mapping_out)
            
            print(f"[{self.name}] inhalerOUT 탐지 완료: {ref_time_out}초")
            
            # PromptBank 데이터 저장
            promptbank_data = {
                "search_reference_time": self.promptbank.search_reference_time,
                "check_action_step_SMI_type1": self.promptbank.check_action_step_SMI_type1
            }
            
            reference_times = {
                "inhalerIN": ref_time_in,
                "faceONinhaler": ref_time_face,
                "inhalerOUT": ref_time_out
            }
            
            q_answers_accumulated = {
                "inhalerIN": q_answers_in,
                "faceONinhaler": q_answers_face,
                "inhalerOUT": q_answers_out
            }
            
            state["agent_logs"].append({
                "agent": self.name,
                "action": "reference_detection_complete",
                "message": f"기준 시점 탐지 완료: IN={ref_time_in}초, FACE={ref_time_face}초, OUT={ref_time_out}초"
            })
            
            # ========================================
            # Part 2: 행동 단계 분석
            # ========================================
            print(f"\n[{self.name}] 행동 단계 분석 시작...")
            
            if promptbank_data:
                # 행동 분석 결과 생성
                action_summary = self._create_action_summary(promptbank_data)
                
                state["agent_logs"].append({
                    "agent": self.name,
                    "action": "action_analysis_complete",
                    "message": f"행동 단계 분석 완료: {len(action_summary)}개 행동 인식"
                })
                
                print(f"[{self.name}] 행동 단계 분석 완료: {len(action_summary)}개 행동")
            else:
                raise ValueError("PromptBank 데이터가 생성되지 않았습니다")
            
            # 동적 모델별 결과 저장
            state["model_results"][self.model_id] = {
                "reference_times": reference_times,
                "action_analysis_results": action_summary,
                "q_answers_accumulated": q_answers_accumulated,
                "promptbank_data": promptbank_data
            }
            
            # 최종 상태 업데이트
            state["agent_logs"].append({
                "agent": self.name,
                "action": "complete",
                "message": f"비디오 분석 완료 (기준 시점 탐지 + 행동 분석) - {self.model_name}"
            })
            
        except Exception as e:
            error_msg = f"[{self.name}] 비디오 분석 중 오류: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "error"
            print(error_msg)
            import traceback
            traceback.print_exc()
        
        return state
    
    # ========================================
    # 기준 시점 탐지 메서드들
    # ========================================
    
    def _detect_inhaler_in(self, video_path: str, play_time: float, start_time: float = 0.0):
        """inhalerIN 기준 시간 탐지"""
        segment_time = 2.0
        sampling_time = segment_time / 10.0
        offset_time = segment_time
        
        system_prompt = "You are a helpful assistant that analyzes images and videos to determine if the user is performing a specific action."
        user_prompt = f"""
[Task 1] Individual Image Analysis
Analyze each image independently without using context from other images.

Question: {self.promptbank.search_reference_time['inhalerIN']['action']}

* Judgment Criteria (apply all):
- Each image is evaluated as a standalone frame.
- If the person holds an object, treat it as an inhaler.
- If consecutive images satisfy the above conditions, the overall answer is YES; otherwise, NO.

* Output Format:
Overall_Answer: [YES or NO]  
Reason: {{Explain the decision very shortly in Korean.}}

[Task 2] Sequential Video Analysis
Analyze the sequence of images as consecutive video frames.

Q1: {self.promptbank.check_action_step_SMI_type1['sit_stand']['action']}

* Judgment Criteria (apply all):
- Treat all frames as parts of a continuous video.
- Use temporal continuity to determine whether the inhaler appears across frames.
- Allow inference of inhaler visibility even if partially obscured in some frames, based on continuity.

* Output Format:
Q1_Answer: [YES or NO]
Q1_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
"""
        
        final_start_time, q_answers_acc = self._search_reference_time(
            video_path, system_prompt, user_prompt, play_time, 
            start_time, segment_time, offset_time, sampling_time
        )
        
        return final_start_time, q_answers_acc
    
    def _detect_face_on_inhaler(self, video_path: str, play_time: float, start_time: float):
        """faceONinhaler 기준 시간 탐지"""
        segment_time = 0.5
        sampling_time = segment_time / 10.0
        offset_time = segment_time
        
        system_prompt = "You are a helpful assistant that analyzes images and videos to determine if the user is performing a specific action."
        user_prompt = f"""
[Task 1] Individual Image Analysis
Analyze each image independently without using context from other images.

Question: {self.promptbank.search_reference_time['faceONinhaler']['action']}

* Judgment Criteria (apply all):
- Each image is evaluated as a standalone frame.
- If the person holds an object, treat it as an inhaler.
- If consecutive images satisfy the above conditions, the overall answer is YES; otherwise, NO.

* Output Format:
Overall_Answer: [YES or NO]  
Reason: {{Explain the decision very shortly in Korean.}}

[Task 2] Sequential Video Analysis
Analyze the sequence of images as consecutive video frames.

Q1. {self.promptbank.check_action_step_SMI_type1['sit_stand']['action']}
Q2. {self.promptbank.check_action_step_SMI_type1['load_dose']['action']}
Q3. {self.promptbank.check_action_step_SMI_type1['remove_cover']['action']}
Q4. {self.promptbank.check_action_step_SMI_type1['inspect_mouthpiece']['action']}
Q5. {self.promptbank.check_action_step_SMI_type1['hold_inhaler']['action']}
Q6. {self.promptbank.check_action_step_SMI_type1['exhale_before']['action']}

* Judgment Criteria (apply all):
- Treat all frames as parts of a continuous video.
- Use temporal continuity to determine whether the inhaler appears across frames.
- Allow inference of inhaler visibility even if partially obscured in some frames, based on continuity.

* Output Format:
Q1_Answer: [YES or NO]
Q1_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q2_Answer: [YES or NO]
Q2_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q3_Answer: [YES or NO]
Q3_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q4_Answer: [YES or NO]
Q4_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q5_Answer: [YES or NO]
Q5_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q6_Answer: [YES or NO]
Q6_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
"""
        
        final_start_time, q_answers_acc = self._search_reference_time(
            video_path, system_prompt, user_prompt, play_time,
            start_time, segment_time, offset_time, sampling_time
        )
        
        return final_start_time, q_answers_acc
    
    def _detect_inhaler_out(self, video_path: str, play_time: float, start_time: float):
        """inhalerOUT 기준 시간 탐지"""
        segment_time = 0.5
        sampling_time = segment_time / 10.0
        offset_time = segment_time
        
        system_prompt = "You are a helpful assistant that analyzes images and videos to determine if the user is performing a specific action."
        user_prompt = f"""
[Task 1] Individual Image Analysis
Analyze each image independently without using context from other images.

Question: {self.promptbank.search_reference_time['inhalerOUT']['action']}

* Judgment Criteria (apply all):
- Each image is evaluated as a standalone frame.
- If the person holds an object, treat it as an inhaler.
- If consecutive images satisfy the above conditions, the overall answer is YES; otherwise, NO.

* Output Format:
Overall_Answer: [YES or NO]  
Reason: {{Explain the decision very shortly in Korean.}}

[Task 2] Sequential Video Analysis
Analyze the sequence of images as consecutive video frames.

Q1. {self.promptbank.check_action_step_SMI_type1['exhale_before']['action']}
Q2. {self.promptbank.check_action_step_SMI_type1['seal_lips']['action']}
Q3. {self.promptbank.check_action_step_SMI_type1['inhale_deeply']['action']}
Q4. {self.promptbank.check_action_step_SMI_type1['remove_inhaler']['action']}
Q5. {self.promptbank.check_action_step_SMI_type1['hold_breath']['action']}
Q6. {self.promptbank.check_action_step_SMI_type1['exhale_after']['action']}

* Judgment Criteria (apply all):
- Treat all frames as parts of a continuous video.
- Use temporal continuity to determine whether the inhaler appears across frames.
- Allow inference of inhaler visibility even if partially obscured in some frames, based on continuity.

* Output Format:
Q1_Answer: [YES or NO]
Q1_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q2_Answer: [YES or NO]
Q2_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q3_Answer: [YES or NO]
Q3_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q4_Answer: [YES or NO]
Q4_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q5_Answer: [YES or NO]
Q5_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
Q6_Answer: [YES or NO]
Q6_Confidence: [0.0 to 1.0, indicating your confidence level in the answer]
"""
        
        final_start_time, q_answers_acc = self._search_reference_time(
            video_path, system_prompt, user_prompt, play_time,
            start_time, segment_time, offset_time, sampling_time
        )
        
        return final_start_time, q_answers_acc
    
    def _search_reference_time(self, video_path: str, system_prompt: str, user_prompt: str,
                              play_time: float, start_time: float, segment_time: float,
                              offset_time: float, sampling_time: float):
        """
        기준 시간 탐색
        """
        M, N = 1, int(segment_time / sampling_time)
        gridSize = (int(1280/2)*N, int(720/2)*M)
        
        q_answers_accumulated = {}
        final_start_time = start_time
        
        while start_time <= play_time - segment_time:
            print(f'  검색 중... start_time={start_time:.1f}초')
            end_time = start_time + segment_time
            
            # 프레임 추출
            output_image, _, _ = self.video_processor.extract_frames(
                video_path, start_time, end_time, M, N, gridSize, (0, 0)
            )
            
            # LLM 쿼리
            response = self.mllm.query_answer_chatGPT(
                system_prompt, user_prompt, image_array=output_image
            )
            
            # 응답 파싱
            overall_answer = self._parse_overall_answer(response)
            current_q_answers, current_q_confidence = self._parse_q_answers(response)
            
            # 누적 저장
            for q_key, answer in current_q_answers.items():
                if q_key not in q_answers_accumulated:
                    q_answers_accumulated[q_key] = []
                confidence = current_q_confidence.get(q_key, None)
                q_answers_accumulated[q_key].append((round(start_time, 1), answer, confidence))
            
            # 종료 조건
            if overall_answer == "YES":
                final_start_time = round(start_time, 1)
                break
            
            start_time += offset_time
        
        # 루프 종료 후 처리
        if start_time > play_time - segment_time:
            print("  영상 거의 끝까지 탐색했습니다.")
            final_start_time = round(start_time - offset_time, 1)
        
        return final_start_time, q_answers_accumulated
    
    def _parse_overall_answer(self, response: str) -> str:
        """Overall_Answer 파싱"""
        overall_pattern = re.compile(r'\*{0,2}Overall_Answer:\s*\*{0,2}\s*(YES|NO)', re.IGNORECASE)
        overall_match = overall_pattern.search(response)
        if overall_match:
            return overall_match.group(1).upper()
        return "NO"
    
    def _parse_q_answers(self, response: str):
        """Q1_Answer, Q2_Answer 등 파싱"""
        current_q_answers = {}
        current_q_confidence = {}
        
        # Q1_Answer, Q2_Answer 파싱
        q_pattern = re.compile(r'\*{0,2}Q(\d+)_Answer:\s*\*{0,2}\s*(YES|NO)', re.IGNORECASE)
        q_matches = q_pattern.findall(response)
        
        for q_num, answer in q_matches:
            current_q_answers[f'Q{q_num}'] = answer.upper()
        
        # Q1_Confidence, Q2_Confidence 파싱
        confidence_pattern = re.compile(r'\*{0,2}Q(\d+)_Confidence:\s*\*{0,2}\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
        confidence_matches = confidence_pattern.findall(response)
        
        for q_num, confidence in confidence_matches:
            try:
                current_q_confidence[f'Q{q_num}'] = float(confidence)
            except ValueError:
                current_q_confidence[f'Q{q_num}'] = None
        
        return current_q_answers, current_q_confidence
    
    # ========================================
    # 행동 단계 분석 메서드들
    # ========================================
    
    def _create_action_summary(self, promptbank_data: dict) -> dict:
        """
        PromptBank 데이터로부터 행동 요약 생성
        
        Args:
            promptbank_data: PromptBank 데이터
            
        Returns:
            행동 요약 딕셔너리
        """
        action_summary = {}
        check_action_step_SMI_type1 = promptbank_data.get("check_action_step_SMI_type1", {})
        
        for action_key, action_data in check_action_step_SMI_type1.items():
            if action_data['time']:  # 데이터가 있는 경우만
                # YES(score=1)인 시간들 추출
                yes_times = [
                    time_val for time_val, score_val in zip(action_data['time'], action_data['score'])
                    if score_val == 1
                ]
                
                # NO(score=0)인 시간들 추출
                no_times = [
                    time_val for time_val, score_val in zip(action_data['time'], action_data['score'])
                    if score_val == 0
                ]
                
                # Confidence 정보
                confidence_info = {}
                if action_data.get('confidence_score'):
                    confidence_info = {
                        time: conf for time, conf in action_data['confidence_score']
                    }
                
                action_summary[action_key] = {
                    'action_description': action_data['action'],
                    'detected_times': yes_times,
                    'not_detected_times': no_times,
                    'confidence': confidence_info,
                    'total_detections': len(yes_times)
                }
        
        return action_summary


