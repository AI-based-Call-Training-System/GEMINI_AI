
import os
import json
import re
import requests
from dotenv import load_dotenv
from operator import itemgetter 
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage # 💡 필요한 Import 추가
from db.history_module import get_user_history_all
# 로컬 모듈 임포트
from gemini.prompt_module import choose_chat_prompt
# from db.history_module import get_user_history # 실제 DB 모듈이 없으므로 임시 함수로 대체

# ----------------------------------------------------
# 임시 DB 함수 (실제 환경에서는 DB 모듈로 대체되어야 합니다)



def prep_for_scoring(session_id: str, scenario: str, llm) -> str:
    """
    세션의 대화 기록을 기반으로 프롬프트를 구성하고,
    LLM에게 전체 scoring JSON 생성을 요청하는 함수 (LangChain 제거 버전)
    """
    try:
        #1) DB에서 과거 히스토리 불러오기
        history_data = get_user_history_all(session_id)

        #2) history를 보기 좋게 문자열 형태로 변환
        # 예: user: 치킨 시킬게요. / gemini: 어떤 메뉴로 도와드릴까요?
        history_text = "\n".join(
            [f"{turn['role']}: {turn['content']}" for turn in history_data]
        )

        #3) 시스템 프롬프트 불러오기
        # choose_chat_prompt() 내부에서 get_prompt() 호출됨
        system_message = choose_chat_prompt(scenario, session_id)

        #4) 문자열 포맷 삽입 (.format 이용)
        # prep_order 프롬프트 내에 {history}, {session_id} 자리가 있어야 함
        prompt = system_message.format(
            history=history_text,
            session_id=session_id
        )

        # 모델 호출 (LangChain chain 제거, 단순 텍스트 입력)
        response_subject = llm.invoke(prompt)
        if isinstance(response_subject, AIMessage):
            response = response_subject.content

        # 출력 정리: dict이면 content 가져오기, 아니면 str로 변환
        # print("response",response)
        try:
            final_json_data = json.loads(response)
            # 🌟 성공! final_json_data는 이제 파이썬 딕셔너리입니다.
            # 이 딕셔너리를 원하는 대로 활용하거나, 문자열로 다시 반환하면 됩니다.

            #2차 수정을 위한 포맷 정리
            real_final_json_data=convert_to_final_format(final_json_data)
            return real_final_json_data 
            
        except json.JSONDecodeError as e:
            # 혹시 모를 오류 대비
            return f"[JSON 파싱 오류] {e}"
    except Exception as e:
        return f"[Gemini 오류] {str(e)}"


def convert_to_final_format(old_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 Mongo-style JSON 데이터를 최종 학습 포맷으로 변환합니다.
    """
    session_id = old_data.get("session_id", old_data.get("_id", "UNKNOWN_ID"))
    history = old_data.get("history", [])

    #1. history를 linearized 텍스트로 병합
    sep_token = "[SEP]"
    linearized_text = f" {sep_token} ".join([
        f"{h['role'].upper()}: {h['content']}" for h in history
    ])

    #2. 일정 길이 기준으로 window 분할 (예: 대화 turn 5개씩)
    window_size = 5
    windows = []
    for i in range(0, len(history), window_size):
        chunk = history[i:i + window_size]
        chunk_text = f" {sep_token} ".join([f"{h['role'].upper()}: {h['content']}" for h in chunk])
        windows.append({"text": chunk_text})

    #3. history 재구성 (messageId, seq 등 포함)
    new_history = []
    for idx, h in enumerate(history, start=1):
        new_history.append({
            "messageId": f"{session_id}-{idx}",
            "seq": idx,
            "role": h["role"],
            "content": h["content"],
            "timestamp": {"$date": None},
            "_id": {"$oid": None}
        })

    #4. 최종 포맷 구성
    final_data = {
        "_id": session_id,
        "preprocessId": session_id,
        "view": {
            "max_len_tokens": 256,
            "truncate": {
                "policy": "head_tail",
                "head_turns": 2,
                "tail_turns": 8
            },
            "linearize_sep": sep_token
        },
        "windows": windows,
        "linearized": {"text": linearized_text},
        "history": new_history,
    }

    #5. 추가 메타 정보 복사
    for key in ["goalSpec", "labels", "meta", "tags"]:
        if key in old_data:
            final_data[key] = old_data[key]

    #6. messageCount 자동 계산
    final_data["messageCount"] = len(history)

    return final_data

def preprocess_session(session_id:str):
    #1 환경 변수 로드
    load_dotenv()

    #2 Gemini 모델 초기화 (LangChain용)
    # 환경 변수 설정: GEMINI_API_KEY=YOUR_API_KEY
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    prep_result=prep_for_scoring(session_id,"prep_order",llm)


    #3 NestJS API에 저장
    url = "http://localhost:3000/preprocess/save"
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=prep_result)
    if res.status_code != 201:
        print(f"[Warning] NestJS 저장 실패: {res.status_code}, {res.text}")
    else:
        print("[Info] MongoDB preprocess 컬렉션에 저장 완료")

    return prep_result




