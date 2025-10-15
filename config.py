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

    # LLM Configuration (FIXED: Added Gemini support)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # Default to Gemini
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Gemini Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
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
    
    @property
    def use_llm(self):
        """Check if LLM should be used"""
        use_llm_env = os.getenv("USE_LLM", "true").lower() == "true"
        has_gemini_key = bool(self.GOOGLE_API_KEY and self.GOOGLE_API_KEY != "your_actual_google_api_key_here")
        has_openai_key = bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY != "your_openai_api_key_here")
        
        return use_llm_env and (has_gemini_key or has_openai_key)
    
    @property
    def llm_config(self):
        """Get LLM configuration based on provider"""
        if self.LLM_PROVIDER == "gemini" and self.GOOGLE_API_KEY:
            return {
                "provider": "gemini",
                "api_key": self.GOOGLE_API_KEY,
                "model": self.GEMINI_MODEL
            }
        elif self.LLM_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return {
                "provider": "openai", 
                "api_key": self.OPENAI_API_KEY,
                "model": self.LLM_MODEL
            }
        else:
            return None

# Create a config instance (FIXED: This should be outside the class)
config = Config()