#!/usr/bin/env python3
"""
Test script to see the intelligent task analysis and scheduling
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from agents.task_scheduler import AdaptiveTaskScheduler, MoodState

def test_intelligent_analysis():
    print("🧠 INTELLIGENT TASK ANALYSIS DEMO")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = AdaptiveTaskScheduler()
    
    # Create test data with varying properties
    now = datetime.now()
    
    tasks = [
        {
            "id": "1",
            "title": "Complete quarterly financial report",
            "description": "Analyze Q3 financial data and prepare detailed report for management - complex analysis required",
            "deadline": (now + timedelta(hours=36)).isoformat(),  # Very urgent
            "priority": "high",
            "estimated_duration": 240,  # 4 hours
            "category": "work",
            "is_flexible": False
        },
        {
            "id": "2", 
            "title": "Grocery shopping",
            "description": "Buy weekly groceries and household supplies",
            "deadline": (now + timedelta(days=3)).isoformat(),
            "priority": "medium", 
            "estimated_duration": 90,  # 1.5 hours
            "category": "personal",
            "is_flexible": True
        },
        {
            "id": "3",
            "title": "Prepare client presentation",
            "description": "Create slides and materials for important client meeting",
            "deadline": (now + timedelta(days=2)).isoformat(),
            "priority": "high",
            "estimated_duration": 180,  # 3 hours
            "category": "work",
            "is_flexible": False
        },
        {
            "id": "4",
            "title": "Read research paper",
            "description": "Read and summarize latest AI research paper - complex technical content",
            "deadline": (now + timedelta(days=7)).isoformat(),
            "priority": "low",
            "estimated_duration": 120,  # 2 hours
            "category": "learning", 
            "is_flexible": True
        },
        {
            "id": "5",
            "title": "Quick team sync",
            "description": "15-minute daily team standup meeting",
            "deadline": (now + timedelta(hours=2)).isoformat(),  # Very urgent
            "priority": "high",
            "estimated_duration": 15,  # 0.25 hours
            "category": "meeting",
            "is_flexible": False
        }
    ]
    
    time_blocks = [
        {
            "start_time": now.replace(hour=9, minute=0, second=0).isoformat(),
            "end_time": now.replace(hour=12, minute=0, second=0).isoformat(),
            "is_available": True,
            "label": "Morning work block"
        },
        {
            "start_time": now.replace(hour=13, minute=0, second=0).isoformat(),
            "end_time": now.replace(hour=17, minute=0, second=0).isoformat(),
            "is_available": True,
            "label": "Afternoon work block"
        }
    ]
    
    # Test different stress scenarios
    stress_scenarios = [
        {
            "stress_level": 9,  # Very high stress
            "reasons": ["Work overload", "Tight deadlines", "Multiple urgent tasks"],
            "mood": "tired",
            "name": "😫 HIGH STRESS (9/10) + TIRED"
        },
        {
            "stress_level": 6,  # Medium stress
            "reasons": ["Moderate workload", "Some deadline pressure"],
            "mood": "focused", 
            "name": "😐 MEDIUM STRESS (6/10) + FOCUSED"
        },
        {
            "stress_level": 2,  # Low stress
            "reasons": ["Light workload", "Manageable deadlines"],
            "mood": "energetic",
            "name": "😊 LOW STRESS (2/10) + ENERGETIC"
        }
    ]
    
    for scenario in stress_scenarios:
        print(f"\n{'='*60}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'='*60}")
        
        # Create a fresh copy of tasks for each scenario
        scenario_tasks = [task.copy() for task in tasks]
        
        # Analyze and schedule
        result = scheduler.analyze_and_schedule(
            stress_data={
                "stress_level": scenario["stress_level"],
                "reasons": scenario["reasons"]
            },
            tasks=scenario_tasks,
            mood=scenario["mood"],
            available_blocks=time_blocks
        )
        
        # Display analysis results
        print(f"📊 STRESS ANALYSIS:")
        print(f"   Level: {result['stress_analysis']['level']}/10")
        print(f"   Impact: {result['stress_analysis']['impact_on_schedule']}")
        print(f"   Actions: {', '.join(result['stress_analysis']['recommended_actions'])}")
        
        print(f"\n📋 TASK ANALYSIS:")
        print(f"   Total tasks: {result['task_analysis']['total_tasks']}")
        print(f"   Scheduled: {result['task_analysis']['scheduled_tasks']}")
        print(f"   Priority distribution: {result['task_analysis']['priority_distribution']}")
        print(f"   Deadline pressure: {result['task_analysis']['deadline_pressure']:.2f}/1.0")
        
        print(f"\n🧠 TASK PRIORITIZATION ANALYSIS:")
        # Get the analyzed tasks from the result
        if result['optimized_schedule']:
            for item in result['optimized_schedule']:
                task = item['task']
                if 'analysis' in task:
                    analysis = task['analysis']
                    print(f"   📌 {task['title'][:35]}...")
                    print(f"      🕒 Urgency: {analysis['urgency_score']:.2f} | "
                          f"⭐ Importance: {analysis['importance_score']:.2f}")
                    print(f"      😌 Stress comp: {analysis['stress_compatibility']:.2f} | "
                          f"🧩 Complexity: {analysis['complexity_score']:.2f}")
                    print(f"      🎯 Overall priority: {analysis['overall_priority']:.2f}")
                    
                    # Show stress-specific notes
                    if 'simplification_notes' in analysis:
                        print(f"      💡 Notes: {analysis['simplification_notes'][0]}")
                    elif 'challenge_note' in analysis:
                        print(f"      💡 Note: {analysis['challenge_note']}")
                    
                    print()
        
        print(f"\n💡 INSIGHTS:")
        print(f"   Total work hours: {result['insights']['total_work_hours']:.1f}h")
        print(f"   Mood compatibility: {result['insights']['mood_compatibility']}")
        for recommendation in result['insights']['recommended_adjustments']:
            print(f"   💭 {recommendation}")
        
        print(f"\n{'='*60}")

if __name__ == "__main__":
    test_intelligent_analysis()