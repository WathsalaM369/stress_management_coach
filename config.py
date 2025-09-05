import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Model paths
    SENTIMENT_MODEL_PATH = 'models/sentiment_model'
    NER_MODEL_PATH = 'models/ner_model'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Agent URLs
    STRESS_ESTIMATOR_URL = 'http://localhost:5001/estimate'