# chunk-audio-api/db/history_module.py
from datetime import datetime
from db.database import sessions_col

def save_detailed_history(user_id: str, role: str, content: str, audio_id: str = None, audio_path: str = None, scenario_id: str = None):
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if audio_id:
        entry["audio_id"] = audio_id
    if audio_path:
        entry["audio_path"] = audio_path

    update_fields = {
        "$push": {"history": entry},
        "$set": {"updatedAt": datetime.utcnow().isoformat()}
    }
    if scenario_id:
        update_fields["$set"]["scenarioId"] = scenario_id

    sessions_col.update_one(
        {"userId": user_id},
        update_fields,
        upsert=True
    )

def save_to_history(user_id: str, role: str, content: str, scenario_id: str = None):
    save_detailed_history(user_id, role, content, scenario_id=scenario_id)

def get_user_history(user_id: str, limit: int = 4):
    doc = sessions_col.find_one({"userId": user_id})
    if doc and "history" in doc:
        return doc["history"][-limit:]
    return []

def reset_user_history(user_id: str):
    sessions_col.update_one(
        {"userId": user_id},
        {"$set": {"history": [], "updatedAt": datetime.utcnow().isoformat()}}
    )
