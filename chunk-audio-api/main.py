from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from stt.stt_module import transcribe_audio
from gemini.gemini_module import ask_gemini
from tts.tts_module import text_to_speech
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 * 가능 / 배포 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat/audio")
async def chat_audio_to_voice(file: UploadFile = File(...)):
    audio_bytes = await file.read()



    # 1. STT
    transcript = transcribe_audio(audio_bytes)
    if not transcript:
        return {"error": "음성 텍스트 감지 불가."}
    
    print("stt완료")
    print(transcript) #사용자의 응답

    # 2. Gemini 응답 생성
    response_text = ask_gemini(transcript)

    print("gemini 응답생성 완료")
    print(response_text) #gemini의 응답

    # 3. TTS로 mp3 변환
    mp3_path = text_to_speech(response_text)
    print("tts 변환 완료")

    # 4. mp3 파일 바로 응답
    # return FileResponse(mp3_path, media_type="audio/mpeg", filename="response.mp3")
    return {"message": response_text}


