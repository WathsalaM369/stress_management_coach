import unittest
from agents.stress_estimator import StressEstimatorAgent

class TestStressEstimator(unittest.TestCase):
    def setUp(self):
        self.agent = StressEstimatorAgent()
    
    def test_high_stress_text(self):
        result = self.agent.estimate_stress_level(
            "I'm completely overwhelmed with work and can't handle this pressure anymore."
        )
        self.assertIn(result['stress_level'], ['High', 'Medium'])
        print(f"High stress test: {result}")
    
    def test_medium_stress_text(self):
        result = self.agent.estimate_stress_level(
            "I have a lot to do but I'm managing okay. Just a bit tired."
        )
        self.assertIn(result['stress_level'], ['Medium', 'Low'])
        print(f"Medium stress test: {result}")
    
    def test_low_stress_text(self):
        result = self.agent.estimate_stress_level(
            "I'm feeling great today! Everything is going well."
        )
        self.assertEqual(result['stress_level'], 'Low')
        print(f"Low stress test: {result}")

if __name__ == '__main__':
    unittest.main()