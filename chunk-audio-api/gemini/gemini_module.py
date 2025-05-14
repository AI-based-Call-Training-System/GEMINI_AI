import os
import google.generativeai as genai
from dotenv import load_dotenv


# 환경 변수 로드
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")



def ask_gemini(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Gemini 오류] {str(e)}"