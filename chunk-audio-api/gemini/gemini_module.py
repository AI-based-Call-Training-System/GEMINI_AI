# chunk-audio-api/gemini/gemini_module.py
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
# LLMChain 대신 LCEL을 사용할 것이므로 주석 처리하거나 삭제합니다.
# from langchain.chains import LLMChain 
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from operator import itemgetter # LCEL에서 입력을 구조화하기 위해 사용

from gemini.prompt_module import choose_chat_prompt
from db.history_module import get_user_history

# 1️⃣ 환경 변수 로드
load_dotenv()

# 2️⃣ Gemini 모델 초기화 (LangChain용)
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

        # 💡 LCEL (LangChain Expression Language)을 사용하여 체인 구성
        
        # 4️⃣ 프롬프트 템플릿 정의 (MessagesPlaceholder를 사용하여 메모리 주입)
        # choose_chat_prompt(scenario)는 시스템 메시지를 반환한다고 가정합니다.
        
        # history: 과거 대화 내용이 들어갈 자리
        # user_input: 현재 사용자의 입력이 들어갈 자리
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", choose_chat_prompt(scenario)),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{user_input}")
            ]
        )

        # 5️⃣ 최종 체인 구성 (Runnable Sequence)
        # itemgetter("user_input")으로 현재 입력을 전달하고,
        # itemgetter("history")로 메모리(과거 대화)를 전달합니다.
        
        # {
        #    "history": memory.load_memory_variables({})["history"], # 과거 대화 내용을 리스트 형태로 로드
        #    "user_input": itemgetter("user_input") # 현재 입력을 그대로 전달
        # }
        
        chain = (
            {
                "history": itemgetter("history_messages"), # 메모리 객체에서 메시지 리스트를 가져옵니다.
                "user_input": itemgetter("user_input"),
            }
            | prompt_template 
            | llm
            | StrOutputParser() # 응답을 깔끔한 문자열로 변환
        )

        # 6️⃣ 메모리 및 입력 데이터를 준비
        # invoke에 전달할 데이터를 딕셔너리로 만듭니다.
        # 메모리 로드: memory.load_memory_variables({})는 {"history": [Message, Message, ...]} 형태로 반환됩니다.
        # 따라서 "history_messages" 대신 메모리 키인 "history"를 사용해야 합니다.
        
        input_data = {
            # memory.load_memory_variables({})에서 memory_key인 "history"의 값을 가져옵니다.
            "history_messages": memory.load_memory_variables({})["history"], 
            "user_input": user_input
        }
        
        # 7️⃣ 모델 호출 (invoke 사용)
        response = chain.invoke(input_data)
        
        # 응답 후 현재 대화를 메모리에 추가 (다음 호출을 위해)
        memory.save_context({"user_input": user_input}, {"output": response})
        
        return response.strip()

    except Exception as e:
        return f"[Gemini 오류] {str(e)}"