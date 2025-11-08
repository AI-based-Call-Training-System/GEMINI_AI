# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, evaluate

app = FastAPI(title="Call Training API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(evaluate.router, prefix="", tags=["Evaluation"])
