#!/usr/bin/env python
# coding: utf-8

"""
간단한 API 키 검증 스크립트
현재 사용 가능한 모델을 확인합니다.
"""

import os
import sys
from dotenv import load_dotenv

# app_server 디렉토리의 .env 파일 로드
app_server_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(app_server_dir, ".env")
load_dotenv(dotenv_path=env_path)

# API 키 로드
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

print("="*80)
print("API 키 검증 테스트")
print("="*80)

# API 키 확인
print("\n[1] API 키 설정 확인")
print(f"  OPENAI_API_KEY: {'✅ 설정됨' if openai_api_key else '❌ 미설정'}")
print(f"  GOOGLE_API_KEY: {'✅ 설정됨' if google_api_key else '❌ 미설정'}")

# OpenAI 테스트
if openai_api_key:
    print("\n[2] OpenAI API 테스트")
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Test successful' in Korean."}
            ],
            max_tokens=30
        )
        
        result = response.choices[0].message.content
        print(f"  모델: gpt-4o")
        print(f"  응답: {result}")
        print("  ✅ OpenAI API 키 정상 동작")
        
    except Exception as e:
        print(f"  ❌ OpenAI API 테스트 실패: {str(e)}")
else:
    print("\n[2] OpenAI API 테스트 스킵 (API 키 미설정)")

# Google Gemini 테스트
if google_api_key:
    print("\n[3] Google Gemini API 테스트")
    try:
        from google import genai
        
        client = genai.Client(api_key=google_api_key)
        
        # 사용 가능한 모델 목록 조회
        print("  - 사용 가능한 Gemini 모델 조회 중...")
        models = client.models.list()
        gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
        
        if gemini_models:
            print(f"  - 총 {len(gemini_models)}개의 Gemini 모델 발견:")
            for idx, model_name in enumerate(gemini_models[:5], 1):
                print(f"    {idx}. {model_name}")
            if len(gemini_models) > 5:
                print(f"    ... 외 {len(gemini_models) - 5}개")
            
            # 첫 번째 모델로 테스트
            test_model = gemini_models[0]
            print(f"\n  - {test_model} 모델로 테스트 중...")
            response = client.models.generate_content(
                model=test_model,
                contents="Say 'Test successful' in Korean."
            )
            result = response.text
            print(f"  응답: {result}")
            print("  ✅ Google Gemini API 키 정상 동작")
        else:
            print("  ⚠️ 사용 가능한 Gemini 모델을 찾을 수 없습니다")
        
    except Exception as e:
        print(f"  ❌ Google Gemini API 테스트 실패: {str(e)}")
        print(f"\n  💡 문제 해결 방법:")
        print(f"     1. API 키가 유효한지 확인")
        print(f"     2. Gemini API가 활성화되어 있는지 확인")
        print(f"     3. 새 API 키 발급: https://aistudio.google.com/app/apikey")
else:
    print("\n[3] Google Gemini API 테스트 스킵 (API 키 미설정)")

print("\n" + "="*80)
print("테스트 완료")
print("="*80)
