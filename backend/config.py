import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/shopdb")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "shopdb")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    SHOP_NAME = os.getenv("SHOP_NAME", "Shop Management")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
