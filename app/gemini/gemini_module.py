# chunk-audio-api/gemini/gemini_module.py

import os
from dotenv import load_dotenv
from operator import itemgetter 

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from db.history_module import get_user_history
# 로컬 모듈 임포트
from gemini.prompt_module import choose_chat_prompt
# from db.history_module import get_user_history # 실제 DB 모듈이 없으므로 임시 함수로 대체

# ----------------------------------------------------
# 임시 DB 함수 (실제 환경에서는 DB 모듈로 대체되어야 합니다)


# 1️⃣ 환경 변수 로드
load_dotenv()

# 2️⃣ Gemini 모델 초기화 (LangChain용)
# 환경 변수 설정: GEMINI_API_KEY=YOUR_API_KEY
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# 3️⃣ 사용자별 세션 처리 함수
def ask_gemini(session_id: str, user_input: str, scenario: str) -> str:
    try:
        # DB에서 과거 히스토리 불러오기 (session_id 또는 user_id 기반)
        history_data = get_user_history(session_id) 

        # LangChain Memory 객체 생성 및 과거 히스토리 로드
        memory = ConversationBufferMemory(
            memory_key="history",
            input_key="user_input",
            return_messages=True,
        )
        
        for turn in history_data:
            if turn["role"] == "user":
                memory.chat_memory.add_user_message(turn["content"])
            elif turn["role"] == "gemini":
                memory.chat_memory.add_ai_message(turn["content"])

        # 4️⃣ 프롬프트 템플릿 정의 
        system_message = choose_chat_prompt(scenario)
        
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="history"), # 변수: history
                ("human", "{user_input}")                    # 변수: user_input
            ]
        )

        # 5️⃣ 최종 체인 구성 (Runnable Sequence)
        # 🚨 수정: itemgetter 키를 "history"와 "user_input"으로 통일
        chain = (
            {
                "history": itemgetter("history"),  
                "user_input": itemgetter("user_input"),
            }
            | prompt_template 
            | llm
            | StrOutputParser()
        )

        # 6️⃣ 메모리 및 입력 데이터를 준비
        # 🚨 수정: input_data의 키를 "history"로 통일
        input_data = {
            # memory.load_memory_variables({})에서 memory_key인 "history"의 값을 가져옴
            "history": memory.load_memory_variables({})["history"], 
            "user_input": user_input
        }
        
        # 7️⃣ 모델 호출 (invoke 사용)
        response = chain.invoke(input_data)
        
        # 응답 후 현재 대화를 메모리에 추가 (다음 호출을 위해)
        memory.save_context({"user_input": user_input}, {"output": response})
        
        return response.strip()

    except Exception as e:
        return f"[Gemini 오류] {str(e)}"
