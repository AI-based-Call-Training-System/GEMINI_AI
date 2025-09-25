# chunk-audio-api/db/history_module.py
from datetime import datetime,timezone
from db.database import sessions_col
import httpx
import asyncio
NESTJS_URL = "http://localhost:3000/history"  # NestJS API 엔드포인트

# 기존에 바로 컬렉션에 저장되던 로직을
# fast->nest->mongo로 우회
async def save_detailed_history(user_id: str, session_id:str,role: str, content: str,token:str):
    print("sv dtl his2 들어옴")
    try:
        # ✅ NestJS로 메타데이터 전송
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {token}",  # 토큰 헤더
                "Content-Type": "application/json"
            }

            print("sv_dtl_hist2 정상작동:",content)
            payload = {
                "seq":1,
                "role": role,
                "content":content,
                "timestamp": datetime.now(timezone.utc).isoformat()  # 필요시 추가
            }
               # URL에 userId, sessionId 삽입
            url = f"{NESTJS_URL}/{user_id}/{session_id}/messages"

            resp = await client.post(url,headers=headers, json=payload)
            # 상태 코드 확인
            print("HTTP 상태 코드:", resp.status_code)

            # 성공 여부 확인
            if resp.status_code == 201:
                print("요청 성공")
            else:
                print("요청 실패:", resp.text)

            resp.raise_for_status()  # 오류 시 예외 발생
        

    except Exception as e:
        return {"error": str(e)}
    

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
