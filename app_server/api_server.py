#!/usr/bin/env python
# coding: utf-8

"""
FastAPI 기반 백엔드 API 서버
프론트엔드와 백엔드 분석 로직을 연결합니다.
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# app_main 모듈 import, app_main.run_device_analysis() 함수 사용
from app_server import app_main

# 고정된 LLM 모델 설정
# "gpt-4.1", "gpt-5-nano", "gpt-5.1", "gpt-5.2"
# "gemini-2.5-pro", "gemini-3-flash-preview", "gemini-3-pro-preview"    
#FIXED_LLM_MODELS = ["gpt-4.1", "gpt-5.1", "gemini-2.5-pro", "gemini-3-flash-preview"]
FIXED_LLM_MODELS = ["gpt-4.1", "gpt-4.1"]

# ============================================
# FastAPI 앱 초기화
# ============================================
app = FastAPI(title="AI Inhaler Analysis API", version="1.0.0")

# CORS 설정 (프론트엔드와 통신)
# 원격 서버 환경을 위해 모든 origin 허용 (개발 환경)
# 프로덕션에서는 특정 origin만 허용하도록 변경 권장
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (원격 서버 지원)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 전역 상태 관리
# ============================================
# 분석 작업 저장소 (실제 운영에서는 DB 사용 권장)
analysis_storage: Dict[str, Dict[str, Any]] = {}

# 업로드된 비디오 저장 디렉토리
UPLOAD_DIR = Path(project_root) / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ============================================
# Pydantic 모델
# ============================================
class StartAnalysisRequest(BaseModel):
    videoId: str  # 프론트엔드와 일치
    deviceType: str  # 프론트엔드와 일치
    # llmModels는 제거됨 (항상 FIXED_LLM_MODELS 사용)
    saveIndividualReport: bool = False


class AnalysisStatusResponse(BaseModel):
    status: str  # 'pending' | 'processing' | 'completed' | 'error'
    progress: int  # 0-100
    current_stage: str
    logs: List[str]
    error: Optional[str] = None


# ============================================
# 데이터 변환 함수
# ============================================
def convert_backend_report_to_frontend(report: Dict[str, Any], final_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    백엔드 final_report를 프론트엔드 AnalysisResult 형식으로 변환
    print_analysis_summary의 출력 내용을 기반으로 변환
    """
    if not report:
        return {
            "status": "error",
            "deviceType": None,
            "videoInfo": None,
            "referenceTimes": None,
            "actionSteps": [],
            "summary": None,
            "modelInfo": None,
            "errors": final_state.get("errors", []),
            "finalSummary": None
        }
    
    video_info = report.get("video_info", {})
    action_decisions = report.get("action_decisions", {})
    action_order = report.get("action_order", [])
    action_analysis = report.get("action_analysis", {})
    final_summary = report.get("final_summary", "")
    
    # 비디오 정보 변환
    video_metadata = {
        "fileName": video_info.get("video_name", ""),
        "duration": video_info.get("play_time", 0),
        "size": 0,  # 백엔드에서 제공하지 않음
        "resolution": f"{video_info.get('video_width', 0)}x{video_info.get('video_height', 0)}",
        "type": "video/mp4",
        "width": video_info.get("video_width", 0),
        "height": video_info.get("video_height", 0),
        "frameCount": video_info.get("frame_count", 0)
    }
    
    # Action Steps 변환 (action_order 순서대로)
    action_steps = []
    for idx, action_key in enumerate(action_order):
        if action_key in action_decisions:
            decision = action_decisions[action_key]
            analysis = action_analysis.get(action_key, {})
            
            # 시간 정보 추출
            detected_times = analysis.get("detected_times", [])
            confidence_scores = analysis.get("confidence", {})
            
            # confidence를 [time, confidence] 형식으로 변환
            confidence_list = [
                [time, conf] 
                for time, conf in confidence_scores.items()
            ]
            
            action_steps.append({
                "id": action_key,
                "order": idx + 1,
                "name": action_key,
                "description": analysis.get("action_description", ""),
                "time": detected_times if detected_times else [],
                "score": [decision] if decision in [0, 1] else [],
                "confidenceScore": confidence_list,
                "result": "pass" if decision == 1 else "fail"
            })
    
    # action_order에 없는 키들도 추가
    for action_key, decision in action_decisions.items():
        if action_key not in action_order:
            analysis = action_analysis.get(action_key, {})
            detected_times = analysis.get("detected_times", [])
            confidence_scores = analysis.get("confidence", {})
            confidence_list = [
                [time, conf] 
                for time, conf in confidence_scores.items()
            ]
            
            action_steps.append({
                "id": action_key,
                "order": len(action_steps) + 1,
                "name": action_key,
                "description": analysis.get("action_description", ""),
                "time": detected_times if detected_times else [],
                "score": [decision] if decision in [0, 1] else [],
                "confidenceScore": confidence_list,
                "result": "pass" if decision == 1 else "fail"
            })
    
    # Summary 계산
    total_steps = len(action_steps)
    passed_steps = sum(1 for step in action_steps if step["result"] == "pass")
    score_percentage = (passed_steps / total_steps * 100) if total_steps > 0 else 0
    
    summary = {
        "totalSteps": total_steps,
        "passedSteps": passed_steps,
        "failedSteps": total_steps - passed_steps,
        "score": score_percentage
    }
    
    # Model Info (final_state에서 추출)
    llm_models = final_state.get("llm_models", [])
    analysis_duration = report.get("summary", {}).get("analysis_duration", 0)
    
    model_info = {
        "models": llm_models,
        "analysisTime": analysis_duration
    }
    
    # Reference Times (백엔드에서 제공하지 않으면 None)
    reference_times = None
    
    # Individual HTML paths (개별 Agent 시각화 HTML 파일 경로)
    individual_html_paths = report.get("individual_html_paths", [])
    
    return {
        "status": "completed",
        "deviceType": None,  # 요청에서 가져와야 함
        "videoInfo": video_metadata,
        "referenceTimes": reference_times,
        "actionSteps": action_steps,
        "summary": summary,
        "modelInfo": model_info,
        "errors": final_state.get("errors", []),
        "finalSummary": final_summary,  # 최종 종합 기술 추가
        "individualHtmlPaths": individual_html_paths  # 개별 Agent 시각화 HTML 파일 경로 추가
    }


# ============================================
# 비동기 분석 실행 함수
# ============================================
async def run_analysis_async(
    analysis_id: str,
    device_type: str,
    video_path: str,
    llm_models: List[str],
    save_individual_report: bool
):
    """
    백그라운드에서 분석을 실행하는 비동기 함수
    """
    try:
        # 상태 업데이트: processing
        analysis_storage[analysis_id]["status"] = "processing"
        analysis_storage[analysis_id]["current_stage"] = "분석 초기화 중..."
        analysis_storage[analysis_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] 분석 시작")
        
        # 동기 함수를 비동기로 실행 (별도 스레드에서)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: app_main.run_device_analysis(
                device_type=device_type,
                video_path=video_path,
                llm_models=llm_models,
                save_individual_report=save_individual_report
            )
        )
        
        if result and result.get("status") == "completed":
            # 성공
            analysis_storage[analysis_id]["status"] = "completed"
            analysis_storage[analysis_id]["progress"] = 100
            analysis_storage[analysis_id]["current_stage"] = "분석 완료"
            analysis_storage[analysis_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] 분석 완료")
            
            # 결과 저장
            analysis_storage[analysis_id]["result"] = convert_backend_report_to_frontend(
                result.get("final_report", {}),
                result
            )
            analysis_storage[analysis_id]["result"]["deviceType"] = device_type
            analysis_storage[analysis_id]["raw_result"] = result
        else:
            # 실패
            analysis_storage[analysis_id]["status"] = "error"
            analysis_storage[analysis_id]["error"] = "분석 중 오류가 발생했습니다."
            if result and result.get("errors"):
                analysis_storage[analysis_id]["error"] = "; ".join(result.get("errors", []))
            analysis_storage[analysis_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] 오류 발생")
    
    except Exception as e:
        # 예외 처리
        analysis_storage[analysis_id]["status"] = "error"
        analysis_storage[analysis_id]["error"] = str(e)
        analysis_storage[analysis_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()


# ============================================
# API 엔드포인트
# ============================================
@app.post("/api/video/upload")
async def upload_video(
    file: UploadFile = File(...),
    deviceType: str = None
):
    """
    비디오 파일 업로드
    """
    try:
        # 파일 저장
        video_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        saved_path = UPLOAD_DIR / f"{video_id}{file_extension}"
        
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 파일 메타데이터 (간단한 버전, 실제로는 비디오 정보 추출 필요)
        file_size = saved_path.stat().st_size
        
        return {
            "videoId": video_id,
            "thumbnail": "",  # 썸네일 생성 필요
            "metadata": {
                "fileName": file.filename,
                "duration": 0,  # 비디오 분석 필요
                "size": file_size,
                "resolution": "",
                "type": file.content_type,
                "width": 0,
                "height": 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@app.post("/api/analysis/start")
async def start_analysis(
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    분석 시작
    """
    try:
        analysis_id = str(uuid.uuid4())
        
        # 비디오 파일 경로 찾기
        video_file = None
        search_pattern = f"{request.videoId}.*"
        matching_files = list(UPLOAD_DIR.glob(search_pattern))
        
        for file in matching_files:
            if file.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                video_file = str(file)
                break
        
        if not video_file:
            # 디버깅 정보
            debug_info = f"UPLOAD_DIR: {UPLOAD_DIR}, videoId: {request.videoId}, 찾은 파일: {matching_files}"
            raise HTTPException(
                status_code=404, 
                detail=f"업로드된 비디오 파일을 찾을 수 없습니다. {debug_info}"
            )
        
        # 분석 작업 초기화
        analysis_storage[analysis_id] = {
            "status": "pending",
            "progress": 0,
            "current_stage": "대기 중...",
            "logs": [],
            "error": None,
            "result": None,
            "raw_result": None,
            "device_type": request.deviceType,
            "video_path": video_file
        }
        
        # 백그라운드 작업으로 분석 시작
        # llm_models는 고정값 사용 (요청의 llmModels는 무시)
        background_tasks.add_task(
            run_analysis_async,
            analysis_id,
            request.deviceType,
            video_file,
            FIXED_LLM_MODELS,  # 고정된 LLM 모델 사용 (요청의 llmModels 무시)
            request.saveIndividualReport
        )
        
        return {
            "analysisId": analysis_id,
            "estimatedTime": 300  # 예상 시간 (초) - 실제로는 계산 필요
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 시작 실패: {str(e)}")


@app.get("/api/analysis/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """
    분석 상태 조회
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    analysis = analysis_storage[analysis_id]
    
    return AnalysisStatusResponse(
        status=analysis["status"],
        progress=analysis["progress"],
        current_stage=analysis["current_stage"],
        logs=analysis["logs"],
        error=analysis.get("error")
    )


@app.get("/api/analysis/result/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """
    분석 결과 조회
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    analysis = analysis_storage[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="분석이 아직 완료되지 않았습니다.")
    
    if not analysis.get("result"):
        raise HTTPException(status_code=500, detail="분석 결과가 없습니다.")
    
    return analysis["result"]


@app.get("/api/analysis/download/{analysis_id}")
async def download_result(analysis_id: str, format: str = "json"):
    """
    분석 결과 다운로드
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    analysis = analysis_storage[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="분석이 아직 완료되지 않았습니다.")
    
    if format == "json":
        import json
        result = analysis.get("raw_result", analysis.get("result", {}))
        file_path = UPLOAD_DIR / f"{analysis_id}_result.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return FileResponse(
            file_path,
            media_type="application/json",
            filename=f"analysis_result_{analysis_id}.json"
        )
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {format}")


@app.get("/api/config")
async def get_config():
    """
    서버 설정 정보 반환
    """
    return {
        "llmModels": FIXED_LLM_MODELS,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    루트 엔드포인트
    """
    return {"message": "AI Inhaler Analysis API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

