import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Model settings
    MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
    MAX_LENGTH = 512
    
    # Stress mapping
    STRESS_MAPPING = {
        'anger': 8,
        'disgust': 7,
        'fear': 9,
        'joy': 2,
        'neutral': 4,
        'sadness': 9,
        'surprise': 5
    }
    
    # Thresholds
    HIGH_STRESS_THRESHOLD = 7
    MEDIUM_STRESS_THRESHOLD = 4

    # Task Scheduler Configuration
    MAX_WORK_HOURS_PER_DAY = int(os.getenv("MAX_WORK_HOURS_PER_DAY", 8))
    MIN_BREAK_DURATION = timedelta(minutes=5)
    MAX_BREAK_DURATION = timedelta(minutes=15)
    IDEAL_WORK_BLOCK_DURATION = timedelta(minutes=50)
    IDEAL_BREAK_FREQUENCY = timedelta(hours=1)
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 5000))
    
    # Security Configuration (if needed later)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

# Create config instance
config = Config()