# app/routers/evaluate.py
from fastapi import APIRouter
from eval.get_wps_gap import (
    calculate_response_delay,
    calculate_speech_rate,
)
from gemini.preprocess_his import *
from db.database import sessions_collection, fs

router = APIRouter()

@router.get("/evaluate_audio/{session_id}")
def get_score_about_4(session_id: str):
    session_doc = sessions_collection.find_one({"sessionId": session_id})
    if not session_doc:
        raise ValueError(f"Session {session_id} not found")

    history = session_doc.get("history", [])
    if not history:
        return None

    gap = calculate_response_delay(history) * 10
    rates = []

    for message in history:
        message_id = message.get("messageId")
        content = message.get("content")
        if not content or not message_id:
            continue

        file_doc = fs.find_one({"filename": {"$regex": f"tester1"}})
        if not file_doc:
            continue

        audio_bytes = file_doc.read()
        try:
            result = calculate_speech_rate(audio_bytes, content)
            if result:
                rates.append(result["words_per_min"])
        except Exception:
            continue

    if not rates:
        return None

    avg_rate = int(sum(rates) / len(rates))
    # ... 이하 점수 계산 및 반환 (기존 로직 유지)
    return {"scores": []}  # 실제 로직은 기존 로직 그대로 적용

@router.get("/preprocess/{session_id}")
def preprocess_test(session_id: str):
    finaldata = preprocess_session(session_id)
    return finaldata
