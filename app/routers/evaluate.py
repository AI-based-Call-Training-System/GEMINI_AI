# app/routers/evaluate.py
from fastapi import APIRouter,BackgroundTasks
from eval.get_wps_gap import (
    calculate_response_delay,
    calculate_whole_speech_rate,
)
from gemini.preprocess_his import *
from db.database import sessions_collection, fs
from eval.get_kobert import kobert_eval_preprocess
router = APIRouter()


@router.get("/evaluate_audio/{session_id}")
def get_score_about_4(session_id: str,background_tasks:BackgroundTasks):
    # 1. Session 문서 가져오기
    session_doc = sessions_collection.find_one({"sessionId": session_id})
    if not session_doc:
        raise ValueError(f"Session {session_id} not found")
    
    #태그값뽑기
    tags=session_doc["tags"]

    #대화내용 뽑기
    history = session_doc.get("history", [])
    if not history:
        return None
    

    #발화간극
    res_result=calculate_response_delay(history)
    print(res_result)
    gap=int(100 - round(abs(res_result["avg_delay"]*10 - 200) / 200 * 100, 1))
    gap_explain=res_result["gap_explain"]


    #발화속도
    rate_result=calculate_whole_speech_rate(history)
    print(rate_result)
    avg_rate=100-int(abs(rate_result["avg_rate"] - 200) / 200 * 100)
    wpm_explain=rate_result["rate_explain"]

    #####################################################


    # session저장 대화내용->가공-> prepare 테이블로 이동
    # 테이블에 저장 완료
    preprocess_session(session_id,tags)

    kobert_result=kobert_eval_preprocess(session_id)

    # 목표달성도
    goal_score=round(kobert_result["goal"]["score"],2)*100
    goal_label=kobert_result["goal"]["label"]
    
    # 맥락일관성
    cohereence_score=round(kobert_result["coherence"]["score"],2)*100
    cohereence_label=kobert_result["coherence"]["label"]

    r={
        "scores": [
            {
            "title": "목표 달성도",
            "score": goal_score,
            "comment": goal_label
            },
            {
            "title": "발화 속도",
            "score":  avg_rate,
            "comment": f"평균 속도 {avg_rate}W/m 으로, 일반인 평균 발화속도 150W/m{wpm_explain}니다."
            },
            {
            "title": "대화간격",
            "score": gap,
            "comment": gap_explain
            },
            {
            "title": "맥락 일관성",
            "score": cohereence_score,
            "comment": cohereence_label
            }
        ]
        }
    
    background_tasks.add_task(save_eval_result_to_db, session_id, r)

    print(r)
    return r


# 별도의 저장 함수 정의
def save_eval_result_to_db(session_id: str, result: dict):
    nest_url = "http://localhost:3000/eval_result/save"
    payload = {
        "session_id": session_id,
        "scores": result
    }

    try:
        response = requests.post(nest_url, json=payload)
        if response.status_code == 200:
            print("✅ NestJS 저장 성공:", response.json())
        else:
            print(f"⚠️ NestJS 저장 실패 ({response.status_code}):", response.text)
    except Exception as e:
        print("❌ NestJS 전송 오류:", e)


# preprocess 테이블 저장 테스트용
@router.get("/preprocess/{session_id}")
def preprocess_test(session_id: str):
    finaldata = preprocess_session(session_id)
    return finaldata
