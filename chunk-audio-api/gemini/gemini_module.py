# chunk-audio-api/gemini/gemini_module.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

from gemini.prompt_module import build_prompt_from_history
from db.history_module import get_user_history, save_to_history

# 환경 변수 로드 및 Gemini 설정
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# 사용자 ID와 입력을 받아 히스토리를 활용해 Gemini 응답 생성
def ask_gemini(user_id: str, user_input: str) -> str:
    try:
        # 1. 세션 히스토리 조회
        history = get_user_history(user_id)

        # 2. 히스토리를 포함한 프롬프트 생성
        prompt = build_prompt_from_history(history, user_input)

        # 3. Gemini 호출
        response = model.generate_content(prompt)
        gemini_reply = response.text.strip()

        # 4. 히스토리 저장
        save_to_history(user_id, "user", user_input)
        save_to_history(user_id, "gemini", gemini_reply)

        return gemini_reply
    except Exception as e:
        return f"[Gemini 오류] {str(e)}"
