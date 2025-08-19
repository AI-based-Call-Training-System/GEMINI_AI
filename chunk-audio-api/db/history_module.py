# chunk-audio-api/db/history_module.py
from datetime import datetime,timezone
from db.database import sessions_col

# 히스토리 저장 함수
# 사용자 ID, 역할, 내용, 오디오 ID 및 경로를 받아 세션 컬렉션에 저장
def save_detailed_history(user_id: str, role: str, content: str, audio_id: str = None, audio_path: str = None, scenario_id: str = None):
    
    # 세션 컬렉션에 사용자 히스토리 저장
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # 오디오 ID와 경로가 제공된 경우 추가
    if audio_id:
        entry["audio_id"] = audio_id
    if audio_path:
        entry["audio_path"] = audio_path

    # 세션 업데이트 또는 생성
    # mongo db 업데이트
    # history 끝단에 entry추가 후 최근업데이트시간갱신 
    update_fields = {
        "$push": {"history": entry},
        "$set": {"updatedAt": datetime.now(timezone.utc).isoformat()}
    }

    # 시나리오 ID가 제공된 경우 추가
    if scenario_id:
        update_fields["$set"]["scenarioId"] = scenario_id

    # 세션 컬렉션에 업데이트
    sessions_col.update_one(
        {"userId": user_id}, 
        update_fields,
        upsert=True
    )

# 사용자 히스토리 저장 함수
def save_to_history(user_id: str, role: str, content: str, scenario_id: str = None):
    save_detailed_history(user_id, role, content, scenario_id=scenario_id)

# 사용자 히스토리 조회 함수
def get_user_history(user_id: str, limit: int = 4):
    doc = sessions_col.find_one({"userId": user_id})
    if doc and "history" in doc:
        return doc["history"][-limit:]
    return []

# 사용자 히스토리 초기화 함수
def reset_user_history(user_id: str):
    sessions_col.update_one(
        {"userId": user_id},
        {"$set": {"history": [], "updatedAt": datetime.utcnow().isoformat()}}
    )
