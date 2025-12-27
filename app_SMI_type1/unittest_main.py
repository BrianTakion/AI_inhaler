#!/usr/bin/env python
# coding: utf-8

"""
LangGraph 기반 Multi-Agent 흡입기 비디오 분석기
동적 LLM 모델 리스트 지원 - 병렬 실행 및 평균 시각화
"""

import os
import sys
from dotenv import load_dotenv

# app_server 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# app_server 디렉토리의 .env 파일 로드
app_server_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app_server')
env_path = os.path.join(app_server_dir, ".env")
load_dotenv(dotenv_path=env_path)

# API 키 로드
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# 사용할 모델의 provider에 따라 필요한 API 키 확인
# OpenAI 모델 사용 시 openai_api_key 필요
# Google Gemini 모델 사용 시 google_api_key 필요

from app_server import class_MultimodalLLM_QA_251107 as mLLM
from agents.state import create_initial_state
from graph_workflow import create_workflow


def main():
    """
    메인 실행 함수
    
    주요 기능:
    1. 리스트로 여러 LLM 모델 지정 (같은 모델 중복 가능)
    2. 모든 모델이 병렬로 비디오 분석 수행
    3. 결과를 자동으로 평균 계산 및 시각화
    """
    
    # ========================================
    # LLM 모델 설정
    # ========================================
    # 리스트에 원하는 모델을 자유롭게 지정 (개수 제한 없음, 중복 가능)
    # 예시:
    #   llm_models = ["gemini-2.5-pro"]                      # 1개 모델 (Google)
    #   llm_models = ["gpt-4o-mini", "gpt-4o-mini", "gpt-4o"] # 3개 모델 (중복 가능)
    #   llm_models = ["gemini-2.5-pro"] * 5                  # 5개 동일 모델
    #   "gpt-5-nano", "gpt-4.1", "gpt-5-mini", "gpt-5.1", "gpt-5.2",
    #   "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-pro-preview"
    
    llm_models = ["gpt-4.1"]
    
    print(f"LLM 모델 초기화 ({len(llm_models)}개):")
    for idx, model_name in enumerate(llm_models):
        print(f"  {idx+1}. {model_name}")
    
    # 각 모델의 provider에 따라 적절한 API 키 사용
    mllm_instances = []
    for model_name in llm_models:
        # 모델명으로 provider 판단
        if "gemini" in model_name:
            if not google_api_key:
                raise ValueError(
                    f"Google Gemini 모델({model_name})을 사용하려면 GOOGLE_API_KEY가 필요합니다.\n"
                    ".env 파일에 'GOOGLE_API_KEY=your-key' 형식으로 추가하세요.\n"
                    "API 키 발급: https://aistudio.google.com/app/apikey"
                )
            mllm_instances.append(mLLM.multimodalLLM(llm_name=model_name, api_key=google_api_key))
        else:  # OpenAI 모델 (gpt-4o, gpt-5 등)
            if not openai_api_key:
                raise ValueError(
                    f"OpenAI 모델({model_name})을 사용하려면 OPENAI_API_KEY가 필요합니다.\n"
                    ".env 파일에 'OPENAI_API_KEY=your-key' 형식으로 추가하세요."
                )
            mllm_instances.append(mLLM.multimodalLLM(llm_name=model_name, api_key=openai_api_key))
    
    # ========================================
    # 비디오 파일 설정
    # ========================================
    base_dir = r"/workspaces/AI_inhaler/app_SMI_type1/video_source/"
    video_options = {
        "video1": base_dir + r"SMI-6 Respimat.MOV",
        "video2": base_dir + r"SMI-8 Respimat.mp4",
    }

    video_path = video_options["video1"]
    
    print(f"\n분석할 비디오: {video_path}")
    
    # ========================================
    # 워크플로우 실행
    # ========================================
    # 첫 번째 모델의 API 키를 전달 (혼합 사용 시 주의 필요)
    first_model_api_key = google_api_key if "gemini" in llm_models[0] else openai_api_key
    
    initial_state = create_initial_state(
        video_path=video_path,
        llm_models=llm_models,
        api_key=first_model_api_key
    )
    
    workflow = create_workflow(mllm_instances, llm_models)
    final_state = workflow.run(initial_state)
    
    # ========================================
    # 결과 출력
    # ========================================
    if final_state["status"] == "completed":
        print("\n✅ 분석이 성공적으로 완료되었습니다!")
        
        if final_state.get("final_report"):
            report = final_state["final_report"]
            print(f"\n총 {report['summary']['total_actions_detected']}개의 행동이 감지되었습니다.")
        
        print(f"\n총 {len(final_state['agent_logs'])}개의 Agent 로그가 기록되었습니다.")
        
    else:
        print("\n❌ 분석 중 오류가 발생했습니다.")
        if final_state.get("errors"):
            print("오류 목록:")
            for error in final_state["errors"]:
                print(f"  - {error}")
    
    print("\n분석 완료!")
    return final_state


if __name__ == "__main__":
    final_state = main()

