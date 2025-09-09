#!/usr/bin/env python3
"""
Demo script to show the Adaptive Task Scheduler in action
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from agents.task_scheduler import AdaptiveTaskScheduler, MoodState

def demo_scheduler():
    print("🚀 ADAPTIVE TASK SCHEDULER DEMO")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = AdaptiveTaskScheduler()
    
    # Create comprehensive test data
    now = datetime.now()
    
    tasks = [
        {
            "id": "1",
            "title": "Complete project report",
            "description": "Finish the quarterly project report - break into chunks if stressed",
            "deadline": (now + timedelta(days=1)).isoformat(),
            "priority": "high",
            "estimated_duration": 120,
            "category": "work",
            "is_flexible": False
        },
        {
            "id": "2", 
            "title": "Grocery shopping",
            "description": "Buy groceries for the week",
            "deadline": (now + timedelta(days=3)).isoformat(),
            "priority": "medium", 
            "estimated_duration": 60,
            "category": "personal",
            "is_flexible": True
        },
        {
            "id": "3",
            "title": "Read research paper",
            "description": "Read and summarize the latest research paper",
            "deadline": (now + timedelta(days=5)).isoformat(),
            "priority": "low",
            "estimated_duration": 90,
            "category": "learning", 
            "is_flexible": True
        },
        {
            "id": "4",
            "title": "Team meeting",
            "description": "Weekly team sync meeting",
            "deadline": (now + timedelta(hours=4)).isoformat(),
            "priority": "high",
            "estimated_duration": 30,
            "category": "meeting",
            "is_flexible": False
        }
    ]
    
    time_blocks = [
        {
            "start_time": now.replace(hour=9, minute=0, second=0).isoformat(),
            "end_time": now.replace(hour=10, minute=30, second=0).isoformat(),
            "is_available": True,
            "label": "Morning focus time"
        },
        {
            "start_time": now.replace(hour=11, minute=0, second=0).isoformat(),
            "end_time": now.replace(hour=12, minute=30, second=0).isoformat(),
            "is_available": True,
            "label": "Late morning"
        },
        {
            "start_time": now.replace(hour=14, minute=0, second=0).isoformat(),
            "end_time": now.replace(hour=16, minute=0, second=0).isoformat(),
            "is_available": True,
            "label": "Afternoon block"
        },
        {
            "start_time": now.replace(hour=16, minute=30, second=0).isoformat(),
            "end_time": now.replace(hour=17, minute=30, second=0).isoformat(),
            "is_available": True,
            "label": "Late afternoon"
        }
    ]
    
    break_activities = [
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
            "title": "Deep breathing",
            "description": "5-minute breathing exercises",
            "duration": 5,
            "stress_reduction": 0.5,
            "category": "mental"
        },
        {
            "id": "break3",
            "title": "Quick stretch",
            "description": "3-minute stretching routine",
            "duration": 3,
            "stress_reduction": 0.2,
            "category": "physical"
        }
    ]
    
    # Test different scenarios
    scenarios = [
        {"stress": 2, "mood": MoodState.ENERGETIC, "name": "😊 LOW STRESS + ENERGETIC"},
        {"stress": 6, "mood": MoodState.FOCUSED, "name": "😐 MEDIUM STRESS + FOCUSED"},
        {"stress": 9, "mood": MoodState.TIRED, "name": "😫 HIGH STRESS + TIRED"},
        {"stress": 8, "mood": MoodState.SCATTERED, "name": "😵 HIGH STRESS + SCATTERED"}
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'='*60}")
        
        result = scheduler.process_inputs(
            stress_level=scenario["stress"],
            tasks=tasks,
            mood_state=scenario["mood"],
            time_blocks=time_blocks,
            break_activities=break_activities
        )
        
        print(f"📋 SCHEDULE OVERVIEW:")
        print(f"   Total tasks scheduled: {len(result['optimized_schedule'])}")
        print(f"   Total work time: {result['schedule_metadata']['total_work_hours']:.1f}h")
        print(f"   Total break time: {result['schedule_metadata']['total_break_time']:.1f}h")
        
        print(f"\n📅 SCHEDULED ITEMS:")
        for i, item in enumerate(result['optimized_schedule'], 1):
            task = item['task']
            time_block = item['time_block']
            start_time = datetime.fromisoformat(time_block['start_time']).strftime("%H:%M")
            end_time = datetime.fromisoformat(time_block['end_time']).strftime("%H:%M")
            
            emoji = "🧠" if "Break" in time_block.get('label', '') else "✅"
            print(f"   {i}. {emoji} {start_time}-{end_time}: {task.get('title', 'Unknown')}")
            if 'notes' in item and item['notes']:
                print(f"      📝 Notes: {item['notes']}")
        
        if result['workload_alerts']:
            print(f"\n⚠️  ALERTS:")
            for alert in result['workload_alerts']:
                print(f"   ⚠️  {alert['message']}")
                print(f"      💡 Suggestion: {alert['suggested_action']}")
        
        if result['postponement_suggestions']:
            print(f"\n📋 POSTPONEMENT SUGGESTIONS:")
            for suggestion in result['postponement_suggestions']:
                print(f"   📌 {suggestion['task_title']}")
                print(f"      📅 {suggestion['suggested_new_time']}")
        
        print(f"\n🎯 STRESS COMPATIBILITY SCORES:")
        for item in result['optimized_schedule']:
            if 'task' in item and 'stress_compatibility' in item:
                task = item['task']
                score = item['stress_compatibility']
                color = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                print(f"   {color} {task.get('title', 'Unknown')}: {score:.2f}/1.0")

if __name__ == "__main__":
    demo_scheduler()