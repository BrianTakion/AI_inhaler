#!/usr/bin/env python
# coding: utf-8

"""
LangGraph Workflow 정의
Multi-Agent 워크플로우를 구성합니다. (동적 모델 지원)
"""

from langgraph.graph import StateGraph, END
from agents.state import VideoAnalysisState
from agents.video_processor_agent import VideoProcessorAgent
from agents.video_analyzer_agent import VideoAnalyzerAgent
from agents.reporter_agent import ReporterAgent


class InhalerAnalysisWorkflow:
    """
    흡입기 비디오 분석 워크플로우 (동적 모델 지원)
    
    워크플로우:
    1. VideoProcessor: 비디오 메타데이터 추출
    2. VideoAnalyzer (병렬):
       - 리스트로 지정된 모델 개수만큼 병렬 실행
    3. Reporter: 결과 취합 및 평균값 시각화
    """
    
    def __init__(self, mllm_instances: list, llm_models: list):
        """
        워크플로우 초기화
        
        Args:
            mllm_instances: Multimodal LLM 인스턴스 리스트
            llm_models: 사용할 LLM 모델 이름 리스트 (예: ["gpt-4o", "gpt-4o-mini", ...])
        """
        if len(mllm_instances) != len(llm_models):
            raise ValueError("mllm_instances와 llm_models의 개수가 일치해야 합니다.")
        
        self.mllm_instances = mllm_instances
        self.llm_models = llm_models
        
        # Agent 초기화
        self.video_processor = VideoProcessorAgent()
        
        # 동적으로 VideoAnalyzerAgent 생성
        self.video_analyzers = []
        self.analyzer_nodes = {}
        for idx, (mllm, model_name) in enumerate(zip(mllm_instances, llm_models)):
            model_id = f"{model_name}_{idx}"
            analyzer = VideoAnalyzerAgent(mllm, self.video_processor, model_id, model_name)
            self.video_analyzers.append(analyzer)
            self.analyzer_nodes[model_id] = analyzer
        
        self.reporter = ReporterAgent()
        
        # 워크플로우 그래프 생성
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
    
    def _create_workflow(self):
        """LangGraph 워크플로우 생성 (병렬 처리, 동적 노드)"""
        
        # StateGraph 생성
        workflow = StateGraph(VideoAnalysisState)
        
        # 1. VideoProcessor 노드 추가
        workflow.add_node("video_processor", self._video_processor_node)
        
        # 2. 동적으로 VideoAnalyzer 노드들 추가
        for model_id, analyzer in self.analyzer_nodes.items():
            node_name = f"video_analyzer_{model_id}"
            workflow.add_node(node_name, self._create_analyzer_node(analyzer, model_id))
        
        # 3. Reporter 노드 추가
        workflow.add_node("reporter", self._reporter_node)
        
        # 엣지 추가 (워크플로우 순서)
        workflow.set_entry_point("video_processor")
        
        # 병렬 실행: video_processor -> 모든 analyzer가 병렬로 실행
        for model_id in self.analyzer_nodes.keys():
            node_name = f"video_analyzer_{model_id}"
            workflow.add_edge("video_processor", node_name)
        
        # 모든 analyzer 결과를 reporter로 전달
        for model_id in self.analyzer_nodes.keys():
            node_name = f"video_analyzer_{model_id}"
            workflow.add_edge(node_name, "reporter")
        
        workflow.add_edge("reporter", END)
        
        return workflow
    
    def _video_processor_node(self, state: VideoAnalysisState) -> VideoAnalysisState:
        """비디오 처리 노드"""
        print("\n" + "="*50)
        print("=== 1. Video Processor Agent 실행 ===")
        print("="*50)
        return self.video_processor.process(state)
    
    def _create_analyzer_node(self, analyzer, model_id):
        """동적으로 Analyzer 노드 함수 생성"""
        def analyzer_node(state: VideoAnalysisState) -> VideoAnalysisState:
            print("\n" + "="*50)
            print(f"=== 2. Video Analyzer Agent ({model_id}) 실행 ===")
            print("="*50)
            return analyzer.process(state)
        return analyzer_node
    
    def _reporter_node(self, state: VideoAnalysisState) -> VideoAnalysisState:
        """리포트 생성 노드"""
        print("\n" + "="*50)
        print("=== 3. Reporter Agent 실행 ===")
        print("="*50)
        return self.reporter.process(state)
    
    def run(self, initial_state: VideoAnalysisState) -> VideoAnalysisState:
        """
        워크플로우 실행
        
        Args:
            initial_state: 초기 상태
            
        Returns:
            최종 상태
        """
        print("\n" + "#"*50)
        print("### LangGraph Multi-Agent 워크플로우 시작 ###")
        print("#"*50)
        
        # 워크플로우 실행
        final_state = self.app.invoke(initial_state)
        
        print("\n" + "#"*50)
        print("### LangGraph Multi-Agent 워크플로우 완료 ###")
        print("#"*50)
        
        # 에러 확인
        if final_state.get("errors"):
            print("\n[경고] 다음 오류가 발생했습니다:")
            for error in final_state["errors"]:
                print(f"  - {error}")
        
        return final_state
    
    def visualize_workflow(self, output_path: str = "workflow_diagram.png"):
        """
        워크플로우 다이어그램 생성 (선택적)
        
        Args:
            output_path: 출력 파일 경로
        """
        try:
            from IPython.display import Image, display
            
            # 워크플로우 시각화
            display(Image(self.app.get_graph().draw_mermaid_png()))
            print(f"워크플로우 다이어그램이 생성되었습니다.")
        except Exception as e:
            print(f"워크플로우 시각화 실패: {e}")


def create_workflow(mllm_instances: list, llm_models: list) -> InhalerAnalysisWorkflow:
    """
    워크플로우 생성 헬퍼 함수
    
    Args:
        mllm_instances: Multimodal LLM 인스턴스 리스트
        llm_models: 사용할 LLM 모델 이름 리스트 (예: ["gpt-4o", "gpt-4o-mini", ...])
        
    Returns:
        InhalerAnalysisWorkflow 인스턴스
    """
    return InhalerAnalysisWorkflow(mllm_instances, llm_models)

