# chunk-audio-api/db/database.py
import os
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
fs = gridfs.GridFS(db)  # GridFS 초기화

# 사용할 컬렉션
users_col = db["Users"]        # 사용자 컬렉션
sessions_col = db["Sessions"]  # 대화 히스토리용 컬렉션
