from fastapi import FastAPI, Query, UploadFile, File, Form,Request

from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# test /eval-audio 용
import shutil


from tts.tts_module import text_to_speech_chunks
from services.audio_logic_service import process_user_audio, process_gemini_response

from pymongo import MongoClient

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017")
db = client["Call-Training-DB"]  # DB
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
async def chat_audio_to_voice(request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    session_id:str=Form(...),
    token: str=Form(...)

):
    form = await request.form()
    print(form) 
    audio_bytes = await file.read()

    try:
        user_data = await process_user_audio(user_id, audio_bytes,session_id,token)
        gemini_data = await process_gemini_response(user_id, user_data["transcript"],session_id,token)
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


@app.get("/evaluate-audio/")
#userId는 특정 세션,,,

# 세션-> 통화 평가 번호
async def evaluate_audio(userId: str = Query(...)):
    # 예: 서버에서 저장된 파일 경로 불러오기
    audio_path = f"saved_audios/{userId}.wav"

    # 실제 평가 함수 실행
    result = run_evaluation(audio_path)

    return JSONResponse(content={"userId": userId, "result": result})


#이걸로 일단 대체
def run_evaluation(audio_path):
    # 예시: 평가 모델 호출
    # 점수 반환 구조 예시
    return {
        # 텍스트 데이터
        "speech_speed": 75.0,
        "silence_time": 20.3,

        #음성데이터
        "context_consistency": 92.0,
        "goal_achievement": 87.5

    }



