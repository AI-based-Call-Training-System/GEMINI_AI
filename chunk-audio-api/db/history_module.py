# chunk-audio-api/db/history_module.py
from datetime import datetime
from db.database import sessions_col

def save_to_history(user_id: str, role: str, content: str, scenario_id: str = None):
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }

    update_fields = {
        "$push": {"history": entry},
        "$set": {
            "updatedAt": datetime.utcnow().isoformat()
        }
    }

    if scenario_id:
        update_fields["$set"]["scenarioId"] = scenario_id

    sessions_col.update_one(
        {"userId": user_id},
        update_fields,
        upsert=True
    )


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
