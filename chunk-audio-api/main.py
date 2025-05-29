from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from stt.stt_module import transcribe_audio
from gemini.gemini_module import ask_gemini
from tts.tts_module import text_to_speech, text_to_speech_chunks

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
    transcript = transcribe_audio(audio_bytes)
    if not transcript:
        return {"error": "음성 텍스트 감지 불가."}

    print("[STT 완료] 사용자 발화:", transcript)

    response_text = ask_gemini(user_id, transcript)
    print("[Gemini 응답 완료]:", response_text)

    # /output/audio 디렉터리에 저장
    wav_path = text_to_speech(response_text, output_dir="output/audio")
    print("[TTS 변환 완료]:", wav_path)

    return {
        "user_input": transcript,
        "gemini_reply": response_text,
        "tts_audio_path": wav_path
    }


# /generate/audio → 단발 텍스트 TTS 변환
@app.post("/generate/audio")
async def generate_audio_from_text(
    text: str = Form(...)
):
    # /output/chunk 디렉터리에 저장
    chunk_paths = text_to_speech_chunks(text, base_filename="tts_chunk", output_dir="output/chunk")

    if not chunk_paths:
        return {"error": "음성 변환 실패"}

    return FileResponse(chunk_paths[0], media_type="audio/wav", filename=os.path.basename(chunk_paths[0]))
