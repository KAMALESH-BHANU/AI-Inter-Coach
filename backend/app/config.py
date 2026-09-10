import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load .env from backend directory and workspace root
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Interview Coach"
    ENV: str = "development"
    PORT: int = 8000
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"

    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb+srv://Kamalesh:%40Kamalesh45@cluster0.txw76.mongodb.net/AI_Interview_Coach?retryWrites=true&w=majority&appName=Cluster0")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "AI_Interview_Coach")

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-key-ai-interview-coach-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Gemini & STT Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "tiny.en")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # Vision & Proctoring Configuration
    FACE_DETECTION_CONFIDENCE: float = float(os.getenv("FACE_DETECTION_CONFIDENCE", "0.5"))
    FACE_TRACKING_CONFIDENCE: float = float(os.getenv("FACE_TRACKING_CONFIDENCE", "0.5"))
    FRAME_SAMPLE_FPS: int = int(os.getenv("FRAME_SAMPLE_FPS", "5"))
    
    # Eye Contact Configuration Thresholds
    EYE_CONTACT_YAW_THRESHOLD: float = float(os.getenv("EYE_CONTACT_YAW_THRESHOLD", "25.0"))
    EYE_CONTACT_PITCH_THRESHOLD: float = float(os.getenv("EYE_CONTACT_PITCH_THRESHOLD", "25.0"))
    GAZE_HORIZONTAL_THRESHOLD: float = float(os.getenv("GAZE_HORIZONTAL_THRESHOLD", "0.40"))
    GAZE_VERTICAL_THRESHOLD: float = float(os.getenv("GAZE_VERTICAL_THRESHOLD", "0.40"))
    EYE_CONTACT_WINDOW_SIZE: int = int(os.getenv("EYE_CONTACT_WINDOW_SIZE", "15"))

    # Speech & Pause Configuration
    MIN_PAUSE_SECONDS: float = float(os.getenv("MIN_PAUSE_SECONDS", "0.8"))

    # Bounded Queue Sizes & Resource Controls
    MAX_AUDIO_QUEUE_SIZE: int = int(os.getenv("MAX_AUDIO_QUEUE_SIZE", "5"))
    MAX_VIDEO_QUEUE_SIZE: int = int(os.getenv("MAX_VIDEO_QUEUE_SIZE", "5"))
    VIDEO_TTL_MINUTES: int = int(os.getenv("VIDEO_TTL_MINUTES", "60"))
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp/interviews")

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
