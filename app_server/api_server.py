#!/usr/bin/env python
# coding: utf-8

"""
FastAPI 기반 백엔드 API 서버
프론트엔드와 백엔드 분석 로직을 연결합니다.

[다중 사용자 지원]
- multiprocessing을 사용하여 각 분석 요청을 별도 프로세스에서 실행
- sys.path 오염 및 경쟁 조건 방지
- 동시 분석 제한 (Semaphore)
- 프로세스 타임아웃
- 파일 검증 및 정리 스케줄러
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import shutil
import multiprocessing
from multiprocessing import Process, Queue
import queue as queue_module  # for queue.Empty exception
import traceback
import threading
import time
import signal

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 주의: app_main은 별도 프로세스에서 import됨 (프로세스 격리)
# from app_server import app_main  # 직접 import 제거

# ============================================
# PID 파일 관리 및 프로세스 정리
# ============================================
PID_FILE = Path(project_root) / "api_server.pid"


def write_pid_file():
    """현재 프로세스의 PID를 파일에 기록"""
    PID_FILE.write_text(str(os.getpid()))
    print(f"[PID] 파일 생성: {PID_FILE} (PID: {os.getpid()})")


def remove_pid_file():
    """PID 파일 삭제"""
    try:
        if PID_FILE.exists() and int(PID_FILE.read_text().strip()) == os.getpid():
            PID_FILE.unlink(missing_ok=True)
            print(f"[PID] 파일 삭제: {PID_FILE}")
    except (ValueError, OSError):
        PID_FILE.unlink(missing_ok=True)


def kill_previous_instance():
    """이전에 실행 중인 api_server 인스턴스가 있으면 종료"""
    if not PID_FILE.exists():
        return

    try:
        old_pid = int(PID_FILE.read_text().strip())
        if old_pid == os.getpid():
            return

        # 프로세스가 실제로 존재하는지 확인
        os.kill(old_pid, 0)

        # 존재하면 SIGTERM 전송
        print(f"[정리] 이전 인스턴스 종료 시도 (PID: {old_pid})")
        os.kill(old_pid, signal.SIGTERM)
        time.sleep(3)

        # 아직 살아있으면 SIGKILL
        try:
            os.kill(old_pid, 0)
            print(f"[정리] SIGTERM 무응답, 강제 종료 (PID: {old_pid})")
            os.kill(old_pid, signal.SIGKILL)
            time.sleep(1)
        except ProcessLookupError:
            pass  # 정상 종료됨

        print(f"[정리] 이전 인스턴스 정리 완료 (PID: {old_pid})")

    except (ProcessLookupError, ValueError):
        pass  # 이미 종료되었거나 잘못된 PID
    except OSError as e:
        print(f"[정리] 이전 인스턴스 정리 중 오류: {e}")
    finally:
        PID_FILE.unlink(missing_ok=True)


def cleanup_child_processes():
    """활성 자식 프로세스(multiprocessing)를 모두 종료"""
    children = multiprocessing.active_children()
    if not children:
        return
    print(f"[정리] 자식 프로세스 {len(children)}개 종료 중...")
    for child in children:
        child.terminate()
    # 일괄 join
    for child in children:
        child.join(timeout=5)
    # 아직 살아있는 프로세스 강제 종료
    for child in multiprocessing.active_children():
        print(f"[정리] 자식 프로세스 강제 종료 (PID: {child.pid})")
        child.kill()


def graceful_shutdown(signum, frame):
    """시그널 수신 시 자식 프로세스 정리 후 종료"""
    sig_name = signal.Signals(signum).name
    print(f"\n[종료] 시그널 {sig_name}({signum}) 수신, 정리 중...")
    cleanup_child_processes()
    remove_pid_file()
    sys.exit(0)


# 고정된 LLM 모델 설정
# "gpt-4.1", "gpt-5-nano", "gpt-5.1", "gpt-5.2"
# "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro" (2026.06.17 종료 예정)
# "gemini-3-flash-preview", "gemini-3-pro-preview" (최신)
#FIXED_LLM_MODELS = ["gpt-4.1", "gpt-5.1", "gemini-2.5-pro", "gemini-3-flash-preview"]
#FIXED_LLM_MODELS = ["gpt-4.1", "gpt-4.1", "gemini-3-flash-preview", "gemini-3-flash-preview"]
FIXED_LLM_MODELS = ["gpt-4.1", "gpt-4.1"]

# ============================================
# 자원 제한 및 파일 관리 설정
# ============================================
# 동시 분석 제한
MAX_CONCURRENT_ANALYSES = 5

# 프로세스 타임아웃 (초)
PROCESS_TIMEOUT = 3600  # 1시간

# 파일 업로드 제한
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}

# 파일 정리 스케줄러 설정
CLEANUP_OLD_FILES_DURATION = 24  # 24 hours

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

# 동시 분석 제한을 위한 Semaphore
analysis_semaphore: Optional[asyncio.Semaphore] = None

def get_analysis_semaphore() -> asyncio.Semaphore:
    """
    asyncio Semaphore를 lazy 초기화하여 반환
    (이벤트 루프가 실행 중일 때만 생성 가능)
    """
    global analysis_semaphore
    if analysis_semaphore is None:
        analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)
    return analysis_semaphore

# 현재 진행 중인 분석 수 추적
current_analysis_count = 0
analysis_count_lock = threading.Lock()

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
# 프로세스 격리 기반 분석 실행 함수
# ============================================
def _run_analysis_in_process(result_queue: Queue, device_type: str, video_path: str, llm_models: List[str], save_individual_report: bool):
    """
    별도 프로세스에서 분석을 실행하는 함수

    [프로세스 격리 장점]
    - 각 프로세스는 독립적인 sys.path, sys.modules 보유
    - 동시에 서로 다른 device_type 분석해도 충돌 없음
    - 메모리 격리로 상태 오염 방지

    Args:
        result_queue: 결과 전달용 큐
        device_type: 디바이스 타입
        video_path: 비디오 파일 경로
        llm_models: LLM 모델 리스트
        save_individual_report: 개별 리포트 저장 여부
    """
    try:
        # 프로세스 내에서 app_main import (격리된 환경)
        from app_server import app_main

        result = app_main.run_device_analysis(
            device_type=device_type,
            video_path=video_path,
            llm_models=llm_models,
            save_individual_report=save_individual_report
        )

        # 결과를 큐에 전달
        result_queue.put({
            "success": True,
            "result": result
        })
    except Exception as e:
        # 예외 발생 시 에러 정보 전달
        result_queue.put({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })


def _run_analysis_with_process_isolation(device_type: str, video_path: str, llm_models: List[str], save_individual_report: bool) -> Dict[str, Any]:
    """
    multiprocessing을 사용하여 프로세스 격리된 환경에서 분석 실행

    이 함수는 동기 함수로, run_in_executor에서 호출됩니다.
    별도 프로세스를 생성하여 분석을 실행하고 결과를 반환합니다.

    [프로세스 타임아웃]
    - PROCESS_TIMEOUT 초 후에 프로세스를 강제 종료
    - terminate() 후 10초 대기, 그래도 살아있으면 kill()

    [FIX] Queue Deadlock 방지:
    - 기존: process.join() → result_queue.get() (Deadlock 위험!)
    - 수정: result_queue.get(timeout) → process.join() (Python 공식 문서 권장)
    - 원인: 자식 프로세스가 Queue.put()으로 큰 데이터를 넣으면 파이프 버퍼가 차서
      put()이 블로킹됨. 이때 부모가 process.join()으로 기다리면 교착상태 발생.
      긴 비디오일수록 결과 데이터가 커져 이 문제가 발생할 확률이 높음.

    Args:
        device_type: 디바이스 타입
        video_path: 비디오 파일 경로
        llm_models: LLM 모델 리스트
        save_individual_report: 개별 리포트 저장 여부

    Returns:
        분석 결과 딕셔너리
    """
    # 결과 전달용 큐 생성
    result_queue = Queue()

    # 별도 프로세스에서 분석 실행
    process = Process(
        target=_run_analysis_in_process,
        args=(result_queue, device_type, video_path, llm_models, save_individual_report)
    )

    print(f"[프로세스 격리] 분석 프로세스 시작 (device_type: {device_type}, PID: {os.getpid()}, timeout: {PROCESS_TIMEOUT}s)")
    process.start()

    # [FIX] Queue에서 결과를 먼저 읽고, 그 후에 process.join()을 호출
    # Python 공식 문서: "a process that puts items on a queue will wait before
    # terminating until all the buffered items are fed by the 'feeder' thread to
    # the underlying pipe. You should join the process AFTER you have consumed all
    # items from the queue."
    queue_result = None
    try:
        queue_result = result_queue.get(timeout=PROCESS_TIMEOUT)
    except queue_module.Empty:
        # 타임아웃: 결과가 오지 않음
        print(f"[프로세스 격리] 타임아웃 ({PROCESS_TIMEOUT}s) - Queue에서 결과를 받지 못함 (device_type: {device_type})")

        # 프로세스가 아직 살아있으면 강제 종료
        if process.is_alive():
            print(f"[프로세스 격리] 프로세스 강제 종료 시도 (device_type: {device_type})")
            process.terminate()
            process.join(timeout=10)

            if process.is_alive():
                print(f"[프로세스 격리] terminate 실패, kill 시도 (device_type: {device_type})")
                process.kill()
                process.join(timeout=5)

        return {
            "status": "error",
            "errors": [f"분석 시간 초과 ({PROCESS_TIMEOUT}초). 프로세스가 강제 종료되었습니다."]
        }
    except Exception as e:
        traceback.print_exc()

        if process.is_alive():
            process.terminate()
            process.join(timeout=10)

        return {
            "status": "error",
            "errors": [f"결과 수신 중 오류: {str(e)}"]
        }

    # Queue에서 결과를 읽었으므로 이제 안전하게 process.join() 호출
    process.join(timeout=30)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)

    # 결과 처리
    if queue_result is None:
        print(f"[프로세스 격리] 프로세스 비정상 종료 (exit_code: {process.exitcode})")
        return {
            "status": "error",
            "errors": [f"분석 프로세스가 비정상 종료됨 (exit_code: {process.exitcode})"]
        }

    if queue_result.get("success"):
        print(f"[프로세스 격리] 분석 완료 (device_type: {device_type})")
        return queue_result.get("result")
    else:
        # 에러 발생
        error_msg = queue_result.get("error", "알 수 없는 오류")
        tb = queue_result.get("traceback", "")
        print(f"[프로세스 격리] 분석 오류: {error_msg}")
        if tb:
            print(tb)
        return {
            "status": "error",
            "errors": [error_msg]
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
    
    [다중 사용자 지원]
    - multiprocessing으로 프로세스 격리하여 분석 실행
    - 각 분석은 독립적인 프로세스에서 실행됨
    - sys.path, sys.modules 오염 없음
    
    [동시 분석 제한]
    - Semaphore를 사용하여 동시 분석 수 제한 (MAX_CONCURRENT_ANALYSES)
    """
    global current_analysis_count
    
    # Semaphore 획득 대기
    semaphore = get_analysis_semaphore()
    
    # 대기 상태 로그
    with analysis_count_lock:
        waiting_count = MAX_CONCURRENT_ANALYSES - semaphore._value if hasattr(semaphore, '_value') else current_analysis_count
    
    if waiting_count >= MAX_CONCURRENT_ANALYSES:
        analysis_storage[analysis_id]["current_stage"] = f"대기 중... (동시 분석 제한: {MAX_CONCURRENT_ANALYSES}개)"
        analysis_storage[analysis_id]["logs"].append(
            f"[{datetime.now().strftime('%H:%M:%S')}] 동시 분석 제한으로 대기 중 (현재 {waiting_count}개 실행 중)"
        )
    
    async with semaphore:
        # 현재 분석 수 증가
        with analysis_count_lock:
            current_analysis_count += 1
            print(f"[동시 분석 제한] 분석 시작 (현재 {current_analysis_count}/{MAX_CONCURRENT_ANALYSES}개)")
        
        try:
            # 상태 업데이트: processing
            analysis_storage[analysis_id]["status"] = "processing"
            analysis_storage[analysis_id]["current_stage"] = "분석 초기화 중..."
            analysis_storage[analysis_id]["logs"].append(
                f"[{datetime.now().strftime('%H:%M:%S')}] 분석 시작 (device_type: {device_type}, 프로세스 격리 모드, 타임아웃: {PROCESS_TIMEOUT}s)"
            )
            
            # 프로세스 격리된 환경에서 분석 실행
            # run_in_executor로 비동기 래핑 (블로킹 방지)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                _run_analysis_with_process_isolation,
                device_type,
                video_path,
                llm_models,
                save_individual_report
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
            traceback.print_exc()
        
        finally:
            # 현재 분석 수 감소
            with analysis_count_lock:
                current_analysis_count -= 1
                print(f"[동시 분석 제한] 분석 종료 (현재 {current_analysis_count}/{MAX_CONCURRENT_ANALYSES}개)")


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
    
    [파일 검증]
    - 확장자 검증: ALLOWED_EXTENSIONS (.mp4, .mov, .avi, .mkv)
    - 파일 크기 검증: MAX_FILE_SIZE (500MB)
    """
    try:
        # 1. 확장자 검증
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 2. 파일 크기 검증 (스트리밍 방식으로 읽어서 검증)
        video_id = str(uuid.uuid4())
        saved_path = UPLOAD_DIR / f"{video_id}{file_extension}"
        
        # 파일을 청크 단위로 저장하면서 크기 검증
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB 청크
        
        with open(saved_path, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                
                # 크기 초과 시 파일 삭제 후 에러 반환
                if total_size > MAX_FILE_SIZE:
                    buffer.close()
                    saved_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"파일 크기가 너무 큽니다. 최대 허용 크기: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
                    )
                
                buffer.write(chunk)
        
        print(f"[파일 업로드] 성공: {file.filename} ({total_size / (1024*1024):.2f}MB)")
        
        return {
            "videoId": video_id,
            "thumbnail": "",  # 썸네일 생성 필요
            "metadata": {
                "fileName": file.filename,
                "duration": 0,  # 비디오 분석 필요
                "size": total_size,
                "resolution": "",
                "type": file.content_type,
                "width": 0,
                "height": 0
            }
        }
    
    except HTTPException:
        raise
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


# ============================================
# 파일 정리 스케줄러
# ============================================
def cleanup_old_files():
    """
    오래된 파일을 정리하는 함수
    
    [정리 대상]
    - uploads/ 디렉토리의 오래된 비디오 파일
    - uploads/ 디렉토리의 오래된 결과 JSON 파일
    
    [정리 기준]
    - CLEANUP_OLD_FILES_DURATION 시간(기본 24시간)보다 오래된 파일
    """
    try:
        cutoff = datetime.now() - timedelta(hours=CLEANUP_OLD_FILES_DURATION)
        cutoff_timestamp = cutoff.timestamp()
        
        deleted_count = 0
        deleted_size = 0
        
        # uploads 디렉토리 정리
        if UPLOAD_DIR.exists():
            for file in UPLOAD_DIR.iterdir():
                if file.is_file():
                    try:
                        file_mtime = file.stat().st_mtime
                        if file_mtime < cutoff_timestamp:
                            file_size = file.stat().st_size
                            file.unlink()
                            deleted_count += 1
                            deleted_size += file_size
                            print(f"[파일 정리] 삭제: {file.name} (생성: {datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')})")
                    except Exception as e:
                        print(f"[파일 정리] 삭제 실패: {file.name} - {e}")
        
        if deleted_count > 0:
            print(f"[파일 정리] 완료: {deleted_count}개 파일 삭제 ({deleted_size / (1024*1024):.2f}MB)")
        else:
            print(f"[파일 정리] 삭제할 파일 없음 (기준: {CLEANUP_OLD_FILES_DURATION}시간 이상)")
            
    except Exception as e:
        print(f"[파일 정리] 오류 발생: {e}")


def run_cleanup_scheduler():
    """
    파일 정리 스케줄러 실행 (백그라운드 스레드)
    
    [실행 주기]
    - 1시간마다 cleanup_old_files() 실행
    """
    print(f"[파일 정리 스케줄러] 시작 (정리 기준: {CLEANUP_OLD_FILES_DURATION}시간, 실행 주기: 1시간)")
    
    while True:
        try:
            # 1시간 대기
            time.sleep(3600)
            
            # 파일 정리 실행
            print(f"[파일 정리 스케줄러] 정리 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            cleanup_old_files()
            
        except Exception as e:
            print(f"[파일 정리 스케줄러] 오류: {e}")
            # 오류 발생해도 계속 실행
            time.sleep(60)


# 서버 시작 시 스케줄러 실행
cleanup_scheduler_thread: Optional[threading.Thread] = None

def start_cleanup_scheduler():
    """
    파일 정리 스케줄러를 백그라운드 스레드로 시작
    """
    global cleanup_scheduler_thread
    
    if cleanup_scheduler_thread is None or not cleanup_scheduler_thread.is_alive():
        cleanup_scheduler_thread = threading.Thread(
            target=run_cleanup_scheduler,
            daemon=True,  # 메인 프로세스 종료 시 함께 종료
            name="FileCleanupScheduler"
        )
        cleanup_scheduler_thread.start()
        print("[파일 정리 스케줄러] 백그라운드 스레드 시작됨")


@app.on_event("startup")
async def startup_event():
    """
    서버 시작 시 실행되는 이벤트 핸들러
    """
    print("=" * 60)
    print("AI Inhaler Analysis API 서버 시작")
    print("=" * 60)
    print(f"[설정] 동시 분석 제한: {MAX_CONCURRENT_ANALYSES}개")
    print(f"[설정] 프로세스 타임아웃: {PROCESS_TIMEOUT}초 ({PROCESS_TIMEOUT/60:.0f}분)")
    print(f"[설정] 최대 파일 크기: {MAX_FILE_SIZE / (1024*1024):.0f}MB")
    print(f"[설정] 허용 확장자: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"[설정] 파일 정리 주기: {CLEANUP_OLD_FILES_DURATION}시간")
    print("=" * 60)
    
    # 파일 정리 스케줄러 시작
    start_cleanup_scheduler()
    
    # 서버 시작 시 즉시 한 번 정리 실행
    print("[파일 정리] 서버 시작 시 초기 정리 실행")
    cleanup_old_files()


@app.on_event("shutdown")
async def shutdown_event():
    """
    서버 종료 시 실행되는 이벤트 핸들러
    - 활성 자식 프로세스(분석 프로세스) 정리
    - PID 파일 삭제
    """
    print("[종료] 서버 종료 이벤트 수신, 정리 중...")
    cleanup_child_processes()
    remove_pid_file()
    print("[종료] 정리 완료")


@app.get("/")
async def root():
    """
    루트 엔드포인트
    """
    return {"message": "AI Inhaler Analysis API", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats():
    """
    서버 상태 통계 반환
    """
    # 현재 분석 중인 작업 수
    active_analyses = sum(1 for a in analysis_storage.values() if a["status"] in ["pending", "processing"])
    completed_analyses = sum(1 for a in analysis_storage.values() if a["status"] == "completed")
    error_analyses = sum(1 for a in analysis_storage.values() if a["status"] == "error")
    
    # 업로드 디렉토리 크기
    upload_size = 0
    upload_count = 0
    if UPLOAD_DIR.exists():
        for file in UPLOAD_DIR.iterdir():
            if file.is_file():
                upload_size += file.stat().st_size
                upload_count += 1
    
    return {
        "currentAnalyses": current_analysis_count,
        "maxConcurrentAnalyses": MAX_CONCURRENT_ANALYSES,
        "activeAnalyses": active_analyses,
        "completedAnalyses": completed_analyses,
        "errorAnalyses": error_analyses,
        "uploadedFiles": upload_count,
        "uploadedSizeMB": round(upload_size / (1024*1024), 2),
        "processTimeoutSeconds": PROCESS_TIMEOUT,
        "cleanupDurationHours": CLEANUP_OLD_FILES_DURATION
    }


if __name__ == "__main__":
    # multiprocessing 시작 방법 설정
    # 'spawn': 새로운 Python 인터프리터 시작 (안전, 권장)
    # 'fork': 부모 프로세스 복제 (Linux 기본, 잠재적 문제 가능)
    multiprocessing.set_start_method('spawn', force=True)

    # 이전 인스턴스 정리 및 PID 파일 생성
    kill_previous_instance()
    write_pid_file()

    # 시그널 핸들러 등록 (SIGTERM, SIGINT, SIGHUP)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGHUP, graceful_shutdown)

    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        cleanup_child_processes()
        remove_pid_file()

