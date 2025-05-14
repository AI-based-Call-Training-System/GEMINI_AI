from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from stt.stt_module import transcribe_audio
from gemini.gemini_module import ask_gemini
from tts.tts_module import text_to_speech

app = FastAPI()

@app.get("/")
def read_root():
    return {"fastapi 연결완료 ㅊㅋㅊㅋ": "여긴 루트라 뭐 설정안해놈"}

@app.post("/chat/audio")
async def chat_audio_to_voice(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # 1. STT
    transcript = transcribe_audio(audio_bytes)
    if not transcript:
        return {"error": "음성에서 텍스트를 인식하지 못했습니다."}

    # 2. Gemini 응답 생성
    response_text = ask_gemini(transcript)

    # 3. TTS로 mp3 변환
    mp3_path = text_to_speech(response_text)

    # 4. mp3 파일 바로 응답
    return FileResponse(mp3_path, media_type="audio/mpeg", filename="response.mp3")
