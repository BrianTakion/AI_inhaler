#!/usr/bin/env python
# coding: utf-8

"""
에이전트 프로그래밍 API 키 최종 검증
텍스트 + 이미지(비전) 기능을 모두 테스트합니다.
"""

import os
import sys
import numpy as np
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

print("="*80)
print("에이전트 프로그래밍 API 키 최종 검증")
print("="*80)

# API 키 확인
print("\n[1단계] API 키 설정 확인")
print(f"  OPENAI_API_KEY: {'✅ 설정됨' if openai_api_key else '❌ 미설정'}")
print(f"  GOOGLE_API_KEY: {'✅ 설정됨' if google_api_key else '❌ 미설정'}")

if not openai_api_key or not google_api_key:
    print("\n❌ 오류: API 키가 설정되지 않았습니다.")
    print("   .env 파일에 API 키를 설정하세요.")
    sys.exit(1)

# MultimodalLLM 클래스 임포트
print("\n[2단계] MultimodalLLM 클래스 로드")
try:
    from class_MultimodalLLM_QA_251107 import multimodalLLM
    print("  ✅ MultimodalLLM 클래스 로드 성공")
except Exception as e:
    print(f"  ❌ MultimodalLLM 클래스 로드 실패: {str(e)}")
    sys.exit(1)

# 테스트 이미지 생성 (간단한 빨간색 사각형)
print("\n[3단계] 테스트 이미지 생성")
try:
    # 300x300 빨간색 이미지 생성
    test_image = np.zeros((300, 300, 3), dtype=np.uint8)
    test_image[:, :] = [0, 0, 255]  # BGR 포맷: 빨간색
    print("  ✅ 테스트 이미지 생성 완료 (300x300 빨간색 이미지)")
except Exception as e:
    print(f"  ❌ 테스트 이미지 생성 실패: {str(e)}")
    sys.exit(1)

# 테스트할 모델 목록
test_models = [
    ("gpt-4.1", openai_api_key, "OpenAI"),
    ("gemini-2.5-flash", google_api_key, "Google Gemini"),
    ("gemini-2.5-pro", google_api_key, "Google Gemini"),
]

print("\n[4단계] 각 모델별 텍스트 + 비전 기능 검증")
print("-" * 80)

results = {}

for model_name, api_key, provider in test_models:
    print(f"\n[{provider}] {model_name} 모델 테스트")
    
    try:
        # MultimodalLLM 인스턴스 생성
        llm = multimodalLLM(model_name, api_key)
        print(f"  ✓ LLM 인스턴스 생성 완료")
        
        # 1. 텍스트 전용 테스트
        print(f"  ✓ [테스트 1/2] 텍스트 쿼리 테스트 중...")
        system_prompt = "You are a helpful assistant."
        user_prompt = "간단히 '테스트 성공'이라고만 한글로 답변하세요."
        
        text_response = llm.query_answer_chatGPT(system_prompt, user_prompt)
        text_success = "테스트" in text_response or "성공" in text_response or "test" in text_response.lower()
        print(f"    응답: {text_response[:50]}")
        print(f"    결과: {'✅ 성공' if text_success else '⚠️ 응답 확인 필요'}")
        
        # 2. 비전(이미지) 테스트
        print(f"  ✓ [테스트 2/2] 비전(이미지) 쿼리 테스트 중...")
        system_prompt = "You are an image analysis assistant."
        user_prompt = "이 이미지의 주요 색상이 무엇인지 한글로 간단히 답변하세요."
        
        vision_response = llm.query_answer_chatGPT(
            system_prompt, user_prompt, image_array=test_image
        )
        vision_success = ("빨강" in vision_response or "레드" in vision_response or 
                         "red" in vision_response.lower() or "빨간색" in vision_response)
        print(f"    응답: {vision_response[:100]}")
        print(f"    결과: {'✅ 성공 (빨간색 감지)' if vision_success else '⚠️ 색상 감지 실패'}")
        
        results[model_name] = {
            "status": "✅ 성공" if (text_success and vision_success) else "⚠️ 부분 성공",
            "provider": provider,
            "text_test": "✅" if text_success else "⚠️",
            "vision_test": "✅" if vision_success else "⚠️",
            "text_response": text_response[:30],
            "vision_response": vision_response[:50]
        }
        
        print(f"  ✅ {model_name} 테스트 완료")
        
    except Exception as e:
        error_msg = str(e)
        results[model_name] = {
            "status": "❌ 실패",
            "provider": provider,
            "error": error_msg[:100]
        }
        print(f"  ❌ {model_name} 테스트 실패")
        print(f"     오류: {error_msg[:100]}")

# 결과 요약
print("\n" + "="*80)
print("[최종 결과 요약]")
print("="*80)

for model_name, result in results.items():
    print(f"\n{result['provider']} - {model_name}")
    print(f"  종합 상태: {result['status']}")
    if "error" in result:
        print(f"  오류: {result['error']}")
    else:
        print(f"  텍스트 테스트: {result['text_test']}")
        print(f"  비전 테스트: {result['vision_test']}")

print("\n" + "-"*80)

success_count = sum(1 for r in results.values() if "성공" in r["status"])
total_count = len(results)

print(f"전체: {success_count}/{total_count} 모델 성공")
print("-"*80)

if success_count == total_count:
    print("\n🎉 모든 API 키가 텍스트 및 비전 기능 모두 정상 동작합니다!")
    print("   에이전트 프로그래밍을 시작할 수 있습니다.")
    print("\n📋 지원 모델:")
    print("   - gpt-4.1 (OpenAI)")
    print("   - gemini-2.5-flash (Google)")
    print("   - gemini-2.5-pro (Google)")
elif success_count > 0:
    print("\n⚠️  일부 모델이 정상 동작합니다.")
    print("   정상 동작하는 모델로 에이전트 프로그래밍을 시작할 수 있습니다.")
else:
    print("\n❌ API 키에 문제가 있습니다.")
    print("   .env 파일의 API 키를 확인하세요.")

print("\n" + "="*80)
print("검증 완료")
print("="*80)
