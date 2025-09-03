import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, Tuple

from config import Config
from utils.text_preprocessor import TextPreprocessor

class StressEstimatorAgent:
    def __init__(self):
        self.config = Config()
        self.preprocessor = TextPreprocessor()
        
        # Load the emotion classification model
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.config.MODEL_NAME)
        
        # Create pipeline for emotion analysis
        self.emotion_analyzer = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            top_k=None
        )
    
    def estimate_stress_level(self, text: str) -> Dict:
        """
        Estimate stress level from text input
        
        Args:
            text (str): User's text input
            
        Returns:
            Dict: Contains stress level, score, and explanation
        """
        # Preprocess text
        cleaned_text = self.preprocessor.clean_text(text)
        
        # Get emotion predictions
        emotions = self.emotion_analyzer(cleaned_text)[0]
        
        # Calculate stress score based on emotions
        stress_score = self._calculate_stress_score(emotions)
        
        # Determine stress level
        stress_level = self._determine_stress_level(stress_score)
        
        # Generate explanation
        explanation = self._generate_explanation(stress_level, emotions, text)
        
        return {
            "stress_level": stress_level,
            "stress_score": stress_score,
            "explanation": explanation,
            "emotions": {e['label']: e['score'] for e in emotions}
        }
    
    def _calculate_stress_score(self, emotions: list) -> float:
        """Calculate stress score from emotion predictions"""
        weighted_sum = 0
        total_weight = 0
        
        for emotion in emotions:
            label = emotion['label']
            score = emotion['score']
            weight = self.config.STRESS_MAPPING.get(label, 5)  # Default to neutral
            weighted_sum += weight * score
            total_weight += score
        
        return weighted_sum / total_weight if total_weight > 0 else 5
    
    def _determine_stress_level(self, score: float) -> str:
        """Convert numerical score to stress level category"""
        if score >= self.config.HIGH_STRESS_THRESHOLD:
            return "High"
        elif score >= self.config.MEDIUM_STRESS_THRESHOLD:
            return "Medium"
        else:
            return "Low"
    
    def _generate_explanation(self, stress_level: str, emotions: list, original_text: str) -> str:
        """Generate explanation for the stress assessment"""
        top_emotion = max(emotions, key=lambda x: x['score'])
        
        explanations = {
            "High": [
                f"Your message indicates high stress, primarily showing {top_emotion['label']}.",
                f"Based on your words, you're experiencing significant stress with strong feelings of {top_emotion['label']}.",
                f"The intensity of {top_emotion['label']} in your message suggests high stress levels."
            ],
            "Medium": [
                f"You seem to be experiencing moderate stress, with elements of {top_emotion['label']}.",
                f"Your message shows moderate stress levels, influenced by feelings of {top_emotion['label']}.",
                f"There are signs of manageable stress in your message, particularly related to {top_emotion['label']}."
            ],
            "Low": [
                f"Your stress levels appear low, with a generally {top_emotion['label']} tone.",
                f"You seem to be handling things well, with primarily {top_emotion['label']} emotions detected.",
                f"Your message suggests low stress with a tendency toward {top_emotion['label']}."
            ]
        }
        
        # Select a random explanation from the appropriate category
        import random
        return random.choice(explanations[stress_level])