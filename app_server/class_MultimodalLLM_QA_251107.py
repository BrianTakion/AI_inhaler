import base64
import os
import cv2
from PIL import Image
import io
import uuid
import shutil

class multimodalLLM:
    """ multimodalLLM에 관한 모음집 - OpenAI GPT 및 Google Gemini 지원"""
    
    # 지원 모델 및 기본 설정
    SUPPORTED_MODELS = {
        # OpenAI 모델 (context_window = 입력 제한, max_output_tokens = 출력 제한)
        # 참고: https://platform.openai.com/docs/models/gpt-4o
        "gpt-4.1": {"context_window": 128_000, "max_output_tokens": 4_096, "supports_vision": True, "supports_video": True, "provider": "openai"},       # 공식 128k context
        "gpt-5-nano": {"context_window": 128_000, "max_output_tokens": 4_096, "supports_vision": True, "supports_video": True, "provider": "openai"},       # 공식 128k context
        "gpt-5.1": {"context_window": 128_000, "max_output_tokens": 4_096, "supports_vision": True, "supports_video": True, "provider": "openai"},         # 공식 수치 미공개 → gpt-4o와 동일 가정
        "gpt-5.2": {"context_window": 400_000, "max_output_tokens": 128_000, "supports_vision": True, "supports_video": False, "provider": "openai"},         # 공식: 400k context, 128k output, vision 지원, video 미지원
        
        # Google Gemini 모델 (context_window = 입력 제한, max_output_tokens = 출력 제한)
        # 참고: https://ai.google.dev/gemini-api/docs/models/gemini
        "gemini-2.5-pro": {"context_window": 1_000_000, "max_output_tokens": 8_192, "supports_vision": True, "supports_video": True, "provider": "google"},   # 최대 1M context
        "gemini-3-flash-preview": {"context_window": 1_000_000, "max_output_tokens": 8_192, "supports_vision": True, "supports_video": True, "provider": "google"},  # 실제 API 모델명
        "gemini-3-pro-preview": {"context_window": 1_000_000, "max_output_tokens": 8_192, "supports_vision": True, "supports_video": True, "provider": "google"},  # 공식 수치 부재 → Pro와 동일 가정
    }
    
    def __init__(self, llm_name: str = "gpt-5-nano", api_key: str = None):
        self.llm_name = llm_name
        
        # 모델 유효성 검사
        if llm_name not in self.SUPPORTED_MODELS:
            print(f"경고: {llm_name}은 지원되지 않는 모델입니다. 지원 모델: {list(self.SUPPORTED_MODELS.keys())}")
            print("gpt-5-nano로 기본 설정합니다.")
            self.llm_name = "gpt-5-nano"
        
        self.model_config = self.SUPPORTED_MODELS[self.llm_name]
        self.provider = self.model_config["provider"]
        
        if self.provider == "openai":  # OpenAI 모델들
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif self.provider == "google":  # Google Gemini 모델들
            from google import genai
            self.client = genai.Client(api_key=api_key)
            self.llm_name_for_api = self.llm_name  # API 호출 시 사용할 모델명 저장
        else:  # ollama 등 다른 모델
            pass


    # 파일명에 한글 포함되었을 때
    # [다중 사용자 지원] UUID 기반 고유 임시 파일명 사용
    def cv2_imread(self, image_path):
        """
        한글 파일명 지원을 위한 cv2.imread 래퍼
        
        [다중 사용자 지원]
        - UUID 기반 고유 임시 파일명으로 동시 접근 충돌 방지
        - try-finally로 예외 발생 시에도 원본 파일 복구
        """
        # 고유한 임시 파일명 생성 (UUID 사용)
        unique_id = uuid.uuid4().hex[:8]
        image_path_temp = f'temporary_cv2_imread_{unique_id}'
        
        try:
            os.replace(image_path, image_path_temp)
            image = cv2.imread(image_path_temp)  # cv2.imread()는 한글 파일명을 처리 못함
            os.replace(image_path_temp, image_path)
            return image
        except Exception as e:
            # 예외 발생 시 원본 파일 복구 시도
            if os.path.exists(image_path_temp) and not os.path.exists(image_path):
                try:
                    os.replace(image_path_temp, image_path)
                except:
                    pass
            raise e
 

    # 파일명에 한글 포함되었을 때
    # [다중 사용자 지원] UUID 기반 고유 임시 파일명 사용
    def cv2_imwrite(self, output_file, output_image):
        """
        한글 파일명 지원을 위한 cv2.imwrite 래퍼
        
        [다중 사용자 지원]
        - UUID 기반 고유 임시 파일명으로 동시 접근 충돌 방지
        - try-finally로 예외 발생 시에도 임시 파일 정리
        """
        # 고유한 임시 파일명 생성 (UUID 사용)
        unique_id = uuid.uuid4().hex[:8]
        output_file_temp = f'temporary_cv2_imwrite_{unique_id}.png'
        
        try:
            cv2.imwrite(output_file_temp, output_image)  # cv2.imwrite()는 한글 파일명을 처리 못함
            os.replace(output_file_temp, output_file)
        finally:
            # 임시 파일 정리
            if os.path.exists(output_file_temp):
                try:
                    os.remove(output_file_temp)
                except:
                    pass


    def query_answer_chatGPT(self, system_prompt, user_prompt, image_path=None, image_array=None, extract_video=10, max_output_tokens=None, temperature=0.0, seed=1):
        # Google Gemini 모델인 경우 별도 처리
        if self.provider == "google":
            return self._query_gemini(system_prompt, user_prompt, image_path, image_array, extract_video, max_output_tokens, temperature)
        
        # max_output_tokens 기본값 및 상한 클램프
        if max_output_tokens is None:
            max_output_tokens = self.model_config["max_output_tokens"]
        else:
            # 사용자 지정 값이 모델 상한을 초과하면 상한으로 클램프
            if max_output_tokens > self.model_config["max_output_tokens"]:
                print(f"경고: 요청한 max_output_tokens({max_output_tokens})이 모델 한도({self.model_config['max_output_tokens']})를 초과하여 클램프합니다.")
                max_output_tokens = self.model_config["max_output_tokens"]
        
        # 비전/비디오 기능 지원 여부 확인
        supports_vision = self.model_config["supports_vision"]
        supports_video = self.model_config["supports_video"]
        
        # 비전 기능을 지원하지 않는 모델의 경우 이미지/비디오 입력 제한
        if (image_array is not None or image_path is not None) and not supports_vision:
            print(f"경고: {self.llm_name} 모델은 이미지/비디오 입력을 지원하지 않습니다. 텍스트만 처리합니다.")
            image_array = None
            image_path = None
            
        if image_array is not None:  # image_array가 직접 제공된 경우
            try:
                # 이미지 배열 유효성 검사
                if image_array is None or not hasattr(image_array, 'size') or image_array.size == 0:
                    print("이미지 배열이 비어있거나 None입니다.")
                    return "Image Error: The image array is empty or None."

                # 이미지 배열 형태 검사 (H x W x 3)
                if len(image_array.shape) != 3 or image_array.shape[2] != 3:
                    print(f"이미지 배열 형태가 올바르지 않습니다: {image_array.shape}")
                    return "Image Error: Invalid image array format."

                # 이미지 배열을 JPEG로 변환
                success, jpeg_image = cv2.imencode('.jpg', image_array)
                if not success:
                    print("이미지 배열을 JPEG로 변환하는 데 실패했습니다.")
                    return "Image Error: Failed to encode image to JPEG format."

                # Base64 인코딩 + MIME 헤더 추가
                b64_str = base64.b64encode(jpeg_image).decode("utf-8")
                b64_with_header = f"data:image/jpeg;base64,{b64_str}"

                # GPT-4o 입력 포맷 구성
                user_prompt2 = [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": b64_with_header}}
                ]
            except Exception as e:
                print(f"이미지 배열 처리 중 오류 발생: {e}")
                return f"Image Error: Error processing image array: {str(e)}"
                
        elif image_path:  # image_path로 파일형태로 제공된 경우
            try:
                _, ext = os.path.splitext(image_path)
                ext = ext.lower()

                # image 파일일 때, JPEG으로 변환 후 base64 encoding으로 보낸다.
                if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                    image = self.cv2_imread(image_path)
                    if image is None:
                        print(f"이미지를 읽어들이는 데 실패했습니다: {image_path}")
                        return f"Image Error: Failed to read image file: {image_path}"
                    
                    # 모든 이미지를 JPEG로 변환 (GPT-4o 안정성 확보)
                    success, jpeg_image = cv2.imencode('.jpg', image)
                    if not success:
                        print("이미지를 JPEG로 변환하는 데 실패했습니다.")
                        return "Image Error: Failed to encode image to JPEG format."
                    
                    # Base64 인코딩 + MIME 헤더 추가
                    b64_str = base64.b64encode(jpeg_image).decode("utf-8")
                    b64_with_header = f"data:image/jpeg;base64,{b64_str}"
                    
                    # GPT-4o 입력 포맷 구성
                    user_prompt2 = [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": b64_with_header}}
                    ]

                # video 파일일 때, multiple JPEG으로 변환 후 base64 encoding(필요시, 일정 간격 추출)으로 보낸다.
                elif ext.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.mpeg']:  # .mp4 동작체크 완료
                    if not supports_video:
                        print(f"경고: {self.llm_name} 모델은 비디오 입력을 지원하지 않습니다.")
                        return f"Video Error: {self.llm_name} model does not support video input."
                    video = cv2.VideoCapture(image_path)
                    if not video.isOpened():
                        print(f"비디오 파일을 열 수 없습니다: {image_path}")
                        return f"Image Error: Failed to open video file: {image_path}"
                    
                    base64Frames = []
                    frame_count = 0
                    while video.isOpened():
                        success, frame = video.read()
                        if not success:
                            break
                        success, buffer = cv2.imencode(".jpg", frame)
                        if not success:
                            print(f"프레임 {frame_count}을 JPEG로 변환하는 데 실패했습니다.")
                            continue
                        # base64 인코딩 + 접두어
                        b64_str = base64.b64encode(buffer).decode("utf-8")
                        base64Frames.append(f"data:image/jpeg;base64,{b64_str}")
                        frame_count += 1
                    video.release()
                    
                    if not base64Frames:
                        print("비디오에서 프레임을 추출할 수 없습니다.")
                        return "Image Error: Failed to extract frames from video."
                    
                    # 일정 간격 추출 (예: extract_video=10 → 10프레임마다)
                    extract_base64Frames = base64Frames[0::extract_video]
                    print(f"video: input frames {len(base64Frames)} --> extracted frames {len(extract_base64Frames)}")
                    
                    # GPT-4o 입력 메시지 구성
                    user_prompt2 = [
                        {"type": "text", "text": user_prompt},
                        *map(lambda x: {"type": "image_url", "image_url": {"url": x}}, extract_base64Frames)
                    ]
                
                else:
                    print(f"Unknown media file format: {ext}")
                    return f"Image Error: Unknown media file format: {ext}"
            except Exception as e:
                print(f"이미지 파일 처리 중 오류 발생: {e}")
                return f"Image Error: Error processing image file: {str(e)}"
        else:  # text input only
            user_prompt2 = user_prompt

        try:
            # API 호출 매개변수 구성 (공통)
            api_params = {
                "model": self.llm_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt2}
                ]
            }

            # 모델별 토큰 파라미터 호환 처리
            # 기본값: max_tokens (gpt-4o 계열 등 일반 모델은 max_tokens가 출력 제한임)
            api_params["max_tokens"] = max_output_tokens
            if self.llm_name == "gpt-5" or self.llm_name.startswith("gpt-5"):
                # gpt-5는 max_completion_tokens를 사용, temperature/seed 미지원
                api_params.pop("max_tokens", None)
                api_params["max_completion_tokens"] = max_output_tokens
            elif self.llm_name.startswith("o1"):
                # o1 계열은 max_output_tokens 사용, temperature/seed 미지원
                api_params.pop("max_tokens", None)
                api_params["max_output_tokens"] = max_output_tokens

            # temperature 설정: gpt-5/o1은 미지원이므로 제외, 그 외 모델만 설정
            if not (self.llm_name == "gpt-5" or self.llm_name.startswith("gpt-5") or self.llm_name.startswith("o1")):
                api_params["temperature"] = temperature

            # seed 설정: gpt-5/o1은 제외
            if not (self.llm_name == "gpt-5" or self.llm_name.startswith("gpt-5") or self.llm_name.startswith("o1")):
                api_params["seed"] = seed

            # GPT-5의 경우 향상된 추론을 위한 추가 설정 (향후 지원 시 확장 포인트)
            if self.llm_name == "gpt-5" or self.llm_name.startswith("gpt-5"):
                pass

            response = self.client.chat.completions.create(**api_params)
            answer = response.choices[0].message.content
            return answer
            
        except Exception as e:
            error_msg = str(e)
            print(f"{self.llm_name} API 호출 중 오류 발생: {error_msg}")
            
            # 구체적인 오류 메시지 제공
            if "context_length_exceeded" in error_msg.lower():
                return f"API Error: 입력이 {self.llm_name}의 최대 입력 토큰 제한(Context Window: {self.model_config['context_window']})을 초과했습니다."
            elif "rate_limit" in error_msg.lower():
                return f"API Error: API 호출 한도 초과. 잠시 후 다시 시도해주세요."
            elif "model_not_found" in error_msg.lower():
                return f"API Error: {self.llm_name} 모델을 찾을 수 없습니다. 모델명을 확인해주세요."
            else:
                return f"API Error: {error_msg}"

    def _query_gemini(self, system_prompt, user_prompt, image_path=None, image_array=None, extract_video=10, max_output_tokens=None, temperature=0.0):
        """Google Gemini 모델 전용 쿼리 메서드"""
        # max_output_tokens 설정
        if max_output_tokens is None:
            max_output_tokens = self.model_config["max_output_tokens"]
        else:
            if max_output_tokens > self.model_config["max_output_tokens"]:
                print(f"경고: 요청한 max_output_tokens({max_output_tokens})이 모델 한도({self.model_config['max_output_tokens']})를 초과하여 클램프합니다.")
                max_output_tokens = self.model_config["max_output_tokens"]
        
        # 비전/비디오 지원 확인
        supports_vision = self.model_config["supports_vision"]
        supports_video = self.model_config["supports_video"]
        
        if (image_array is not None or image_path is not None) and not supports_vision:
            print(f"경고: {self.llm_name} 모델은 이미지/비디오 입력을 지원하지 않습니다. 텍스트만 처리합니다.")
            image_array = None
            image_path = None
        
        try:
            from google.genai import types
            
            # 프롬프트 구성 (Gemini는 system_prompt를 user_prompt에 통합)
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            contents = [types.Part.from_text(text=combined_prompt)]
            
            # 이미지/비디오 처리
            if image_array is not None:
                # numpy array를 PIL Image로 변환
                try:
                    if image_array is None or not hasattr(image_array, 'size') or image_array.size == 0:
                        print("이미지 배열이 비어있거나 None입니다.")
                        return "Image Error: The image array is empty or None."
                    
                    if len(image_array.shape) != 3 or image_array.shape[2] != 3:
                        print(f"이미지 배열 형태가 올바르지 않습니다: {image_array.shape}")
                        return "Image Error: Invalid image array format."
                    
                    # BGR -> RGB 변환 (OpenCV는 BGR 사용)
                    image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(image_rgb)
                    
                    # PIL Image를 bytes로 변환
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='JPEG')
                    img_bytes = img_byte_arr.getvalue()
                    contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                    
                except Exception as e:
                    print(f"이미지 배열 처리 중 오류 발생: {e}")
                    return f"Image Error: Error processing image array: {str(e)}"
                    
            elif image_path:
                try:
                    _, ext = os.path.splitext(image_path)
                    ext = ext.lower()
                    
                    # 이미지 파일 처리
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                        image = self.cv2_imread(image_path)
                        if image is None:
                            print(f"이미지를 읽어들이는 데 실패했습니다: {image_path}")
                            return f"Image Error: Failed to read image file: {image_path}"
                        
                        # BGR -> RGB 변환
                        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(image_rgb)
                        
                        # PIL Image를 bytes로 변환
                        img_byte_arr = io.BytesIO()
                        pil_image.save(img_byte_arr, format='JPEG')
                        img_bytes = img_byte_arr.getvalue()
                        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                    
                    # 비디오 파일 처리
                    elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.mpeg']:
                        if not supports_video:
                            print(f"경고: {self.llm_name} 모델은 비디오 입력을 지원하지 않습니다.")
                            return f"Video Error: {self.llm_name} model does not support video input."
                        
                        video = cv2.VideoCapture(image_path)
                        if not video.isOpened():
                            print(f"비디오 파일을 열 수 없습니다: {image_path}")
                            return f"Image Error: Failed to open video file: {image_path}"
                        
                        frames = []
                        frame_count = 0
                        while video.isOpened():
                            success, frame = video.read()
                            if not success:
                                break
                            frames.append(frame)
                            frame_count += 1
                        video.release()
                        
                        if not frames:
                            print("비디오에서 프레임을 추출할 수 없습니다.")
                            return "Image Error: Failed to extract frames from video."
                        
                        # 일정 간격 추출
                        extract_frames = frames[0::extract_video]
                        print(f"video: input frames {len(frames)} --> extracted frames {len(extract_frames)}")
                        
                        # 프레임들을 PIL Image로 변환 후 bytes로 변환
                        for frame in extract_frames:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_image = Image.fromarray(frame_rgb)
                            img_byte_arr = io.BytesIO()
                            pil_image.save(img_byte_arr, format='JPEG')
                            img_bytes = img_byte_arr.getvalue()
                            contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                    
                    else:
                        print(f"Unknown media file format: {ext}")
                        return f"Image Error: Unknown media file format: {ext}"
                        
                except Exception as e:
                    print(f"이미지 파일 처리 중 오류 발생: {e}")
                    return f"Image Error: Error processing image file: {str(e)}"
            
            # Gemini API 호출 (새 SDK 사용)
            generation_config = types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            
            response = self.client.models.generate_content(
                model=self.llm_name,
                contents=contents,
                config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"{self.llm_name} API 호출 중 오류 발생: {error_msg}")
            
            # 구체적인 오류 메시지 제공
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                return f"API Error: API 호출 한도 초과. 잠시 후 다시 시도해주세요."
            elif "invalid" in error_msg.lower() and "api" in error_msg.lower():
                return f"API Error: API 키가 유효하지 않습니다."
            else:
                return f"API Error: {error_msg}"
    
    def get_model_info(self):
        """현재 설정된 모델의 정보를 반환합니다."""
        return {
            "model_name": self.llm_name,
            "context_window": self.model_config["context_window"],
            "max_output_tokens": self.model_config["max_output_tokens"],
            "supports_vision": self.model_config["supports_vision"],
            "supports_video": self.model_config["supports_video"],
            "provider": self.provider
        }
    
    def list_supported_models(self):
        """지원하는 모든 모델 목록을 반환합니다."""
        return list(self.SUPPORTED_MODELS.keys())
    
    def switch_model(self, new_model_name, api_key=None):
        """모델을 다른 모델로 변경합니다."""
        if new_model_name not in self.SUPPORTED_MODELS:
            print(f"오류: {new_model_name}은 지원되지 않는 모델입니다.")
            print(f"지원 모델: {self.list_supported_models()}")
            return False
        
        old_provider = self.provider
        self.llm_name = new_model_name
        self.model_config = self.SUPPORTED_MODELS[new_model_name]
        self.provider = self.model_config["provider"]
        
        # provider가 변경된 경우 클라이언트 재초기화
        if old_provider != self.provider:
            if api_key is None:
                print(f"경고: provider가 {old_provider}에서 {self.provider}로 변경되었습니다. API 키를 제공해야 합니다.")
                return False
            
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            elif self.provider == "google":
                from google import genai
                self.client = genai.Client(api_key=api_key)
                self.llm_name_for_api = self.llm_name
        elif self.provider == "google":
            # Gemini는 모델이 변경되면 새 Client 인스턴스 필요 (실제로는 동일 클라이언트 사용 가능)
            from google import genai
            if api_key is None:
                # 기존 클라이언트 재사용 (모델명만 변경)
                self.llm_name_for_api = self.llm_name
            else:
                self.client = genai.Client(api_key=api_key)
                self.llm_name_for_api = self.llm_name
        
        print(f"모델이 {new_model_name}로 변경되었습니다.")
        return True


if __name__ == "__main__":
    from dotenv import load_dotenv
    # app_server 디렉토리의 .env 파일에서 환경변수 로드
    app_server_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(app_server_dir, ".env")
    load_dotenv(dotenv_path=env_path)
    
    # API 키 로드
    openai_api_key = os.getenv('OPENAI_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')  # Gemini용

    if not openai_api_key:
        print("경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("app_server 디렉토리의 .env 파일에 'OPENAI_API_KEY=your-api-key-here' 형식으로 추가하세요.")
    
    if not google_api_key:
        print("경고: GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("app_server 디렉토리의 .env 파일에 'GOOGLE_API_KEY=your-api-key-here' 형식으로 추가하세요.")
    
    # 다양한 모델 테스트
    test_models = [
        ("gpt-4o-mini", openai_api_key),
        ("gpt-4o", openai_api_key),
        ("gemini-1.5-flash", google_api_key),
        ("gemini-1.5-pro", google_api_key),
        ("gemini-2.5-flash", google_api_key),
        ("gemini-2.5-pro", google_api_key),
        ("gemini-3.0-flash", google_api_key),
        ("gemini-3.0-pro", google_api_key)
    ]
    
    for llm_name, api_key in test_models:
        if not api_key:
            print(f"\n=== {llm_name} 테스트 스킵 (API 키 없음) ===")
            continue
            
        print(f"\n=== {llm_name} 테스트 ===")
        try:
            llm = multimodalLLM(llm_name, api_key)
            
            # 기본 텍스트 테스트
            system_prompt = "You are an excellent AI assistant with advanced reasoning capabilities."
            user_prompt = "간단한 인사와 함께 당신의 모델명과 주요 기능을 소개해주세요."
            
            answer = llm.query_answer_chatGPT(system_prompt, user_prompt)
            print(f"모델: {llm_name}")
            print(f"Provider: {llm.provider}")
            print(f"지원 기능: 비전={llm.model_config['supports_vision']}, 비디오={llm.model_config['supports_video']}")
            print(f"입력 제한(Context): {llm.model_config['context_window']}, 출력 제한: {llm.model_config['max_output_tokens']}")
            print(f"응답: {answer[:200]}...")  # 처음 200자만 출력
            
        except Exception as e:
            print(f"{llm_name} 테스트 실패: {e}")
    
    # 실제 사용 예시 (주석 처리)
    # OpenAI 예시
    # llm_openai = multimodalLLM("gpt-4o", openai_api_key)
    # system_prompt = "You are an excellent image analyst."
    # user_prompt = "이미지에서 무엇이 보이는지 설명하시오."
    # image_path = "your_image.jpg"  # 실제 파일 경로로 변경
    # answer = llm_openai.query_answer_chatGPT(system_prompt, user_prompt, image_path)
    # print(answer)
    
    # Gemini 예시
    # llm_gemini = multimodalLLM("gemini-1.5-pro", google_api_key)
    # system_prompt = "You are an excellent video analyst."
    # user_prompt = "비디오에서 어떤 행동을 하는지 단계적으로 설명하시오."
    # image_path = "your_video_file.mp4"  # 실제 파일 경로로 변경
    # answer = llm_gemini.query_answer_chatGPT(system_prompt, user_prompt, image_path)
    # print(answer)