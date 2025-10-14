# chunk-audio-api/gemini/memory_module.py
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import AIMessage, HumanMessage
from db.history_module import get_user_history

# 기본 버전 (그냥 과거 대화 버퍼)
def init_memory_from_db(user_id: str, summary: bool = False):
    """
    DB에서 사용자 대화 이력을 불러와 LangChain 메모리 객체로 초기화
    summary=True일 경우, 긴 대화는 요약 메모리로 관리
    """
    history_data = get_user_history(user_id)

    # 1️⃣ 어떤 타입의 메모리를 쓸지 선택
    if summary:
        memory = ConversationSummaryMemory(
            llm=None,  # 나중에 Gemini 모델을 전달해도 됨
            memory_key="history",
            input_key="user_input",
            return_messages=True,
        )
    else:
        memory = ConversationBufferMemory(
            memory_key="history",
            input_key="user_input",
            return_messages=True,
        )

    # 2️⃣ DB에서 불러온 히스토리 추가
    for turn in history_data:
        if turn["role"] == "user":
            memory.chat_memory.add_message(HumanMessage(content=turn["content"]))
        elif turn["role"] == "gemini":
            memory.chat_memory.add_message(AIMessage(content=turn["content"]))

    return memory


def append_to_memory(memory, role: str, content: str):
    """현재 메모리에 새 메시지를 추가"""
    if role == "user":
        memory.chat_memory.add_user_message(content)
    elif role == "gemini":
        memory.chat_memory.add_ai_message(content)


"""
⚙️ 이걸 gemini_module에서 어떻게 쓰느냐면:
# chunk-audio-api/gemini/gemini_module.py
from gemini.memory_module import init_memory_from_db, append_to_memory
from gemini.prompt_module import chat_prompt
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from db.history_module import save_message

def ask_gemini(user_id: str, user_input: str):
    try:
        # 1️⃣ 메모리 초기화 (DB → LangChain 메모리 객체)
        memory = init_memory_from_db(user_id)

        # 2️⃣ LLM 체인 구성
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)
        chain = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)

        # 3️⃣ 모델 호출
        response = chain.run(user_input=user_input)

        # 4️⃣ 메모리 및 DB 업데이트
        append_to_memory(memory, "user", user_input)
        append_to_memory(memory, "gemini", response)
        save_message(user_id, "user", user_input)
        save_message(user_id, "gemini", response)

        return response.strip()
    except Exception as e:
        return f"[Gemini 오류] {str(e)}"
"""