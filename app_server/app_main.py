#!/usr/bin/env python
# coding: utf-8

"""
통합 흡입기 비디오 분석 애플리케이션
여러 디바이스 타입에 대해 통합적으로 분석을 수행합니다.
"""

import os
import sys
import importlib.util
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# app_server 디렉토리의 .env 파일 로드
app_server_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(app_server_dir, ".env")
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
    
    # 개별 Agent 시각화 HTML 파일 경로 출력
    if "individual_html_paths" in report and report["individual_html_paths"]:
        print(f"\n[개별 Agent 시각화 HTML 파일]")
        for idx, html_path in enumerate(report["individual_html_paths"], 1):
            print(f"  {idx}. {html_path}")
    
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
    
    # importlib.util을 사용하여 모듈을 파일 경로로 직접 로드 (캐싱 문제 방지)
    # 고유한 모듈 이름 사용 (device_type 포함하여 충돌 방지)
    module_prefix = f"app_{device_type.replace('-', '_')}"
    
    # 다른 app_* 경로들을 sys.path에서 임시 제거하여 경쟁 조건 방지
    # 모듈 로드 시 올바른 디바이스 타입의 모듈만 사용하도록 보장
    original_sys_path = sys.path.copy()
    other_app_paths = [p for p in sys.path if os.path.basename(p).startswith('app_') and p != app_dir]
    for path in other_app_paths:
        if path in sys.path:
            sys.path.remove(path)
    
    # agents 모듈의 상대 import를 지원하기 위해 app_dir을 sys.path 맨 앞에 추가
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    elif sys.path.index(app_dir) != 0:
        # 이미 있지만 맨 앞이 아니면 맨 앞으로 이동
        sys.path.remove(app_dir)
        sys.path.insert(0, app_dir)
    
    try:
        # 1. agents.state 모듈 로드
        agents_state_path = os.path.join(app_dir, "agents", "state.py")
        if not os.path.exists(agents_state_path):
            raise FileNotFoundError(f"agents/state.py 파일을 찾을 수 없습니다: {agents_state_path}")
        
        agents_state_spec = importlib.util.spec_from_file_location(
            f"{module_prefix}.agents.state", 
            agents_state_path
        )
        agents_state_module = importlib.util.module_from_spec(agents_state_spec)
        # 고유한 모듈 이름과 일반 이름 모두 등록
        # graph_workflow가 "from agents.state import ..."를 사용할 수 있도록
        sys.modules[f"{module_prefix}.agents.state"] = agents_state_module
        sys.modules["agents.state"] = agents_state_module
        agents_state_spec.loader.exec_module(agents_state_module)
        create_initial_state = agents_state_module.create_initial_state
        
        # graph_workflow가 agents 모듈을 import하기 전에 기존 agents 모듈 캐시 제거
        # graph_workflow는 "from agents.xxx import ..."를 사용하므로, 
        # sys.modules에 있는 기존 agents 모듈들이 재사용되지 않도록 제거
        agents_modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            # agents 패키지와 관련된 모든 모듈 제거
            # 단, 방금 로드한 module_prefix.agents.state는 제외
            if (module_name.startswith('agents.') or 
                module_name == 'agents' or
                (module_name.startswith('app_') and 'agents' in module_name and module_name != f"{module_prefix}.agents.state")):
                agents_modules_to_remove.append(module_name)
        
        for module_name in agents_modules_to_remove:
            del sys.modules[module_name]
        
        # sys.path 격리 상태 재확인 (graph_workflow 로드 전)
        current_other_app_paths = [p for p in sys.path if os.path.basename(p).startswith('app_') and p != app_dir]
        for path in current_other_app_paths:
            if path in sys.path:
                sys.path.remove(path)
        
        if app_dir not in sys.path or sys.path.index(app_dir) != 0:
            if app_dir in sys.path:
                sys.path.remove(app_dir)
            sys.path.insert(0, app_dir)
        
        # agents 패키지 자체를 올바른 경로에서 미리 로드
        # graph_workflow가 "from agents.xxx import ..."를 실행할 때 올바른 패키지를 사용하도록
        agents_init_path = os.path.join(app_dir, "agents", "__init__.py")
        if os.path.exists(agents_init_path):
            # agents 패키지를 sys.modules에 등록 (graph_workflow의 import를 위해)
            agents_pkg_spec = importlib.util.spec_from_file_location(
                "agents",
                agents_init_path
            )
            agents_pkg = importlib.util.module_from_spec(agents_pkg_spec)
            sys.modules["agents"] = agents_pkg
            sys.modules[f"{module_prefix}.agents"] = agents_pkg
            agents_pkg_spec.loader.exec_module(agents_pkg)
            
            # agents의 하위 모듈들도 미리 로드하여 올바른 모듈이 사용되도록 보장
            agents_modules = [
                ("agents.reporter_agent", "reporter_agent.py"),
                ("agents.video_processor_agent", "video_processor_agent.py"),
                ("agents.video_analyzer_agent", "video_analyzer_agent.py"),
            ]
            
            for module_name, filename in agents_modules:
                module_path = os.path.join(app_dir, "agents", filename)
                if os.path.exists(module_path):
                    module_spec = importlib.util.spec_from_file_location(
                        module_name,
                        module_path
                    )
                    module = importlib.util.module_from_spec(module_spec)
                    # 일반 이름과 고유한 이름 모두 등록
                    sys.modules[module_name] = module
                    sys.modules[f"{module_prefix}.{module_name}"] = module
                    module_spec.loader.exec_module(module)
        
        # 2. graph_workflow 모듈 로드
        # graph_workflow는 agents 모듈을 import하므로, sys.path 격리 상태에서 로드해야 함
        graph_workflow_path = os.path.join(app_dir, "graph_workflow.py")
        if not os.path.exists(graph_workflow_path):
            raise FileNotFoundError(f"graph_workflow.py 파일을 찾을 수 없습니다: {graph_workflow_path}")
        
        graph_workflow_spec = importlib.util.spec_from_file_location(
            f"{module_prefix}.graph_workflow",
            graph_workflow_path
        )
        graph_workflow_module = importlib.util.module_from_spec(graph_workflow_spec)
        # 고유한 모듈 이름으로 등록하여 다른 device_type과 충돌 방지
        sys.modules[f"{module_prefix}.graph_workflow"] = graph_workflow_module
        graph_workflow_spec.loader.exec_module(graph_workflow_module)
        create_workflow = graph_workflow_module.create_workflow
        
        # 3. app_server 모듈은 공통이므로 일반 import 사용
        from app_server import class_MultimodalLLM_QA_251107 as mLLM
        
        print(f"[모듈 로드] {device_type} 모듈을 독립적으로 로드했습니다.")
        print(f"  - agents.state: {agents_state_path}")
        print(f"  - graph_workflow: {graph_workflow_path}")
        
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
        
        # app_dir 정보를 initial_state에 추가 (reporter_agent가 올바른 경로를 사용하도록)
        # TypedDict에 없는 필드이지만 런타임에는 문제없음
        initial_state["app_dir"] = app_dir
        
        # 워크플로우 생성
        workflow = create_workflow(mllm_instances, llm_models)
        
        # 워크플로우 실행 전에 sys.path 격리 상태 확인 및 유지
        # 다른 app_* 경로가 다시 추가되었는지 확인하고 제거
        current_other_app_paths = [p for p in sys.path if os.path.basename(p).startswith('app_') and p != app_dir]
        for path in current_other_app_paths:
            if path in sys.path:
                sys.path.remove(path)
        
        # app_dir이 맨 앞에 있는지 확인
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        elif sys.path.index(app_dir) != 0:
            sys.path.remove(app_dir)
            sys.path.insert(0, app_dir)
        
        # 워크플로우 실행 (sys.path 격리 상태 유지)
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
        # 로드한 모듈을 sys.modules에서 제거 (메모리 정리 및 다음 요청을 위한 준비)
        # 단, app_server 모듈은 공통이므로 제거하지 않음
        modules_to_remove = [
            f"{module_prefix}.agents.state",
            f"{module_prefix}.graph_workflow"
        ]
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # agents 패키지 관련 모듈도 제거 (상대 import로 로드된 모듈들)
        agents_modules_to_remove = [
            f"{module_prefix}.agents",
            f"{module_prefix}.agents.video_processor_agent",
            f"{module_prefix}.agents.video_analyzer_agent",
            f"{module_prefix}.agents.reporter_agent",
        ]
        for module_name in agents_modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # sys.path 복원: 다른 app_* 경로들을 다시 추가
        # 단, app_dir은 제거 (다음 요청을 위해)
        if app_dir in sys.path:
            sys.path.remove(app_dir)
        
        # 원래 있던 다른 app_* 경로들을 복원
        for path in other_app_paths:
            if path not in sys.path:
                # 원래 위치에 가깝게 복원 (하지만 정확한 위치는 보장하지 않음)
                sys.path.append(path)


def main():
    """
    메인 실행 함수
    """
    # ========================================
    # 사용자 지정 변수
    # ========================================
    video_path = r"/workspaces/AI_inhaler/app_server/test_clip.mp4"
    device_list = ['pMDI_type1', 'pMDI_type2', 'DPI_type1', 'DPI_type2', 'DPI_type3', 'SMI_type1']
    device_type = device_list[1]

    # "gpt-4.1", "gpt-5-nano", "gpt-5.1", "gpt-5.2"
    # "gemini-2.5-pro", "gemini-3-flash-preview", "gemini-3-pro-preview"
    #set_llm_models = ['gpt-4.1', 'gpt-5.1', 'gemini-2.5-pro', 'gemini-3-flash-preview']
    set_llm_models = ['gpt-4.1', 'gpt-4.1']
    save_individual_report = True  # 개별 리포트 저장 여부 (True: 저장, False: 저장하지 않기)
    
    result = run_device_analysis(
        device_type=device_type,
        video_path=video_path,
        llm_models=set_llm_models,
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

