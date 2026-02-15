
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Core
    APP_NAME: str = "Tiryaq Voice SaaS"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    # Firebase / Firestore
    FIRESTORE_PROJECT_ID: str = os.getenv("FIRESTORE_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Voice Config
    DEFAULT_PERSONA_PATH: str = "personas/tiryaq.json"
    SAMPLE_RATE: int = 16000
    VAD_SENSITIVITY: int = 3 # 1-3
    
    class Config:
        env_file = ".env"
        extra = "ignore" # Allow extra env variables

settings = Settings()
