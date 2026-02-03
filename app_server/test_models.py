#!/usr/bin/env python
# coding: utf-8

"""
LLM 모델 테스트 스크립트
gpt-4.1과 gemini-3-flash-preview 모델이 정상적으로 작동하는지 테스트합니다.
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
print("LLM 모델 테스트 시작")
print("="*80)

# API 키 확인
print("\n[1] API 키 확인")
print(f"  OPENAI_API_KEY: {'설정됨' if openai_api_key else '미설정'}")
print(f"  GOOGLE_API_KEY: {'설정됨' if google_api_key else '미설정'}")

if not openai_api_key:
    print("\n❌ 오류: OPENAI_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

if not google_api_key:
    print("\n❌ 오류: GOOGLE_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

# OpenAI 모델 테스트
print("\n[2] OpenAI 모델 (gpt-4.1) 테스트")
try:
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_api_key)
    
    print("  - API 클라이언트 생성 완료")
    print("  - 간단한 요청 테스트 중...")
    
    response = client.chat.completions.create(
        model="gpt-4o",  # gpt-4.1은 실제로 gpt-4o를 사용할 가능성이 높음
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' in Korean."}
        ],
        max_tokens=50
    )
    
    result = response.choices[0].message.content
    print(f"  - 응답: {result}")
    print("  ✅ OpenAI 모델 테스트 성공")
    
except Exception as e:
    print(f"  ❌ OpenAI 모델 테스트 실패: {str(e)}")
    sys.exit(1)

# Google Gemini 모델 테스트
print("\n[3] Google Gemini 모델 (google.genai 패키지 사용) 테스트")
try:
    from google import genai
    
    client = genai.Client(api_key=google_api_key)
    
    print("  - API 클라이언트 생성 완료")
    print("  - 간단한 요청 테스트 중...")
    
    # gemini-2.5-flash로 테스트 (gemini-2.0-flash-exp, gemini-1.5-flash는 종료됨)
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Say 'Hello' in Korean."
        )
        result = response.text
        print(f"  - 응답: {result}")
        print("  ✅ Google Gemini 모델 테스트 성공 (gemini-2.5-flash)")
    except Exception as e1:
        print(f"  ⚠️ gemini-2.5-flash 테스트 실패: {str(e1)}")
        print("  - gemini-3-flash-preview로 재시도 중...")
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents="Say 'Hello' in Korean."
            )
            result = response.text
            print(f"  - 응답: {result}")
            print("  ✅ Google Gemini 모델 테스트 성공 (gemini-3-flash-preview)")
        except Exception as e2:
            print(f"  ❌ gemini-3-flash-preview 테스트 실패: {str(e2)}")
            raise e2
    
except Exception as e:
    print(f"  ❌ Google Gemini 모델 테스트 실패: {str(e)}")
    print(f"\n⚠️ Google API 키 문제:")
    print(f"  - API 키가 일시 중단되었거나 만료되었을 수 있습니다")
    print(f"  - 새로운 API 키를 발급받아 .env 파일에 설정하세요")
    print(f"  - https://makersuite.google.com/app/apikey")
    sys.exit(1)

# 사용 가능한 모델 목록 확인
print("\n[4] 사용 가능한 Gemini 모델 목록 확인")
try:
    models = client.models.list()
    gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
    print(f"  - 총 {len(gemini_models)}개의 Gemini 모델 발견:")
    for idx, model_name in enumerate(gemini_models[:10], 1):  # 최대 10개만 출력
        print(f"    {idx}. {model_name}")
    if len(gemini_models) > 10:
        print(f"    ... 외 {len(gemini_models) - 10}개")
except Exception as e:
    print(f"  ⚠️ 모델 목록 조회 실패: {str(e)}")

print("\n" + "="*80)
print("✅ 모든 모델 테스트 완료")
print("="*80)
print("\n다음 단계:")
print("  1. app_main.py의 LLM 모델 설정에서 테스트된 모델명 사용")
print("  2. 실제 분석 작업 실행 테스트")
print("")
