from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # ✅ 이제 v1 API에서 지원됨
    google_api_key=os.getenv("GEMINI_API_KEY")

)

print(llm.invoke("여보세요 주문 좀 하려고요"))
