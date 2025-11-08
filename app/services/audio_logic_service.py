# app/services/audio_logic_service.py
from datetime import datetime,timezone
import uuid

import io
import os
from fastapi.responses import StreamingResponse

from db.database import fs
from db.history_module import save_detailed_history
from stt.stt_module import transcribe_audio
from gemini.gemini_module import ask_gemini
from tts.tts_module import text_to_speech
from pydub import AudioSegment

import subprocess
import tempfile
import os
import shutil
def convert_to_wav(input_bytes: bytes) -> str:
    """어떤 포맷이든 wav로 변환"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".input") as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in.flush()
        input_path = tmp_in.name

    output_path = input_path + ".wav"

    # ffmpeg 실행
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-ac", "1", "-ar", "16000",  # mono, 16kHz (STT 최적)
        output_path
    ], check=True)

    return output_path

async def process_user_audio(user_id: str, audio_bytes: bytes, session_id:str,token:str) -> dict:
    # 1. 업로드된 파일을 wav로 변환
    wav_path = convert_to_wav(audio_bytes)

    print("audio_logic_service: wav 변환 완료")
    # 2. 변환된 wav 파일을 STT에 전달
    with open(wav_path, "rb") as f:
        transcript = transcribe_audio(f.read())
    print("audio_logic_service:STT 전환 완료")

    if not transcript:
        raise ValueError("음성 텍스트 감지 실패:{transcript}")

    print("음성감지성공")

    # 3. DB/GridFS 저장
    print("db 저장 시도")

    file_id = fs.put(open(wav_path, "rb"), filename=f"user_{user_id}_{session_id}_{datetime.now(timezone.utc).isoformat()}")
    audio_path = f"output/audio/user/{str(file_id)}.wav"

    os.makedirs("output/audio/user", exist_ok=True)
    shutil.move(wav_path, audio_path)  # 변환 파일을 최종 저장소로 이동

# nestjs서버와 통신할 수 있게 변환한
# 새로운 버전의 save_detailed_history
    await save_detailed_history(
        role="user",
        user_id=user_id,
        session_id=session_id,
        content=transcript,
        token=token
    )
    return {"transcript": transcript, "audio_id": str(file_id), "audio_path": audio_path}

async def process_gemini_response(user_id: str, input_text: str,session_id:str,token:str,scenario:str) -> dict:
    response_text = ask_gemini(session_id, input_text,scenario)
    tts_path = text_to_speech(response_text, output_dir="output/audio/gemini")

    with open(tts_path, "rb") as f:
        audio_bytes = f.read()

    filename = f"tts_{uuid.uuid4().hex}.wav"
    file_id = fs.put(audio_bytes, filename=filename)
    audio_path = f"output/audio/gemini/{filename}"

    # mongodb에서 gemini의 음성을 빼와 전달
    # 파일 다시 읽어 클라이언트에 전송 (원하면 base64 혹은 바이너리로)
    
    # stored_file = fs.get(file_id)
    # wav_bytes = stored_file.read()
    wav_bytes=audio_bytes

    # base64로 변환
    import base64
    wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")

    await save_detailed_history(
        user_id=user_id,
        role="gemini",
        content=response_text,
        session_id=session_id,
        token=token
    )

    return {"reply": response_text, "audio_id": str(file_id), "audio_path": audio_path,"tts_audio_base64": wav_b64}

