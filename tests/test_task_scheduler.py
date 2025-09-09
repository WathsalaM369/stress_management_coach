import unittest
from datetime import datetime, timedelta
from agents.task_scheduler import AdaptiveTaskScheduler, MoodState

class TestAdaptiveTaskScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = AdaptiveTaskScheduler()
        
        # Create test tasks
        self.tasks = [
            {
                "id": "1",
                "title": "Complete project report",
                "description": "Finish the quarterly project report",
                "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                "priority": "high",
                "estimated_duration": 120,  # 2 hours
                "category": "work"
            },
            {
                "id": "2",
                "title": "Grocery shopping",
                "description": "Buy groceries for the week",
                "deadline": (datetime.now() + timedelta(days=3)).isoformat(),
                "priority": "medium",
                "estimated_duration": 60,  # 1 hour
                "category": "personal"
            },
            {
                "id": "3",
                "title": "Read research paper",
                "description": "Read and summarize the latest research paper",
                "deadline": (datetime.now() + timedelta(days=5)).isoformat(),
                "priority": "low",
                "estimated_duration": 90,  # 1.5 hours
                "category": "learning"
            }
        ]
        
        # Create test time blocks
        now = datetime.now()
        self.time_blocks = [
            {
                "start_time": now.replace(hour=9, minute=0, second=0).isoformat(),
                "end_time": now.replace(hour=11, minute=0, second=0).isoformat(),
                "is_available": True,
                "label": "Morning work block"
            },
            {
                "start_time": now.replace(hour=13, minute=0, second=0).isoformat(),
                "end_time": now.replace(hour=15, minute=0, second=0).isoformat(),
                "is_available": True,
                "label": "Afternoon work block"
            },
            {
                "start_time": now.replace(hour=16, minute=0, second=0).isoformat(),
                "end_time": now.replace(hour=17, minute=0, second=0).isoformat(),
                "is_available": True,
                "label": "Evening work block"
            }
        ]
        
        # Create test break activities
        self.break_activities = [
            {
                "id": "break1",
                "title": "Short walk",
                "description": "Take a 5-minute walk outside",
                "duration": 5,
                "stress_reduction": 0.3,
                "category": "physical"
            },
            {
                "id": "break2",
                "title": "Meditation",
                "description": "5-minute breathing meditation",
                "duration": 5,
                "stress_reduction": 0.5,
                "category": "mental"
            }
        ]
    
    def test_prioritize_tasks(self):
        """Test that tasks are prioritized correctly"""
        prioritized = self.scheduler._prioritize_tasks(
            self.tasks, 5, MoodState.FOCUSED
        )
        
        # High priority task should come first
        self.assertEqual(prioritized[0]['priority'], 'high')
        
        # Should have all tasks
        self.assertEqual(len(prioritized), 3)
    
    def test_stress_compatibility_calculation(self):
        """Test stress compatibility calculation"""
        task = self.tasks[0]  # High priority task
        
        # Test with high stress
        compatibility_high_stress = self.scheduler._calculate_stress_compatibility(
            task, 8, MoodState.TIRED
        )
        
        # Test with low stress
        compatibility_low_stress = self.scheduler._calculate_stress_compatibility(
            task, 3, MoodState.ENERGETIC
        )
        
        # Compatibility should be different based on stress level
        self.assertNotEqual(compatibility_high_stress, compatibility_low_stress)
        
        # Compatibility should be between 0 and 1
        self.assertTrue(0 <= compatibility_high_stress <= 1)
        self.assertTrue(0 <= compatibility_low_stress <= 1)
    
    def test_schedule_creation(self):
        """Test that a schedule is created successfully"""
        result = self.scheduler.process_inputs(
            stress_level=5,
            tasks=self.tasks,
            mood_state=MoodState.FOCUSED,
            time_blocks=self.time_blocks,
            break_activities=self.break_activities
        )
        
        # Should have optimized schedule in result
        self.assertIn("optimized_schedule", result)
        
        # Should have metadata
        self.assertIn("schedule_metadata", result)
        
        # Should have some tasks scheduled
        self.assertTrue(len(result["optimized_schedule"]) > 0)
    
    def test_high_stress_handling(self):
        """Test handling of high stress levels"""
        result = self.scheduler.process_inputs(
            stress_level=9,  # Very high stress
            tasks=self.tasks,
            mood_state=MoodState.SCATTERED,
            time_blocks=self.time_blocks,
            break_activities=self.break_activities
        )
        
        # Should potentially have workload alerts
        self.assertIn("workload_alerts", result)
        
        # Might have postponement suggestions for high stress
        self.assertIn("postponement_suggestions", result)
    
    def test_time_compatibility_calculation(self):
        """Test time compatibility calculation"""
        task = self.tasks[0]  # High priority task
        time_block = self.time_blocks[0]  # Morning block
        
        compatibility = self.scheduler._calculate_time_compatibility(
            task, time_block, MoodState.FOCUSED
        )
        
        # Compatibility should be between 0 and 1
        self.assertTrue(0 <= compatibility <= 1)

if __name__ == "__main__":
    unittest.main()