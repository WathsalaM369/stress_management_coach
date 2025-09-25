# The core stress detection agent that analyzes text input and returns stress levels.

import numpy as np
from flask import Flask, request, jsonify  # create the web API
from flask_cors import CORS
import re
import json
from datetime import datetime
import pandas as pd
import random
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.text_preprocessor import preprocess_text, sanitize_input, extract_stress_keywords

# Flask Web Server Setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def simple_sentiment_analysis(text):
    """
    Improved rule-based sentiment:
    - positive_words & negative_words store *magnitudes* (positive numbers).
    - negation applies for a short window (negation_window).
    - intensifiers amplify the next sentiment word.
    - normalization uses tanh to keep compound in (-1,1).
    """
    # Positive words and their weights (magnitudes)
    positive_words = {
        'good': 1, 'great': 1.5, 'excellent': 2, 'awesome': 1.5, 'wonderful': 1.5,
        'fantastic': 1.5, 'amazing': 1.5, 'perfect': 2, 'love': 2, 'like': 1,
        'happy': 1.5, 'joy': 1.5, 'pleased': 1, 'content': 1, 'satisfied': 1,
        'better': 1, 'best': 1.5, 'fine': 0.5, 'okay': 0.5, 'alright': 0.5,
        'calm': 1, 'relaxed': 1, 'peaceful': 1, 'grateful': 1, 'thankful': 1
    }

    # Negative words and their weights (magnitudes)
    negative_words = {
        'bad': 1, 'terrible': 2, 'awful': 2, 'horrible': 2, 'hate': 2,
        'dislike': 1.5, 'angry': 1.5, 'mad': 1.5, 'upset': 1.5, 'sad': 1.5,
        'unhappy': 1.5, 'depressed': 2, 'anxious': 2, 'worried': 1.5,
        'stressed': 2.5, 'overwhelmed': 2.5, 'tired': 1, 'exhausted': 1.5,
        'frustrated': 1.5, 'annoyed': 1, 'problem': 1, 'issue': 1,
        'difficult': 1, 'hard': 1, 'challenging': 0.5, 'struggle': 1.5,
        'panic': 2, 'nervous': 1.5, 'scared': 1.5, 'afraid': 1.5,
        'hopeless': 2, 'helpless': 2, 'lost': 1.5
    }

    # Intensifiers that amplify sentiment (multipliers)
    intensifiers = {
        'very': 1.5, 'really': 1.3, 'extremely': 1.7, 'quite': 1.2,
        'too': 1.3, 'so': 1.2, 'absolutely': 1.6, 'completely': 1.5,
        'totally': 1.4, 'utterly': 1.6
    }

    # Negation words
    negations = {'not', 'no', 'never', 'none', 'nothing', 'nobody', 'nowhere', "n't"}

    words = text.lower().split()
    sentiment_score = 0.0
    current_intensifier = 1.0
    negation_window = 0  # number of tokens left for which negation applies

    for word in words:
        # if this token is an intensifier, set multiplier (negation window still counts down)
        if word in intensifiers:
            current_intensifier = intensifiers[word]
        elif word in negations:
            # open a small negation window (applies to next up to N tokens)
            negation_window = 3
        elif word in positive_words:
            word_score = positive_words[word] * current_intensifier
            if negation_window > 0:
                # negation flips positive -> negative
                sentiment_score -= word_score
            else:
                sentiment_score += word_score
            # consume intensifier and negation
            current_intensifier = 1.0
            negation_window = 0
        elif word in negative_words:
            word_score = negative_words[word] * current_intensifier
            if negation_window > 0:
                # negation flips negative -> positive
                sentiment_score += word_score
            else:
                sentiment_score -= word_score
            current_intensifier = 1.0
            negation_window = 0
        else:
            # non-sentiment token: decay the negation window
            if negation_window > 0:
                negation_window -= 1
            # keep current_intensifier until a sentiment word consumes it (optional)

    # Normalize with tanh for stability (maps real -> -1..1 smoothly)
    # divisor chosen to control sensitivity (3 is a reasonable starting point)
    normalized_score = float(np.tanh(sentiment_score / 3.0))

    return {
        'compound': normalized_score,
        'positive': max(0.0, normalized_score),
        'negative': max(0.0, -normalized_score),
        'neutral': 1.0 - abs(normalized_score)
    }

class StressEstimator:
    def __init__(self):
        # thresholds (unchanged)
        self.stress_thresholds = {'low': 3.0, 'medium': 6.0, 'high': 10.0}
        self.stress_history = {}
        self.sample_data = self.load_sample_data()

    def load_sample_data(self):
        try:
            sample_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_stress_data.csv')
            if os.path.exists(sample_data_path):
                return pd.read_csv(sample_data_path)
            return None
        except:
            return None

    def analyze_sentiment(self, text):
        return simple_sentiment_analysis(text)

    def estimate_stress_level(self, text, user_id=None):
        # Preprocess and then use cleaned text for sentiment and keyword extraction
        cleaned_text = preprocess_text(text)

        # Sentiment & keywords on the cleaned text
        sentiment_scores = self.analyze_sentiment(cleaned_text)
        stress_keywords = extract_stress_keywords(cleaned_text)

        # Base score from sentiment: compound in [-1,1]
        # (1 - compound) * 2.5 --> range 0..5
        base_score = (1.0 - sentiment_scores['compound']) * 2.5

        # Keyword adjustment: scale depends on sentiment polarity strength
        if sentiment_scores['compound'] < -0.3:
            # strongly negative sentiment -> keywords matter more
            keyword_adjustment = min(len(stress_keywords) * 1.5, 3.0)
        elif sentiment_scores['compound'] > 0.3:
            # positive sentiment -> keywords less likely to indicate real stress
            keyword_adjustment = min(len(stress_keywords) * 0.5, 1.0)
        else:
            # neutral -> moderate weight
            keyword_adjustment = min(len(stress_keywords) * 1.0, 2.0)

        # Length adjustment (rumination signal) up to 2 points
        length_adjustment = min(len(cleaned_text.split()) * 0.1, 2.0)

        # Punctuation adjustment (exclamation intensity) up to 1 point
        exclamation_count = cleaned_text.count('!')
        punctuation_adjustment = min(exclamation_count * 0.2, 1.0)

        # Final score clamp to 0-10
        final_score = min(base_score + keyword_adjustment + length_adjustment + punctuation_adjustment, 10.0)
        final_score = max(0.0, final_score)

        # Categorize
        if final_score <= self.stress_thresholds['low']:
            level = "Low"
        elif final_score <= self.stress_thresholds['medium']:
            level = "Medium"
        else:
            level = "High"

        explanation = self.generate_explanation(level, stress_keywords, sentiment_scores, final_score, text)

        if user_id:
            self.update_stress_history(user_id, final_score, level)

        return {
            "stress_score": round(final_score, 1),
            "stress_level": level,
            "keywords": stress_keywords,
            "explanation": explanation,
            "sentiment_scores": sentiment_scores,
            "input_text": text
        }

    def generate_explanation(self, level, keywords, sentiment_scores, score, original_text):
        explanations = {
            "Low": [
                "You seem to be handling things well and maintaining a positive outlook.",
                "Your current stress levels appear manageable and within a healthy range.",
                "You're showing good resilience and coping strategies in your current situation."
            ],
            "Medium": [
                "You're showing some signs of stress but seem to be managing overall.",
                "There are some stressors present, but you appear to be coping reasonably well.",
                "You might benefit from some stress-reduction techniques to maintain balance."
            ],
            "High": [
                "You're experiencing significant stress that would benefit from attention.",
                "Your current stress levels are quite high, suggesting you may need support.",
                "It seems like you're dealing with multiple stressors that are impacting you."
            ]
        }

        base_explanation = random.choice(explanations[level])

        if keywords:
            keyword_str = ", ".join(keywords[:3])
            base_explanation += f" Keywords like '{keyword_str}' suggest specific stressors."

        if sentiment_scores['compound'] < -0.3:
            base_explanation += " Your language indicates negative emotions which may contribute to stress."
        elif sentiment_scores['compound'] > 0.3:
            base_explanation += " Your positive outlook helps mitigate stress."

        word_count = len(original_text.split())
        if word_count > 30:
            base_explanation += " The detailed description suggests you're giving this significant thought."
        elif word_count < 5:
            base_explanation += " The brief response might indicate you're not fully expressing your feelings."

        base_explanation += f" (Stress score: {score}/10)"

        return base_explanation

    def update_stress_history(self, user_id, score, level):
        if user_id not in self.stress_history:
            self.stress_history[user_id] = []
        self.stress_history[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "level": level
        })
        if len(self.stress_history[user_id]) > 100:
            self.stress_history[user_id] = self.stress_history[user_id][-100:]

    def get_stress_trend(self, user_id):
        if user_id not in self.stress_history or len(self.stress_history[user_id]) < 2:
            return None
        history = self.stress_history[user_id]
        recent_scores = [entry['score'] for entry in history[-5:]]
        if len(recent_scores) < 2:
            return "stable"
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
        if trend > 0.5:
            return "increasing"
        elif trend < -0.5:
            return "decreasing"
        else:
            return "stable"

# Initialize
estimator = StressEstimator()

@app.route('/estimate', methods=['POST'])
def estimate_stress():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing text input"}), 400
        text = data['text']
        user_id = data.get('user_id', 'anonymous')
        if not text.strip():
            return jsonify({"error": "Text input cannot be empty"}), 400
        text = sanitize_input(text)
        result = estimator.estimate_stress_level(text, user_id)
        trend = estimator.get_stress_trend(user_id)
        if trend:
            result['trend'] = trend
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Stress Level Estimator Agent",
        "description": "Accepts any text input and returns stress analysis"
    })

@app.route('/history/<user_id>', methods=['GET'])
def get_stress_history(user_id):
    if user_id in estimator.stress_history:
        return jsonify({
            "user_id": user_id,
            "history": estimator.stress_history[user_id],
            "count": len(estimator.stress_history[user_id])
        })
    else:
        return jsonify({
            "user_id": user_id,
            "message": "No history found for this user",
            "history": [],
            "count": 0
        })

if __name__ == '__main__':
    app.run(port=5001, debug=True)
