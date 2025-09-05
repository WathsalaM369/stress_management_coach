import unittest
import sys
import os

# Add the parent directory to the path so we can import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.stress_estimator import StressEstimator
from utils.text_preprocessor import extract_stress_keywords, sanitize_input

class TestStressEstimator(unittest.TestCase):
    def setUp(self):
        self.estimator = StressEstimator()
    
    def test_low_stress_text(self):
        result = self.estimator.estimate_stress_level("I'm feeling good today")
        self.assertEqual(result['stress_level'], 'Low')
        self.assertLessEqual(result['stress_score'], 3.0)
    
    def test_medium_stress_text(self):
        result = self.estimator.estimate_stress_level("I have a lot of work to do")
        self.assertEqual(result['stress_level'], 'Medium')
        self.assertGreaterEqual(result['stress_score'], 3.1)
        self.assertLessEqual(result['stress_score'], 6.0)
    
    def test_high_stress_text(self):
        result = self.estimator.estimate_stress_level("I'm so overwhelmed with this deadline and I can't cope")
        self.assertEqual(result['stress_level'], 'High')
        self.assertGreaterEqual(result['stress_score'], 6.1)
    
    def test_keyword_extraction(self):
        keywords = extract_stress_keywords("I'm stressed about my exam and feeling overwhelmed")
        self.assertIn('stressed', keywords)
        self.assertIn('overwhelmed', keywords)
        self.assertIn('exam', keywords)
    
    def test_input_sanitization(self):
        sanitized = sanitize_input("Hello <script>alert('xss')</script> world")
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('</script>', sanitized)
    
    def test_stress_history(self):
        user_id = "test_user_123"
        result1 = self.estimator.estimate_stress_level("I'm feeling good", user_id)
        result2 = self.estimator.estimate_stress_level("I'm stressed", user_id)
        
        trend = self.estimator.get_stress_trend(user_id)
        self.assertIsNotNone(trend)
    
    def test_explanation_generation(self):
        result = self.estimator.estimate_stress_level("I'm worried about my exam")
        self.assertIn('explanation', result)
        self.assertIsInstance(result['explanation'], str)
        self.assertGreater(len(result['explanation']), 0)

if __name__ == '__main__':
    unittest.main()