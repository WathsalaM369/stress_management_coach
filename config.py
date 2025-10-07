#Vinushas
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

    # LLM Configuration (FIXED: Removed the nested class)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Agent Configuration
    STRESS_ESTIMATOR_PORT = int(os.getenv("STRESS_ESTIMATOR_PORT", 8001))
    MOTIVATIONAL_AGENT_PORT = int(os.getenv("MOTIVATIONAL_AGENT_PORT", 8002))
    ACTIVITY_RECOMMENDER_PORT = int(os.getenv("ACTIVITY_RECOMMENDER_PORT", 8003))
    
    # API URLs
    BASE_URL = os.getenv("BASE_URL", "http://localhost")
    
    @property
    def stress_estimator_url(self):
        return f"{self.BASE_URL}:{self.STRESS_ESTIMATOR_PORT}"
    
    @property
    def motivational_agent_url(self):
        return f"{self.BASE_URL}:{self.MOTIVATIONAL_AGENT_PORT}"
    
    @property
    def activity_recommender_url(self):
        return f"{self.BASE_URL}:{self.ACTIVITY_RECOMMENDER_PORT}"

# Create a config instance (FIXED: This should be outside the class)
config = Config()