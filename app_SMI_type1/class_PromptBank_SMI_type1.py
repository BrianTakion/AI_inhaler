class PromptBank:
    def __init__(self):
        """
        PromptBank 클래스 초기화
        reference_time은 0, timeANDscore는 빈 리스트로 초기화
        """
        self.search_reference_time = {
            'inhalerIN': {
                'action': 'Is the inhaler visible at any point throughout the images?',
                'reference_time': 0.0
            },
            'faceONinhaler': {
                'action': 'Is the person holding an object to the mouth as if using an inhaler?',
                'reference_time': 0.0
            },
            'inhalerOUT': {
                'action': 'Is the inhaler invisible at any point throughout the images?',
                'reference_time': 0.0
            }
        }

        self.check_action_step_SMI_type1 = {
            'sit_stand': {
                'action': 'Is the user sitting or standing upright? (Consider the user upright even if they are sitting with a slight forward lean.)',
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'load_dose': {
                'action': 'Is the user loading the medication? (Consider the user loading the medication if they are manipulating, twisting, or opening the inhaler.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'remove_cover': {
                'action': 'Has the user removed the mouthpiece cover? (Consider the user removing the cover if the mouthpiece is visible when the inhaler is positioned near the mouth.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'inspect_mouthpiece': {
                'action': 'Is the user inspecting the mouthpiece? (Consider the user inspecting if they are gazing toward the mouthpiece.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'hold_inhaler': {
                'action': 'Is the user holding the inhaler upright?', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'exhale_before': {
                'action': 'Is the user exhaling away from the inhaler? (Consider the user exhaling if the mouth moves, the head lowers, or the eyes gaze downward.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'seal_lips': {
                'action': 'Is the user placing their mouth on the mouthpiece of the inhaler?', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'inhale_deeply': {
                'action': 'Is the user inhaling from the inhaler? (Consider the user inhaling if the inhaler is in their mouth and they appear to be sucking on it.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'remove_inhaler': {
                'action': 'Is the user removing the inhaler from their mouth?', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'hold_breath': {
                'action': 'Is the user holding their breath? (Consider the user holding their breath if their mouth stays closed for a while.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            },
            'exhale_after': {
                'action': 'Is the user exhaling away from the inhaler? (Consider the user exhaling if lips are tighter than in the previous frames.)', 
                'time': [],
                'score': [],
                'confidence_score': []
            }
        }


    def save_to_promptbank(self, reference_key, reference_time, q_answers_accumulated, q_mapping):
        """
        누적된 Q&A 결과를 PromptBank에 저장하는 메서드
        
        Args:
            reference_key (str): search_reference_time의 키 (예: 'inhalerIN', 'faceONinhaler')
            reference_time (float): 기준 시간
            q_answers_accumulated (dict): 누적된 Q&A 결과 (time, answer, confidence)
            q_mapping (dict): Q번호와 액션 키의 매핑 (예: {'Q1': 'sit_stand'})
        """
        # 1. 기준 시간 저장
        self.search_reference_time[reference_key]['reference_time'] = reference_time
        
        # 2. Q&A 결과를 time과 score로 분리하여 저장
        for q_key, action_key in q_mapping.items():
            if q_key in q_answers_accumulated:
                for answer_data in q_answers_accumulated[q_key]:
                    # answer_data는 (time, answer, confidence) 튜플
                    if len(answer_data) == 3:
                        time_val, answer_str, confidence = answer_data
                    else:
                        # 하위 호환성: confidence가 없는 경우
                        time_val, answer_str = answer_data
                        confidence = None
                    
                    # 시간값을 float로 변환하여 저장
                    time_val = float(time_val)
                    score = 1 if answer_str == 'YES' else 0
                    self.check_action_step_SMI_type1[action_key]['time'].append(time_val)
                    self.check_action_step_SMI_type1[action_key]['score'].append(score)
                    
                    # confidence score 저장
                    if confidence is not None:
                        self.check_action_step_SMI_type1[action_key]['confidence_score'].append((time_val, confidence))

    @staticmethod
    def get_fail_summary_prompt(action_decisions: dict, action_analysis: dict) -> tuple:
        """
        FAIL 항목에 대한 종합 기술을 생성하기 위한 프롬프트 생성
        
        Args:
            action_decisions: 최종 판단 결과 (예: {'sit_stand': 1, 'load_dose': 0, ...})
            action_analysis: 행동 분석 상세 정보
            
        Returns:
            (system_prompt, user_prompt) 튜플
        """
        # FAIL된 항목 추출
        fail_actions = []
        for action_key, decision in action_decisions.items():
            if decision == 0:  # FAIL
                fail_actions.append(action_key)
        
        # FAIL이 없으면 빈 프롬프트 반환
        if not fail_actions:
            return None, None
        
        # Action 설명 매핑
        action_descriptions = {
            'sit_stand': '앉거나 서서 똑바로 있는 자세',
            'remove_cover': '마우스피스 커버 제거',
            'load_dose': '약물 로딩 (흡입기를 조작, 비틀거나 여는 행동)',
            'inspect_mouthpiece': '마우스피스 검사 (마우스피스를 향해 시선을 두는 행동)',
            'hold_inhaler': '흡입기를 똑바로 잡기',
            'exhale_before': '흡입기에서 멀리 숨 내쉬기 (입 움직임, 머리 내림, 눈 시선 아래로)',
            'seal_lips': '마우스피스에 입 대기',
            'inhale_deeply': '흡입기로 깊게 흡입하기 (흡입기가 입에 있고 빨아들이는 모습)',
            'remove_inhaler': '입에서 흡입기 제거',
            'hold_breath': '숨 참기 (입이 잠시 닫혀있는 상태)',
            'exhale_after': '흡입기에서 멀리 숨 내쉬기 (이전 프레임보다 입술이 더 조이는 모습)'
        }
        
        # FAIL 항목 정보 수집
        fail_info_list = []
        for action_key in fail_actions:
            action_desc = action_descriptions.get(action_key, action_key)
            fail_info_list.append(f"- {action_key} ({action_desc})")
        
        # System Prompt
        system_prompt = """당신은 흡입기 사용법 분석 전문가입니다."""

        # User Prompt
        user_prompt = f"""다음은 흡입기 사용법 비디오 분석 결과입니다.

[FAIL된 항목]
{chr(10).join(fail_info_list)}

위 [FAIL된 항목] 정보를 바탕으로 FAIL 항목별로 구체적인 문제점을 [출력 예시]처럼 한국어로 기술 바랍니다. 

[출력 예시]
  - 마우스피스 검사: 흡입기 사용 전 마우스피스를 눈으로 확인하지 않았습니다.
  - 숨 참기: 약물을 흡입한 후 숨을 잠시 참지 않았습니다.
  - 입에서 흡입기 제거: 흡입 후 흡입기를 입에서 바로 제거하지 않았습니다.

  수행되지 않은 윗 단계에 대해 추가 연습이 필요합니다."""

        return system_prompt, user_prompt