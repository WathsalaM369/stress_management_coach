import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def safe_download_nltk_data():
    """Safely download required NLTK data with error handling"""
    try:
        nltk.data.find('tokenizers/punkt')
        print("NLTK punkt data already available")
    except LookupError:
        print("Downloading NLTK punkt data...")
        try:
            nltk.download('punkt', quiet=True)
            print("NLTK punkt data downloaded successfully")
        except Exception as e:
            print(f"Error downloading punkt data: {e}")
            return False
    
    try:
        nltk.data.find('corpora/stopwords')
        print("NLTK stopwords data already available")
    except LookupError:
        print("Downloading NLTK stopwords data...")
        try:
            nltk.download('stopwords', quiet=True)
            print("NLTK stopwords data downloaded successfully")
        except Exception as e:
            print(f"Error downloading stopwords data: {e}")
            return False
    
    return True

# Try to download NLTK data
nltk_data_available = safe_download_nltk_data()

def preprocess_text(text):
    """
    Preprocess text by cleaning and tokenizing
    """
    if not nltk_data_available:
        # Fallback if NLTK data is not available
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        return text
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    try:
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word not in stop_words]
        
        return ' '.join(filtered_tokens)
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        # Fallback to simple processing
        return text

def sanitize_input(text):
    """
    Sanitize user input to prevent injection attacks
    """
    # Remove potentially dangerous characters
    text = re.sub(r'[<>{}]', '', text)
    
    # Limit length to prevent DoS
    if len(text) > 1000:
        text = text[:1000]
        
    return text

def extract_stress_keywords(text):
    """
    Extract stress-related keywords using pattern matching
    """
    stress_patterns = [
    r'\b(stress|stressed|stressful|overwhelm|overwhelmed|anxious|anxiety)\b',
    r'\b(worry|worried|pressure|pressured|burntout|burnout|exhausted)\b',
    r'\b(deadline|exam|test|presentation|interview|meeting|assignment)\b',
    r'\b(can\'t cope|can\'t handle|too much|so much|drowning|overloaded)\b',
    r'\b(panic|nervous|tense|frustrated|annoyed|irritated|angry|mad)\b',  # Added more
    r'\b(depressed|sad|unhappy|miserable|hopeless|helpless|lost)\b'       # Added more
]
    
    keywords = []
    for pattern in stress_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)
        
    return list(set(keywords))