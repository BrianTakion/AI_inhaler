#!/usr/bin/env python
# coding: utf-8

"""
통합 흡입기 비디오 분석 애플리케이션
여러 디바이스 타입에 대해 통합적으로 분석을 수행합니다.
"""

import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# app_common 디렉토리의 .env 파일 로드
app_common_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(app_common_dir, ".env")
load_dotenv(dotenv_path=env_path)

# API 키 로드
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")


def print_analysis_summary(report: dict):
    """
    분석 결과 요약 출력
    
    Args:
        report: final_report 딕셔너리 (action_order 포함)
    """
    print("\n" + "="*50)
    print("=== 비디오 분석 결과 요약 ===")
    print("="*50)
    
    # 비디오 정보
    video_info = report["video_info"]
    print(f"\n[비디오 정보]")
    print(f"  파일명: {video_info['video_name']}")
    print(f"  재생시간: {video_info['play_time']}초")
    print(f"  총 프레임: {video_info['frame_count']}")
    print(f"  해상도: {video_info['video_width']}x{video_info['video_height']}px")
    
    # 최종 판단 결과
    if "action_decisions" in report:
        print(f"\n[최종 판단 결과]")
        action_order = report.get("action_order", [])
        
        # action_order에 따라 순서대로 출력
        for key in action_order:
            if key in report["action_decisions"]:
                val = report["action_decisions"][key]
                result_str = "SUCCESS" if val == 1 else "FAIL"
                print(f"  {key}: {result_str} ({val})")
        
        # action_order에 없는 키들도 출력
        for key, val in report["action_decisions"].items():
            if key not in action_order:
                result_str = "SUCCESS" if val == 1 else "FAIL"
                print(f"  {key}: {result_str} ({val}) <--- action_order에 없음음")
    
    # 최종 종합 기술 출력
    if "final_summary" in report:
        print(f"\n[최종 종합 기술]")
        final_summary = report["final_summary"]
        if final_summary:
            # 여러 줄로 출력 (들여쓰기 포함)
            for line in final_summary.split('\n'):
                print(f"  {line}")
        else:
            print("  종합 기술 정보가 없습니다.")
    
    print("\n" + "="*50)


def run_device_analysis(device_type: str, video_path: str, llm_models: list, save_individual_report: bool = False):
    """
    특정 디바이스 타입에 대한 분석 실행
    
    Args:
        device_type: 디바이스 타입 (예: 'pMDI_type1', 'DPI_type1' 등)
        video_path: 분석할 비디오 파일 경로
        llm_models: 사용할 LLM 모델 리스트
        save_individual_report: 개별 에이전트 결과물에 대한 시각화 HTML 저장 여부 (기본값: False)
        
    Returns:
        분석 결과 상태
    """
    print("\n" + "="*80)
    print(f"디바이스 타입: {device_type}")
    print("="*80)
    
    # 해당 디바이스 타입의 app 디렉토리 경로
    app_dir = os.path.join(project_root, f"app_{device_type}")
    
    if not os.path.exists(app_dir):
        print(f"❌ 오류: {app_dir} 디렉토리가 존재하지 않습니다.")
        return None
    
    # 해당 디렉토리로 sys.path 추가
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    try:
        # 해당 디바이스의 모듈 import
        from agents.state import create_initial_state
        from graph_workflow import create_workflow
        from app_common import class_MultimodalLLM_QA_251107 as mLLM
        
        print(f"LLM 모델 초기화 ({len(llm_models)}개):")
        for idx, model_name in enumerate(llm_models):
            print(f"  {idx+1}. {model_name}")
        
        # 각 모델의 provider에 따라 적절한 API 키 사용하여 인스턴스 생성
        mllm_instances = []
        for model_name in llm_models:
            if "gemini" in model_name:
                if not google_api_key:
                    raise ValueError(
                        f"Google Gemini 모델({model_name})을 사용하려면 GOOGLE_API_KEY가 필요합니다.\n"
                        ".env 파일에 'GOOGLE_API_KEY=your-key' 형식으로 추가하세요."
                    )
                mllm_instances.append(mLLM.multimodalLLM(llm_name=model_name, api_key=google_api_key))
            else:  # OpenAI 모델
                if not openai_api_key:
                    raise ValueError(
                        f"OpenAI 모델({model_name})을 사용하려면 OPENAI_API_KEY가 필요합니다.\n"
                        ".env 파일에 'OPENAI_API_KEY=your-key' 형식으로 추가하세요."
                    )
                mllm_instances.append(mLLM.multimodalLLM(llm_name=model_name, api_key=openai_api_key))
        
        print(f"\n분석할 비디오: {video_path}")
        
        # 첫 번째 모델의 API 키를 전달
        first_model_api_key = google_api_key if "gemini" in llm_models[0] else openai_api_key
        
        # 초기 상태 생성
        initial_state = create_initial_state(
            video_path=video_path,
            llm_models=llm_models,
            api_key=first_model_api_key,
            save_individual_report=save_individual_report
        )
        
        # 워크플로우 생성
        workflow = create_workflow(mllm_instances, llm_models)
        
        # 워크플로우 실행
        final_state = workflow.run(initial_state)
        
        # 결과 출력
        if final_state["status"] == "completed":
            print("\n✅ 분석이 성공적으로 완료되었습니다!")
            
            if final_state.get("final_report"):
                report = final_state["final_report"]
                # 분석 결과 요약 출력
                print_analysis_summary(report)
            
            print(f"\n총 {len(final_state['agent_logs'])}개의 Agent 로그가 기록되었습니다.")
        else:
            print("\n❌ 분석 중 오류가 발생했습니다.")
            if final_state.get("errors"):
                print("오류 목록:")
                for error in final_state["errors"]:
                    print(f"  - {error}")
        
        return final_state
        
    except Exception as e:
        print(f"❌ {device_type} 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # sys.path에서 제거 (다음 디바이스 분석을 위해)
        if app_dir in sys.path:
            sys.path.remove(app_dir)


def main():
    """
    메인 실행 함수
    """
    # ========================================
    # 사용자 지정 변수
    # ========================================
    video_path = r"/workspaces/AI_inhaler/app_pMDI_type2/video_source/foster2.mp4"
    device_list = ['pMDI_type1', 'pMDI_type2', 'DPI_type1', 'DPI_type2', 'DPI_type3', 'SMI_type1']
    device_type = device_list[1]

    # "gpt-4.1", "gpt-5-nano", "gpt-5.1", "gpt-5.2"
    # "gemini-2.5-pro", "gemini-3-flash-preview", "gemini-3-pro-preview"
    llm_models = ['gpt-4.1', 'gpt-5.1', 'gemini-2.5-pro', 'gemini-3-flash-preview']
    save_individual_report = True  # 개별 리포트 저장 여부 (True: 저장, False: 저장하지 않기)
    
    result = run_device_analysis(
        device_type=device_type,
        video_path=video_path,
        llm_models=llm_models,
        save_individual_report=save_individual_report
    )

    # ========================================
    # 전체 결과 요약
    # ========================================
    print("\n" + "="*80)
    print("전체 분석 결과 요약")
    print("="*80)
    
    if result is None:
        print(f"{device_type}: ❌ 실패")
    elif result.get("status") == "completed":
        print(f"{device_type}: ✅ 완료")
    else:
        print(f"{device_type}: ⚠️ 부분 완료 또는 오류")
    
    print("\n분석 완료!")
    return result


if __name__ == "__main__":
    results = main()

