from fastapi import FastAPI, UploadFile, File, Form,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import gridfs
import librosa
import soundfile as sf
import io
from datetime import datetime
# test /eval-audio 용
import shutil


from tts.tts_module import text_to_speech_chunks
from services.audio_logic_service import process_user_audio, process_gemini_response
from eval.get_wps_gap import *
from pymongo import MongoClient

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017")
db = client["Call-Training-DB"]  # DB
fs = gridfs.GridFS(db)

sessions_collection = db["Sessions"]  # 컬렉션

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정
# 모든 도메인에서 접근 허용
# 실제 배포 시에는 필요한 도메인만 허용하도록 설정하는 것이 좋음
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /chat/audio → 히스토리 기반 AI 응답 및 음성 생성
@app.post("/chat/audio",
          summary="file,user_id-> ai 응답생성")
# header에 Authorization으로 token을 전달하면(flutter->fastapi 의 과정도중) session_id로 전달됨
# 문제원인을 아직도 파악 못함 왜지
async def chat_audio_to_voice(request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    session_id:str=Form(...),
    token: str=Form(...),
    scenario:str=Form(...)

):
    form = await request.form()
    # print(form) 
    # token= request.headers.get("Authorization")

    print("chat/audio로 부터 받은 token:",token)
    audio_bytes = await file.read()

    try:
        user_data = await process_user_audio(user_id, audio_bytes,session_id,token)
        gemini_data = await process_gemini_response(user_id, user_data["transcript"],session_id,token,scenario)
    except Exception as e:
        return {"error": str(e)}

    return {
        "user_input": user_data["transcript"],
        "gemini_reply": gemini_data["reply"],
        "tts_audio_path": gemini_data["audio_path"],
        "user_audio_id": user_data["audio_id"],
        "gemini_audio_id": gemini_data["audio_id"],
        "tts_audio_base64": gemini_data["tts_audio_base64"]
    }



@app.get("/evaluate_audio/{session_id}")
def get_average_speech_rate(session_id: str):
    # 1. Session 문서 가져오기
    session_doc = sessions_collection.find_one({"sessionId": session_id})
    if not session_doc:
        raise ValueError(f"Session {session_id} not found")

    history = session_doc.get("history", [])
    if not history:
        return None

    rates = []


    for message in history:
        message_id = message.get("messageId")
        content = message.get("content")
        if not content or not message_id:
            continue

        # 2. GridFS에서 해당 메시지 파일 찾기
        # 파일 이름에 sessionId가 포함되어 있다고 가정
        file_doc = fs.find_one({"filename": {"$regex": f"tester1"}})
        if not file_doc:
            print(f"⚠️ Audio file for {message_id} not found")
            continue

        # 3. 파일을 메모리로 읽기
        audio_bytes = file_doc.read()  # bytes

        # 4. calculate_speech_rate_active 함수 적용
        try:
            result = calculate_speech_rate(audio_bytes, content)
            if result:
                rates.append(result["words_per_min"])
        except Exception as e:
            print(f"⚠️ Error processing {message_id}: {e}")

    if not rates:
        return None

    avg_rate = sum(rates) / len(rates)
    return {
        "scores": [
            {
            "title": "목표 달성도",
            "score": 92,
            "comment": "주문 내용을 정확히 이해하고 응답했습니다."
            },
            {
            "title": "발화 속도",
            "score": (avg_rate).round(),
            "comment": "약간 빠른 편이지만 전반적으로 자연스러웠습니다."
            },
            {
            "title": "침묵 시간",
            "score": 85,
            "comment": "적절한 템포로 대화를 이어갔습니다."
            },
            {
            "title": "맥락 일관성",
            "score": 95,
            "comment": "대화 흐름이 자연스럽고 일관되었습니다."
            }
        ]
        }

# if __name__ == "__main__":
#     session_id = "S-01K6ZWCA052JXADC3D1KA84BBW"
#     avg = get_average_speech_rate(session_id)
#     print(f"Average speech rate: {avg:.2f} words/min")


