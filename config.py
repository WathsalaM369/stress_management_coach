import os

class Config:
    # Database
    DATABASE_PATH = 'stress_data.db'
    
    # Server
    PORT = 5001
    DEBUG = True
    
    # AI Model Paths (for future enhancements)
    SENTIMENT_MODEL_PATH = 'models/sentiment_model'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')