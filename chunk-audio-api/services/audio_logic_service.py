# app/services/audio_logic_service.py
from datetime import datetime
import uuid
from bson import ObjectId
import io
import os
from fastapi.responses import StreamingResponse

from db.database import fs
from db.history_module import save_detailed_history
from stt.stt_module import transcribe_audio
from gemini.gemini_module import ask_gemini
from tts.tts_module import text_to_speech

def process_user_audio(user_id: str, audio_bytes: bytes) -> dict:
    transcript = transcribe_audio(audio_bytes)
    if not transcript:
        raise ValueError("음성 텍스트 감지 실패")

    file_id = fs.put(audio_bytes, filename=f"user_{user_id}_{datetime.utcnow().isoformat()}")
    audio_path = f"output/audio/user/{str(file_id)}.wav"

    os.makedirs("output/audio/user", exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    save_detailed_history(
        user_id=user_id,
        role="user",
        content=transcript,
        audio_id=str(file_id),
        audio_path=audio_path
    )

    return {"transcript": transcript, "audio_id": str(file_id), "audio_path": audio_path}

def process_gemini_response(user_id: str, input_text: str) -> dict:
    response_text = ask_gemini(user_id, input_text)
    tts_path = text_to_speech(response_text, output_dir="output/audio/gemini")

    with open(tts_path, "rb") as f:
        audio_bytes = f.read()

    filename = f"tts_{uuid.uuid4().hex}.wav"
    file_id = fs.put(audio_bytes, filename=filename)
    audio_path = f"output/audio/gemini/{filename}"

    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    save_detailed_history(
        user_id=user_id,
        role="gemini",
        content=response_text,
        audio_id=str(file_id),
        audio_path=audio_path
    )

    return {"reply": response_text, "audio_id": str(file_id), "audio_path": audio_path}

def stream_audio_from_gridfs(audio_id: str):
    try:
        audio_data = fs.get(ObjectId(audio_id)).read()
        return StreamingResponse(io.BytesIO(audio_data), media_type="audio/wav")
    except Exception as e:
        raise RuntimeError(f"오디오 스트리밍 실패: {str(e)}")
