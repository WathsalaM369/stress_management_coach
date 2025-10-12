"""
Enhanced Adaptive Task Scheduler Agent
- Uses FETCHED stress data from Wathsala's stress estimator
- LLM ONLY for scheduling optimization (NOT stress assessment)
- Deadline-aware scheduling with Gemini
- Google Calendar export support
"""

import json
from datetime import datetime, timedelta
import os
import google.generativeai as genai
from dotenv import load_dotenv


class AdaptiveSchedulerAgent:
    """
    Intelligent scheduler that:
    - FETCHES stress data from the stress estimator system
    - Uses LLM ONLY for task scheduling (not stress assessment)
    - Provides deadline compliance
    - Generates Google Calendar exports
    """
    
    def __init__(self, use_llm=True):
        self.use_llm = use_llm
        self.llm_client = None
        
        print(f"🗓️ Initializing Adaptive Scheduler Agent")
        
        if use_llm:
            self.llm_client = self._setup_gemini()
            if self.llm_client:
                print("✅ Gemini client initialized for SCHEDULING ONLY")
                self.use_llm = True
            else:
                print("❌ Gemini setup failed, using rule-based scheduling")
                self.use_llm = False
    
    def _setup_gemini(self):
        """Setup Gemini client with error handling"""
        try:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key or api_key == 'your_actual_google_api_key_here':
                print("❌ GOOGLE_API_KEY not found or invalid")
                return None
            
            genai.configure(api_key=api_key)
            model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.0-flash-001')
            print(f"🤖 Using Gemini model for scheduling: {model_name}")
            
            model = genai.GenerativeModel(model_name)
            
            # Test connection
            test_response = model.generate_content("Say 'SCHEDULER_READY'")
            print(f"✅ Scheduler Gemini API test successful")
            return model
                
        except Exception as e:
            print(f"❌ Error in Gemini setup: {str(e)}")
            return None
    
    def generate_optimized_schedule(self, user_routine, tasks, stress_data, week_start, mood='neutral'):
        """
        Generate optimized schedule using FETCHED stress data
        
        Args:
            user_routine: User's weekly routine (from database)
            tasks: List of tasks to schedule
            stress_data: FETCHED from Wathsala's stress estimator (NOT assessed here)
            week_start: Start date of the week
            mood: User's mood (from stress estimator)
        """
        print(f"🎯 Generating schedule for week starting {week_start}")
        print(f"📊 Using FETCHED stress data: {stress_data.get('stress_level', 'Unknown')} ({stress_data.get('stress_score', 5)}/10)")
        print(f"📋 Tasks to schedule: {len(tasks)}")
        
        # Validate tasks
        for task in tasks:
            if not task.get('deadline'):
                task['deadline'] = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
            # NO default duration - LLM will calculate based on task context
        
        if self.use_llm and self.llm_client:
            return self._gemini_schedule(user_routine, tasks, stress_data, week_start, mood)
        else:
            return self._rule_based_schedule(user_routine, tasks, stress_data, week_start, mood)
    
    def _gemini_schedule(self, user_routine, tasks, stress_data, week_start, mood):
        """Generate schedule using Gemini - SCHEDULING ONLY (not stress assessment)"""
        print("🤖 Using Gemini AI for intelligent SCHEDULING...")
        
        prompt = self._build_scheduling_prompt(user_routine, tasks, stress_data, week_start, mood)
        
        try:
            response = self.llm_client.generate_content(prompt)
            schedule_data = self._parse_gemini_schedule_response(response.text)
            
            # Validate deadline compliance
            schedule_data = self._validate_deadlines(schedule_data, tasks)
            
            print(f"✅ AI schedule generated successfully")
            return schedule_data
            
        except Exception as e:
            print(f"❌ Gemini scheduling failed: {e}")
            return self._rule_based_schedule(user_routine, tasks, stress_data, week_start, mood)
    
    def _build_scheduling_prompt(self, user_routine, tasks, stress_data, week_start, mood):
        """Build prompt for SCHEDULING ONLY - stress data is already provided"""
        
        stress_score = stress_data.get('stress_score', 5)
        stress_level = stress_data.get('stress_level', 'Medium')
        
        # Sort tasks by urgency
        sorted_tasks = sorted(tasks, key=lambda x: (
            datetime.strptime(x['deadline'], '%Y-%m-%d') if x.get('deadline') else datetime(2099, 12, 31),
            0 if x.get('priority') == 'high' else (1 if x.get('priority') == 'medium' else 2)
        ))
        
        prompt = f"""You are an EXPERT AI Task Scheduler. Your job is to CREATE AN OPTIMAL SCHEDULE ONLY.

IMPORTANT: You are NOT assessing stress. The stress level has ALREADY been assessed by another AI system.

═══════════════════════════════════════════════════════════════
🎯 YOUR MISSION: SCHEDULE OPTIMIZATION
═══════════════════════════════════════════════════════════════
Create a weekly schedule that:
1. ✅ MEETS ALL DEADLINES (critical priority)
2. ⚡ Prioritizes HIGH priority + URGENT tasks
3. 🧠 Adapts to the PROVIDED stress level
4. 🔄 Balances workload intelligently
5. 🛡️ Includes appropriate breaks

═══════════════════════════════════════════════════════════════
📊 PROVIDED STRESS DATA (From Stress Estimator System)
═══════════════════════════════════════════════════════════════
Stress Level: {stress_level}
Stress Score: {stress_score}/10
Mood: {mood}

NOTE: This stress data was ALREADY ASSESSED. You only need to USE it for scheduling decisions.

═══════════════════════════════════════════════════════════════
📅 SCHEDULING CONTEXT
═══════════════════════════════════════════════════════════════
Week Starting: {week_start}
Total Tasks: {len(tasks)}

═══════════════════════════════════════════════════════════════
🗓️ USER'S WEEKLY ROUTINE (Available Time Slots)
═══════════════════════════════════════════════════════════════
{json.dumps(user_routine, indent=2)}

═══════════════════════════════════════════════════════════════
📋 TASKS TO SCHEDULE (Sorted by Urgency)
═══════════════════════════════════════════════════════════════
{json.dumps(sorted_tasks, indent=2)}

NOTE: For each task, calculate optimal duration based on:
- Task complexity (infer from name/priority)
- Available time slots
- User's stress level
- Deadline urgency

═══════════════════════════════════════════════════════════════
🎯 STRESS-ADAPTIVE SCHEDULING RULES
═══════════════════════════════════════════════════════════════

{self._get_stress_rules(stress_score)}

═══════════════════════════════════════════════════════════════
⚡ DEADLINE COMPLIANCE RULES
═══════════════════════════════════════════════════════════════
1. Schedule tasks with deadlines ≤2 days as URGENT (first priority)
2. Place high-priority tasks in morning hours (peak energy)
3. ALL tasks MUST be scheduled BEFORE their deadline
4. If a deadline is impossible to meet, add to warnings
5. Group similar tasks to reduce context switching

═══════════════════════════════════════════════════════════════
🚫 ABSOLUTE CONSTRAINTS
═══════════════════════════════════════════════════════════════
• NEVER schedule during "blocked" or "sleep" time slots
• NEVER exceed stress-based daily work hour limits
• NEVER schedule tasks after their deadline
• ALWAYS include buffers between tasks
• ALWAYS respect user's routine commitments

═══════════════════════════════════════════════════════════════
📤 OUTPUT FORMAT (VALID JSON ONLY)
═══════════════════════════════════════════════════════════════

{{
  "schedule": [
    {{
      "day": "Monday",
      "date": "2025-10-13",
      "total_work_hours": 5.5,
      "slots": [
        {{
          "time": "09:00-11:00",
          "task": "Task name",
          "priority": "High",
          "type": "work",
          "flexible": false,
          "deadline": "2025-10-15",
          "urgency": "urgent",
          "notes": "Due in 2 days - scheduled in peak energy time"
        }},
        {{
          "time": "11:00-11:15",
          "task": "Break - Deep breathing",
          "priority": "Medium",
          "type": "break",
          "flexible": false,
          "notes": "Stress relief break"
        }}
      ]
    }}
  ],
  "warnings": [
    "Any scheduling conflicts or deadline issues"
  ],
  "suggestions": [
    "Optimization tips for better productivity"
  ],
  "workload_analysis": {{
    "Monday": "balanced",
    "Tuesday": "light",
    "Wednesday": "heavy"
  }},
  "stress_adaptations": [
    "How schedule was adapted for the stress level"
  ],
  "deadline_compliance": [
    "Summary of deadline adherence"
  ]
}}

═══════════════════════════════════════════════════════════════
🎯 SCHEDULING STRATEGY
═══════════════════════════════════════════════════════════════
1. Calculate urgency for all tasks (days until deadline)
2. Identify time conflicts with user routine
3. Apply stress-based work hour limits
4. Schedule URGENT tasks first in morning slots
5. Balance remaining tasks across the week
6. Add stress-appropriate breaks
7. Verify ALL deadlines are met
8. Calculate optimal duration for each task
9. Generate actionable suggestions

CRITICAL: Return ONLY valid JSON. No markdown, no extra text.
"""
        
        return prompt
    
    def _get_stress_rules(self, stress_score):
        """Get stress-specific scheduling constraints"""
        if stress_score >= 7:
            return """🔴 HIGH STRESS MODE:
   • MAX 4-5 hours focused work per day
   • 15-20 minute buffer between tasks
   • Mandatory 10-minute break every hour
   • NO back-to-back difficult tasks
   • Prioritize easy tasks during afternoon
   • Include extra relaxation breaks"""
        elif stress_score >= 4:
            return """🟡 MEDIUM STRESS MODE:
   • MAX 6-7 hours focused work per day
   • 10-minute buffer between tasks
   • 5-minute break every 90 minutes
   • Balance difficult and easy tasks
   • Respect energy peaks for complex work"""
        else:
            return """🟢 LOW STRESS MODE:
   • Up to 8 hours productive work possible
   • Standard 5-minute buffers
   • Can handle challenging tasks
   • Back-to-back tasks acceptable if needed"""
    
    def _parse_gemini_schedule_response(self, response_text):
        """Parse Gemini's schedule response"""
        try:
            cleaned = response_text.strip()
            
            # Remove markdown formatting
            if '```json' in cleaned:
                json_start = cleaned.find('```json') + 7
                json_end = cleaned.find('```', json_start)
                cleaned = cleaned[json_start:json_end].strip()
            elif '```' in cleaned:
                json_start = cleaned.find('```') + 3
                json_end = cleaned.rfind('```')
                cleaned = cleaned[json_start:json_end].strip()
            
            schedule_data = json.loads(cleaned)
            
            # Validate required keys
            required_keys = ['schedule', 'warnings', 'suggestions']
            for key in required_keys:
                if key not in schedule_data:
                    schedule_data[key] = []
            
            # Add metadata
            schedule_data['generated_at'] = datetime.now().isoformat()
            schedule_data['generated_by'] = 'AdaptiveSchedulerAgent'
            schedule_data['llm_model'] = 'gemini'
            
            return schedule_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response preview: {response_text[:500]}")
            raise ValueError("Failed to parse Gemini response as JSON")
        except Exception as e:
            print(f"❌ Error parsing schedule: {e}")
            raise
    
    def _validate_deadlines(self, schedule_data, tasks):
        """Validate deadline compliance"""
        scheduled_tasks = set()
        warnings = list(schedule_data.get('warnings', []))
        
        # Extract scheduled tasks
        for day_schedule in schedule_data.get('schedule', []):
            for slot in day_schedule.get('slots', []):
                if slot.get('type') == 'work':
                    scheduled_tasks.add(slot.get('task'))
        
        # Check for missing tasks
        for task in tasks:
            if task['name'] not in scheduled_tasks:
                warnings.append(f"⚠️ Task '{task['name']}' could not be scheduled before deadline {task.get('deadline')}")
        
        # Check deadline violations
        for day_schedule in schedule_data.get('schedule', []):
            day_date = datetime.strptime(day_schedule['date'], '%Y-%m-%d')
            for slot in day_schedule.get('slots', []):
                if slot.get('deadline'):
                    deadline_date = datetime.strptime(slot['deadline'], '%Y-%m-%d')
                    if day_date > deadline_date:
                        warnings.append(f"❌ DEADLINE VIOLATION: '{slot['task']}' scheduled after deadline!")
        
        schedule_data['warnings'] = warnings
        return schedule_data
    
    def _rule_based_schedule(self, user_routine, tasks, stress_data, week_start, mood):
        """Fallback rule-based scheduling"""
        print("🔄 Using rule-based scheduling...")
        
        stress_score = stress_data.get('stress_score', 5)
        stress_level = stress_data.get('stress_level', 'Medium')
        
        # Stress-based limits
        if stress_score >= 7:
            max_daily_hours = 5
            buffer_minutes = 20
        elif stress_score >= 4:
            max_daily_hours = 6.5
            buffer_minutes = 10
        else:
            max_daily_hours = 8
            buffer_minutes = 5
        
        # Sort by urgency
        sorted_tasks = sorted(tasks, key=lambda x: (
            datetime.strptime(x.get('deadline', '2099-12-31'), '%Y-%m-%d'),
            0 if x.get('priority') == 'high' else 1
        ))
        
        schedule = []
        warnings = []
        week_date = datetime.strptime(week_start, '%Y-%m-%d')
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        task_index = 0
        for day_offset, day_name in enumerate(days):
            current_date = week_date + timedelta(days=day_offset)
            date_str = current_date.strftime('%Y-%m-%d')
            
            day_schedule = {
                'day': day_name,
                'date': date_str,
                'slots': [],
                'total_work_hours': 0
            }
            
            routine_slots = user_routine.get(day_name, [])
            work_slots = [slot for slot in routine_slots if slot.get('type') == 'work']
            
            daily_hours = 0
            for slot in work_slots:
                if task_index >= len(sorted_tasks) or daily_hours >= max_daily_hours:
                    break
                
                task = sorted_tasks[task_index]
                
                # Check deadline
                if task.get('deadline'):
                    deadline_date = datetime.strptime(task['deadline'], '%Y-%m-%d')
                    if current_date > deadline_date:
                        warnings.append(f"⚠️ Task '{task['name']}' deadline passed")
                        task_index += 1
                        continue
                
                duration_hours = min(task.get('duration', 2), max_daily_hours - daily_hours)
                
                start_time = slot['start']
                start_dt = datetime.strptime(start_time, '%H:%M')
                end_dt = start_dt + timedelta(hours=duration_hours)
                end_time = end_dt.strftime('%H:%M')
                
                days_until_deadline = (deadline_date - current_date).days if task.get('deadline') else 999
                urgency = 'urgent' if days_until_deadline <= 2 else 'normal'
                
                day_schedule['slots'].append({
                    'time': f"{start_time}-{end_time}",
                    'task': task['name'],
                    'priority': task.get('priority', 'medium').capitalize(),
                    'type': 'work',
                    'flexible': True,
                    'deadline': task.get('deadline'),
                    'urgency': urgency,
                    'notes': f"{task.get('priority', 'medium').capitalize()} priority - Due {task.get('deadline')}"
                })
                
                daily_hours += duration_hours
                
                # Add stress break
                if stress_score >= 7 and daily_hours < max_daily_hours:
                    break_end = (end_dt + timedelta(minutes=10)).strftime('%H:%M')
                    day_schedule['slots'].append({
                        'time': f"{end_time}-{break_end}",
                        'task': 'Stress relief break',
                        'priority': 'Medium',
                        'type': 'break',
                        'flexible': False,
                        'notes': 'Recommended for stress management'
                    })
                
                task_index += 1
            
            day_schedule['total_work_hours'] = round(daily_hours, 1)
            schedule.append(day_schedule)
        
        return {
            'schedule': schedule,
            'warnings': warnings,
            'suggestions': [
                f"Schedule optimized for {stress_level} stress",
                f"Daily work limit: {max_daily_hours}h",
                f"Buffer time: {buffer_minutes}min"
            ],
            'workload_analysis': {
                day['day']: 'balanced' if day['total_work_hours'] <= max_daily_hours else 'heavy'
                for day in schedule
            },
            'stress_adaptations': [
                f"Applied {max_daily_hours}h limit for {stress_level} stress",
                f"Added {buffer_minutes}min buffers"
            ],
            'deadline_compliance': [
                f"Scheduled {task_index} of {len(tasks)} tasks"
            ],
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'AdaptiveSchedulerAgent',
            'llm_model': 'rule_based'
        }


# Singleton instance
scheduler_agent = AdaptiveSchedulerAgent(use_llm=True)