# app/routers/chat.py
from fastapi import APIRouter, UploadFile, File, Form, Request
from services.audio_logic_service import process_user_audio, process_gemini_response

router = APIRouter()

@router.post("/audio", summary="file,user_id -> ai 응답생성")
async def chat_audio_to_voice(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    session_id: str = Form(...),
    token: str = Form(...),
    scenario: str = Form(...)
):
    audio_bytes = await file.read()
    try:
        user_data = await process_user_audio(user_id, audio_bytes, session_id, token)
        gemini_data = await process_gemini_response(user_id, user_data["transcript"], session_id, token, scenario)
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
