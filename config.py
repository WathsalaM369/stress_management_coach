import os
from dotenv import load_dotenv

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

# config.py (Updated for Flask)
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./stress_app.db")
        self.agent_port = int(os.getenv("AGENT_PORT", 5000))

settings = Settings()