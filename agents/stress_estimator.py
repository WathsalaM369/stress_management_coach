import logging
from transformers import pipeline
from config import Config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class StressEstimatorAgent:
    def __init__(self):
        self.config = Config()
        logger.info("Initializing Stress Estimator Agent")

        # Initialize the emotion classification model
        try:
            self.classifier = pipeline(
                "text-classification",
                model=self.config.MODEL_NAME,
                top_k=None,
                max_length=self.config.MAX_LENGTH
            )
            logger.info("Emotion classification model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.classifier = None

    def estimate_stress_level(self, text: str) -> dict:
        """Estimate stress level from text input"""
        if not text or not text.strip():
            return {"stress_level": 0, "confidence": 0, "error": "No text provided"}

        try:
            # If model failed to load, return a default response
            if self.classifier is None:
                return {
                    "stress_level": 5.0,
                    "confidence": 0.7,
                    "message": "Using fallback estimation",
                    "error": "Model not loaded"
                }

            # Get emotion predictions
            predictions = self.classifier(text)

            if not predictions or not predictions[0]:
                return {"stress_level": 0, "confidence": 0, "error": "No predictions"}

            # Calculate stress score based on emotions
            stress_score = 0
            total_confidence = 0

            for emotion in predictions[0]:
                emotion_label = emotion["label"].lower()
                emotion_score = emotion["score"]

                if emotion_label in self.config.STRESS_MAPPING:
                    stress_value = self.config.STRESS_MAPPING[emotion_label]
                    stress_score += stress_value * emotion_score
                    total_confidence += emotion_score

            if total_confidence > 0:
                stress_level = stress_score / total_confidence
            else:
                stress_level = 5.0  # Default neutral

            return {
                "stress_level": round(stress_level, 2),
                "confidence": round(total_confidence, 2),
                "message": "Stress level estimated successfully"
            }

        except Exception as e:
            logger.error(f"Error in stress estimation: {e}")
            return {
                "stress_level": 5.0,
                "confidence": 0.5,
                "error": str(e),
                "message": "Fallback estimation due to error"
            }


# Create a singleton instance
stress_estimator = StressEstimatorAgent()
import logging
from config import Config

logger = logging.getLogger(__name__)

class StressEstimatorAgent:
    def __init__(self):
        self.config = Config()
        logger.info("Initializing Stress Estimator Agent")
        
        # Initialize the emotion classification model
        try:
            # For now, we'll use a simple approach without transformers
            # If you want to use transformers later, you can add it back
            logger.info("Using simple keyword-based stress estimation")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            self.model_loaded = False
    
    def estimate_stress_level(self, text: str) -> dict:
        """Estimate stress level from text input using keyword analysis"""
        if not text or not text.strip():
            return {"stress_level": 0, "confidence": 0, "error": "No text provided"}
        
        try:
            # Convert text to lowercase for easier matching
            text_lower = text.lower()
            
            # Stress keywords and their weights
            stress_keywords = {
                'overwhelmed': 8, 'stressed': 9, 'anxious': 8, 'panic': 9,
                'pressure': 7, 'deadline': 8, 'exhausted': 7, 'burnout': 9,
                'tired': 6, 'worried': 7, 'nervous': 7, 'frustrated': 7,
                'angry': 8, 'depressed': 9, 'sad': 7, 'hopeless': 9,
                'cannot sleep': 8, 'insomnia': 8, 'headache': 6
            }
            
            # Positive keywords (reduce stress score)
            positive_keywords = {
                'happy': -5, 'good': -4, 'relaxed': -6, 'calm': -6,
                'excited': -3, 'joy': -5, 'peaceful': -6, 'content': -5,
                'rested': -5, 'energy': -4, 'motivated': -4
            }
            
            # Calculate base stress score
            base_score = 5.0  # Neutral
            keyword_count = 0
            total_impact = 0
            
            # Check for stress keywords
            for keyword, weight in stress_keywords.items():
                if keyword in text_lower:
                    count = text_lower.count(keyword)
                    total_impact += weight * count
                    keyword_count += count
            
            # Check for positive keywords
            for keyword, weight in positive_keywords.items():
                if keyword in text_lower:
                    count = text_lower.count(keyword)
                    total_impact += weight * count
                    keyword_count += count
            
            # Calculate final stress level
            if keyword_count > 0:
                stress_level = base_score + (total_impact / keyword_count) / 2
            else:
                stress_level = base_score
            
            # Ensure stress level is between 0 and 10
            stress_level = max(0, min(10, stress_level))
            
            # Calculate confidence based on keyword matches
            confidence = min(0.9, keyword_count * 0.2) if keyword_count > 0 else 0.5
            
            logger.info(f"Estimated stress level: {stress_level} for text: {text[:50]}...")
            
            return {
                "stress_level": round(stress_level, 2),
                "confidence": round(confidence, 2),
                "message": "Stress level estimated using keyword analysis",
                "method": "keyword_matching"
            }
            
        except Exception as e:
            logger.error(f"Error in stress estimation: {e}")
            return {
                "stress_level": 5.0,
                "confidence": 0.5,
                "error": str(e),
                "message": "Fallback estimation due to error"
            }

# Create a singleton instance
stress_estimator = StressEstimatorAgent()