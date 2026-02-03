#!/usr/bin/env python
# coding: utf-8

"""
에이전트 프로그래밍 API 키 종합 검증
실제 MultimodalLLM 클래스를 사용하여 API 키 동작을 확인합니다.
"""

import os
import sys
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
print("에이전트 프로그래밍 API 키 종합 검증")
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

# 테스트할 모델 목록 (에이전트에서 실제 사용하는 모델들)
test_models = [
    ("gpt-4.1", openai_api_key, "OpenAI"),
    ("gemini-2.5-flash", google_api_key, "Google Gemini"),
]

print("\n[3단계] 각 모델별 API 키 동작 검증")
print("-" * 80)

results = {}

for model_name, api_key, provider in test_models:
    print(f"\n[{provider}] {model_name} 모델 테스트")
    
    try:
        # MultimodalLLM 인스턴스 생성
        llm = multimodalLLM(model_name, api_key)
        print(f"  ✓ LLM 인스턴스 생성 성공")
        print(f"    - Provider: {llm.provider}")
        print(f"    - 비전 지원: {llm.model_config['supports_vision']}")
        print(f"    - 비디오 지원: {llm.model_config['supports_video']}")
        print(f"    - Context Window: {llm.model_config['context_window']}")
        print(f"    - Max Output Tokens: {llm.model_config['max_output_tokens']}")
        
        # 간단한 텍스트 쿼리 테스트
        system_prompt = "You are a helpful assistant."
        user_prompt = "한국어로 '안녕하세요'라고 인사해주세요."
        
        print(f"  ✓ 텍스트 쿼리 테스트 중...")
        response = llm.query_answer_chatGPT(system_prompt, user_prompt)
        print(f"    응답: {response[:100]}...")
        
        results[model_name] = {
            "status": "✅ 성공",
            "provider": provider,
            "response_preview": response[:50]
        }
        
        print(f"  ✅ {model_name} 테스트 완료")
        
    except Exception as e:
        error_msg = str(e)
        results[model_name] = {
            "status": "❌ 실패",
            "provider": provider,
            "error": error_msg
        }
        print(f"  ❌ {model_name} 테스트 실패")
        print(f"     오류: {error_msg}")

# 결과 요약
print("\n" + "="*80)
print("[최종 결과 요약]")
print("="*80)

success_count = sum(1 for r in results.values() if "성공" in r["status"])
total_count = len(results)

for model_name, result in results.items():
    print(f"\n{result['provider']} - {model_name}")
    print(f"  상태: {result['status']}")
    if "error" in result:
        print(f"  오류: {result['error']}")
    elif "response_preview" in result:
        print(f"  응답 미리보기: {result['response_preview']}")

print("\n" + "-"*80)
print(f"성공: {success_count}/{total_count} 모델")
print("-"*80)

if success_count == total_count:
    print("\n🎉 모든 API 키가 정상 동작합니다!")
    print("   에이전트 프로그래밍을 시작할 수 있습니다.")
else:
    print("\n⚠️  일부 API 키에 문제가 있습니다.")
    print("   실패한 모델의 API 키를 확인하세요.")

print("\n" + "="*80)
print("검증 완료")
print("="*80)
