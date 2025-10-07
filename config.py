import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Wathsala's stress estimator configuration"""
    # Database
    DATABASE_PATH = 'stress_data.db'
    
    # Server
    PORT = 5001
    DEBUG = True
    
    # AI Model Paths (for future enhancements)
    SENTIMENT_MODEL_PATH = 'models/sentiment_model'
    
    # Thresholds
    HIGH_STRESS_THRESHOLD = 7
    MEDIUM_STRESS_THRESHOLD = 4
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

class Settings:
    """Senuthi's activity recommender configuration"""
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./stress_app.db")
        self.agent_port = int(os.getenv("AGENT_PORT", 5000))

# Create instances for easy access
config = Config()
settings = Settings()
