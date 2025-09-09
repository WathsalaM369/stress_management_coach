#!/usr/bin/env python3
"""
Interactive Task Scheduler - Users can input their actual tasks and get personalized schedules
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from agents.task_scheduler import AdaptiveTaskScheduler, MoodState

def get_user_input():
    """Get real input from the user"""
    print("🎯 PERSONALIZED TASK SCHEDULER")
    print("=" * 50)
    
    # Get stress level
    while True:
        try:
            stress_level = int(input("\n📊 Enter your current stress level (1-10, where 10 is highest): "))
            if 1 <= stress_level <= 10:
                break
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")
    
    # Get mood
    print("\n😊 How are you feeling today?")
    print("1. Energetic 💪")
    print("2. Tired 😴") 
    print("3. Focused 🎯")
    print("4. Scattered 🤯")
    
    mood_choice = input("Choose your mood (1-4): ")
    mood_map = {"1": "energetic", "2": "tired", "3": "focused", "4": "scattered"}
    mood = mood_map.get(mood_choice, "focused")
    
    # Get tasks
    print("\n📝 Enter your tasks (press Enter without title to finish):")
    tasks = []
    task_id = 1
    
    while True:
        print(f"\n--- Task {task_id} ---")
        title = input("Task title: ").strip()
        if not title:
            break
            
        description = input("Task description: ").strip()
        
        # Get deadline
        while True:
            deadline_input = input("Deadline (YYYY-MM-DD HH:MM or hours from now): ").strip()
            try:
                if ':' in deadline_input:  # Full datetime
                    deadline = datetime.strptime(deadline_input, "%Y-%m-%d %H:%M")
                else:  # Hours from now
                    hours = float(deadline_input)
                    deadline = datetime.now() + timedelta(hours=hours)
                break
            except ValueError:
                print("Please enter valid date/time or hours")
        
        # Get priority
        priority = input("Priority (high/medium/low): ").strip().lower()
        if priority not in ['high', 'medium', 'low']:
            priority = 'medium'
        
        # Get duration
        while True:
            try:
                duration = int(input("Estimated duration (minutes): "))
                break
            except ValueError:
                print("Please enter a valid number")
        
        # Get category
        category = input("Category (work/personal/learning/health): ").strip().lower()
        
        task = {
            "id": str(task_id),
            "title": title,
            "description": description,
            "deadline": deadline.isoformat(),
            "priority": priority,
            "estimated_duration": duration,
            "category": category,
            "is_flexible": True
        }
        
        tasks.append(task)
        task_id += 1
    
    # Get available time blocks
    print("\n⏰ Enter your available time blocks today:")
    time_blocks = []
    
    while True:
        print(f"\n--- Time Block {len(time_blocks) + 1} ---")
        start_input = input("Start time (HH:MM or 'done' to finish): ").strip()
        if start_input.lower() == 'done':
            break
            
        end_input = input("End time (HH:MM): ").strip()
        
        try:
            # Parse times
            start_time = datetime.now().replace(
                hour=int(start_input.split(':')[0]),
                minute=int(start_input.split(':')[1]),
                second=0
            )
            end_time = datetime.now().replace(
                hour=int(end_input.split(':')[0]),
                minute=int(end_input.split(':')[1]),
                second=0
            )
            
            time_block = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_available": True,
                "label": f"Block {len(time_blocks) + 1}"
            }
            
            time_blocks.append(time_block)
            
        except (ValueError, IndexError):
            print("Please enter time in HH:MM format")
    
    return {
        "stress_level": stress_level,
        "mood": mood,
        "tasks": tasks,
        "time_blocks": time_blocks
    }

def display_results(result):
    """Display the scheduling results in a user-friendly format"""
    print("\n" + "=" * 60)
    print("📅 YOUR PERSONALIZED SCHEDULE")
    print("=" * 60)
    
    print(f"\n📊 STRESS ANALYSIS:")
    print(f"   Your stress level: {result['stress_analysis']['level']}/10")
    print(f"   Impact: {result['stress_analysis']['impact_on_schedule']}")
    print(f"   Recommended actions: {', '.join(result['stress_analysis']['recommended_actions'])}")
    
    print(f"\n📋 TASK OVERVIEW:")
    print(f"   Total tasks: {result['task_analysis']['total_tasks']}")
    print(f"   Tasks scheduled: {result['task_analysis']['scheduled_tasks']}")
    print(f"   Priority breakdown: {result['task_analysis']['priority_distribution']}")
    print(f"   Overall deadline pressure: {result['task_analysis']['deadline_pressure']:.2f}/1.0")
    
    print(f"\n🧠 INTELLIGENT ANALYSIS:")
    if result['optimized_schedule']:
        for item in result['optimized_schedule']:
            task = item['task']
            time_block = item['time_block']
            
            if 'analysis' in task:
                analysis = task['analysis']
                
                # Parse times for display
                start_time = datetime.fromisoformat(time_block['start_time'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(time_block['end_time'].replace('Z', '+00:00'))
                
                print(f"\n⏰ {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}:")
                print(f"   📌 {task['title']}")
                print(f"   🕒 Duration: {task['estimated_duration']} minutes")
                print(f"   ⭐ Priority: {task['priority'].upper()} | 🎯 Score: {analysis['overall_priority']:.2f}")
                print(f"   😌 Stress fit: {analysis['stress_compatibility']:.2f} | 🧩 Complexity: {analysis['complexity_score']:.2f}")
                
                if 'scheduling_notes' in item and item['scheduling_notes']:
                    print(f"   💡 Note: {item['scheduling_notes'][0]}")
    else:
        print("   No tasks could be scheduled with available time blocks.")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for recommendation in result['insights']['recommended_adjustments']:
        print(f"   • {recommendation}")
    
    print(f"\n⏱️  TOTAL WORK TIME: {result['insights']['total_work_hours']:.1f} hours")
    print("=" * 60)

def main():
    """Main interactive function"""
    scheduler = AdaptiveTaskScheduler()
    
    # Get user input
    user_data = get_user_input()
    
    # Add some default break activities
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
        }
    ]
    
    # Analyze and schedule
    print("\n🧠 Analyzing your tasks and creating optimal schedule...")
    
    result = scheduler.analyze_and_schedule(
        stress_data={
            "stress_level": user_data["stress_level"],
            "reasons": ["User-reported stress level"]
        },
        tasks=user_data["tasks"],
        mood=user_data["mood"],
        available_blocks=user_data["time_blocks"]
    )
    
    # Display results
    display_results(result)
    
    # Show unscheduled tasks if any
    total_tasks = result['task_analysis']['total_tasks']
    scheduled_tasks = result['task_analysis']['scheduled_tasks']
    
    if scheduled_tasks < total_tasks:
        print(f"\n⚠️  {total_tasks - scheduled_tasks} tasks could not be scheduled.")
        print("   Consider adding more time blocks or postponing lower priority tasks.")

if __name__ == "__main__":
    main()