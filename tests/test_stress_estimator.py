import unittest
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.stress_estimator import StressEstimator

class TestStressEstimator(unittest.TestCase):
    def setUp(self):
        # Initialize with no LLM for faster testing
        self.agent = StressEstimator(use_llm=False, use_database=False)
    
    def _create_test_data(self, text):
        """Helper method to create proper test data structure"""
        return {
            'assessment_data': {
                'user_message': text,
                'initialMood': {'input_method': 'text', 'text': text}
            },
            'user_id': 'test_user'
        }
    
    def test_high_stress_text(self):
        """Test with high-stress language"""
        test_data = self._create_test_data(
            "I'm completely overwhelmed with work and can't handle this pressure anymore."
        )
        result = self.agent.enhanced_comprehensive_analysis(test_data, 'test_user_1')
        
        # High stress should be 6.0 or above
        self.assertGreaterEqual(result['stress_score'], 6.0)
        print(f"✅ High stress test: {result['stress_level']} ({result['stress_score']}/10)")
    
    def test_medium_stress_text(self):
        """Test with moderate stress language"""
        test_data = self._create_test_data(
            "I have a lot to do but I'm managing okay. Just a bit tired."
        )
        result = self.agent.enhanced_comprehensive_analysis(test_data, 'test_user_2')
        
        # Medium stress should be between 3.0 and 7.0
        self.assertGreaterEqual(result['stress_score'], 3.0)
        self.assertLessEqual(result['stress_score'], 7.0)
        print(f"✅ Medium stress test: {result['stress_level']} ({result['stress_score']}/10)")
    
    def test_low_stress_text(self):
        """Test with positive, low-stress language"""
        test_data = self._create_test_data(
            "I'm feeling great today! Everything is going well."
        )
        result = self.agent.enhanced_comprehensive_analysis(test_data, 'test_user_3')
        
        # Low stress should be 4.0 or below
        self.assertLessEqual(result['stress_score'], 4.0)
        print(f"✅ Low stress test: {result['stress_level']} ({result['stress_score']}/10)")
    
    def test_empty_text(self):
        """Test with empty input"""
        test_data = self._create_test_data("")
        result = self.agent.enhanced_comprehensive_analysis(test_data, 'test_user_4')
        
        self.assertIn('stress_level', result)
        self.assertIn('stress_score', result)
        print(f"✅ Empty text test: {result['stress_level']} ({result['stress_score']}/10)")
    
    def test_stress_categories(self):
        """Test that all stress categories are valid"""
        valid_levels = ['Low', 'Medium', 'High', 'Very High', 'Chronic High']
        
        test_cases = [
            ("I'm so happy!", 'Low'),
            ("Work is stressful", 'Medium'),
            ("I can't handle this", 'High'),
            ("Everything is falling apart", 'Very High'),
            ("I've been stressed for months", 'Chronic High')
        ]
        
        for i, (text, expected_level) in enumerate(test_cases):
            test_data = self._create_test_data(text)
            result = self.agent.enhanced_comprehensive_analysis(test_data, f'category_test_{i}')
            self.assertIn(result['stress_level'], valid_levels)
            print(f"✅ Category test: '{text[:20]}...' -> {result['stress_level']} ({result['stress_score']}/10)")
    
    def test_response_structure(self):
        """Test that response has all expected fields"""
        test_data = self._create_test_data("Regular day with some stress")
        result = self.agent.enhanced_comprehensive_analysis(test_data, 'test_user_structure')
        
        # Check required fields
        required_fields = [
            'stress_score', 'stress_level', 'detailed_analysis', 
            'key_findings', 'timestamp'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing field: {field}")
        
        # Check data types
        self.assertIsInstance(result['stress_score'], (int, float))
        self.assertIsInstance(result['stress_level'], str)
        self.assertIsInstance(result['key_findings'], list)
        
        print(f"✅ Structure test: All fields present - Score: {result['stress_score']}, Level: {result['stress_level']}")

if __name__ == '__main__':
    # Run tests with more verbose output
    unittest.main(verbosity=2)