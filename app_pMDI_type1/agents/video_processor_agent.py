#!/usr/bin/env python
# coding: utf-8

"""
Video Processor Agent
비디오 메타데이터 추출 및 전처리를 담당합니다.
"""

import sys
import os
# app_server 모듈 경로 추가 (상위 2단계 디렉토리)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..'))

from app_server import class_Media_Edit_251107 as ME
from .state import VideoAnalysisState


class VideoProcessorAgent:
    """
    비디오 처리 전담 Agent
    - 비디오 메타데이터 추출
    - 프레임 샘플링 및 전처리
    - 이미지 그리드 생성
    """
    
    def __init__(self):
        self.video_edit = ME.MediaEdit()
        self.name = "VideoProcessorAgent"
    
    def process(self, state: VideoAnalysisState) -> VideoAnalysisState:
        """
        비디오 정보를 추출하고 상태에 저장
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        try:
            video_path = state["video_path"]
            
            # 로그 추가
            state["agent_logs"].append({
                "agent": self.name,
                "action": "start_processing",
                "message": f"비디오 파일 처리 시작: {video_path}"
            })
            
            # 비디오 정보 추출
            video_name, play_time, frame_count, video_width, video_height, file_size = \
                self.video_edit.query_videoInfo(video_path)
            
            if video_name is None:
                raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
            
            # 비디오 정보를 상태에 저장
            state["video_info"] = {
                "video_name": video_name,
                "play_time": play_time,
                "frame_count": frame_count,
                "video_width": video_width,
                "video_height": video_height,
                "file_size": file_size
            }
            
            # 상태 업데이트
            state["status"] = "video_processed"
            
            # 로그 추가
            state["agent_logs"].append({
                "agent": self.name,
                "action": "processing_complete",
                "message": f"비디오 정보 추출 완료: {video_name}, {play_time}초, {frame_count}프레임, {video_width}x{video_height}px"
            })
            
            print(f"[{self.name}] 비디오 정보: {video_name}, {play_time}초, {frame_count}프레임")
            
        except Exception as e:
            error_msg = f"[{self.name}] 비디오 처리 중 오류: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = "error"
            print(error_msg)
        
        return state
    
    def extract_frames(self, video_path: str, start_time: float, end_time: float, 
                      M: int, N: int, gridSize: tuple = (640, 360), padSize: tuple = (0, 0)):
        """
        비디오에서 프레임을 추출하여 MxN 그리드 이미지로 생성
        
        Args:
            video_path: 비디오 파일 경로
            start_time: 시작 시간 (초)
            end_time: 종료 시간 (초)
            M: 행 수
            N: 열 수
            gridSize: 그리드 크기
            padSize: 패딩 크기
            
        Returns:
            output_image: 생성된 이미지 배열
            image_W: 이미지 너비
            image_H: 이미지 높이
        """
        output_image, image_W, image_H = self.video_edit.extract_frames_to_MxN_image(
            option='time',
            start=start_time,
            end=end_time,
            MxN=(M, N),
            video_path=video_path,
            output_dir=None,  # None이면 image_array를 반환
            gridSize=gridSize,
            padSize=padSize
        )
        
        return output_image, image_W, image_H

