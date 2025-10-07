#Vinushas
import os

class Config:
    # Database
    DATABASE_PATH = 'stress_data.db'
    
    # Server
    PORT = 5001
    DEBUG = True
    
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
    
    # AI Model Paths (for future enhancements) - from Wathsala
    SENTIMENT_MODEL_PATH = 'models/sentiment_model'
    
    # Security - from Wathsala
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
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