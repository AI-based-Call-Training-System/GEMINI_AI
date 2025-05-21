from fastapi import FastAPI, WebSocket
from stt.stt_module import transcribe_audio
from gemini.gemini_module import ask_gemini
from tts.tts_module import text_to_speech
from vad.vad_module import is_speech_chunk
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse
import os
import uuid

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 * 가능 / 배포 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    await websocket.accept()
    audio_buffer = b""
    silence_counter = 0
    threshold = 20  # 몇 번 연속으로 침묵이면 '종단점'으로 간주할지

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer += data

            if is_speech_chunk(data):
                silence_counter = 0  # 말 중이면 리셋
            else:
                silence_counter += 1

            if silence_counter > threshold:
                print("📢 말 끝난 것 같아, STT 시작!")

                transcript = transcribe_audio(audio_buffer)
                response_text = ask_gemini(transcript)
                tts_path = text_to_speech(response_text)

                await websocket.send_json({
                    "transcript": transcript,
                    "response": response_text,
                    "audio_id": os.path.basename(tts_path)
                })

                # 초기화
                audio_buffer = b""
                silence_counter = 0

    except Exception as e:
        print(f"[에러] {e}")
        await websocket.close()
