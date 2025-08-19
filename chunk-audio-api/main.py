from fastapi import FastAPI, Query, UploadFile, File, Form

from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# test /eval-audio 용
import shutil


from tts.tts_module import text_to_speech_chunks
from services.audio_logic_service import process_user_audio, process_gemini_response, stream_audio_from_gridfs

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
async def chat_audio_to_voice(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    audio_bytes = await file.read()

    try:
        user_data = process_user_audio(user_id, audio_bytes)
        gemini_data = process_gemini_response(user_id, user_data["transcript"])
    except Exception as e:
        return {"error": str(e)}

    return {
        "user_input": user_data["transcript"],
        "gemini_reply": gemini_data["reply"],
        "tts_audio_path": gemini_data["audio_path"],
        "user_audio_id": user_data["audio_id"],
        "gemini_audio_id": gemini_data["audio_id"]
    }


# session 테이블에서 userId의 세션을 조회해 history를 끌고와서 gemini에게 줄 history 준비
# ex) http://127.0.0.1:8000/session/history?user_id=111
@app.get("/session/history")
def get_history(user_id: str = Query(..., description="조회할 사용자 ID")):
    session = db["Sessions"].find_one(
        {"userId": user_id},        
        {"history.role": 1, "history.content": 1, "_id": 0}  # projection
)
    if session and "history" in session:
        # history 배열에서 role과 content만 반환
        filtered_history = [
            {"role": item.get("role"), "content": item.get("content")}
            for item in session["history"]
        ]
        return {"history": filtered_history}
    
    return {"history": []}



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




# tts 테스트 코드

# @app.post("/generate/audio",
#           summary="text(ai 응답))")
# # 비동기 : tts
# async def generate_audio_from_text(
#     # 텍스트를 form 형식으로 보냄
#     # 이렇게 담게 되면 fastapi는 자동으로 multipart/form-data를 응답으로 기대
#     # Form 대신 Body로 json을 기대하게 할 수 있음
#     text: str = Form(...)
# ):
#     chunk_paths = text_to_speech_chunks(text, base_filename="tts_chunk", output_dir="output/chunk")
#     if not chunk_paths:
#         return {"error": "음성 변환 실패"}
#     # fastapi 에서 파일을 http 응답으로 반환하는 객체
#     return FileResponse(chunk_paths[0], media_type="audio/wav", filename=os.path.basename(chunk_paths[0]))


#############################################################################33
# ai audio 반환 테스트 endpoint
#   
# # /get-audio/{audio_id} → 저장된 GridFS 음성 스트리밍
# # gridFS란? 음성 동영상등 큰 크기의 파일을 저장하는 방식
# @app.get("/get-audio/{audio_id}")
# def get_audio(audio_id: str):
#     try:
#         return stream_audio_from_gridfs(audio_id)
#     except Exception as e:
#         return {"error": str(e)}
