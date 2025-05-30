from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from tts.tts_module import text_to_speech_chunks
from services.audio_logic_service import process_user_audio, process_gemini_response, stream_audio_from_gridfs

# 환경 변수 로드
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /chat/audio → 히스토리 기반 AI 응답 및 음성 생성
@app.post("/chat/audio")
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

# /generate/audio → 단발 텍스트 TTS 변환
@app.post("/generate/audio")
async def generate_audio_from_text(
    text: str = Form(...)
):
    chunk_paths = text_to_speech_chunks(text, base_filename="tts_chunk", output_dir="output/chunk")
    if not chunk_paths:
        return {"error": "음성 변환 실패"}
    return FileResponse(chunk_paths[0], media_type="audio/wav", filename=os.path.basename(chunk_paths[0]))

# /get-audio/{audio_id} → 저장된 GridFS 음성 스트리밍
@app.get("/get-audio/{audio_id}")
def get_audio(audio_id: str):
    try:
        return stream_audio_from_gridfs(audio_id)
    except Exception as e:
        return {"error": str(e)}
