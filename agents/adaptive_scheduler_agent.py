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
        
        # Sort tasks by SMART urgency (deadline + stress consideration)
        def calculate_urgency_score(task):
            if not task.get('deadline'):
                return (datetime(2099, 12, 31), 2)
            
            deadline_date = datetime.strptime(task['deadline'], '%Y-%m-%d')
            days_until = (deadline_date - datetime.strptime(week_start, '%Y-%m-%d')).days
            
            # If high stress and far deadline, lower the urgency
            if stress_score >= 7 and days_until > 7:
                urgency_modifier = 3  # Lower priority
            elif stress_score >= 4 and days_until > 5:
                urgency_modifier = 2
            else:
                urgency_modifier = 0 if task.get('priority') == 'high' else 1
            
            return (deadline_date, urgency_modifier)

        sorted_tasks = sorted(tasks, key=calculate_urgency_score)
        
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
⏰ TIME AWARENESS RULES - CRITICAL
═══════════════════════════════════════════════════════════════
CURRENT TIME: {current_time}
CURRENT DATE: {datetime.now().strftime('%Y-%m-%d')}

YOU MUST CHECK TIME:
1. For TODAY only: Skip any time slot that ENDS before {current_time}
   Example: Current time is 14:30
   - Slot 09:00-12:00 → SKIP (already passed)
   - Slot 13:00-14:00 → SKIP (already passed)
   - Slot 14:00-16:00 → SKIP (ends at 16:00 but starts before current time)
   - Slot 15:00-17:00 → CAN USE (starts after 14:30) ✅
   - Slot 18:00-20:00 → CAN USE ✅

2. For FUTURE DAYS (not today): Use all available slots normally

═══════════════════════════════════════════════════════════════
🚨 CRITICAL: SLOT TYPE FILTERING
═══════════════════════════════════════════════════════════════
BEFORE scheduling ANY task, you MUST:

1. Check the slot's "type" field
2. ONLY schedule work tasks in slots where type="work"
3. IGNORE all other slot types (blocked, sleep, hobby, leisure, exercise)

YOU CAN ONLY SCHEDULE TASKS IN SLOTS WHERE type="work"

ALLOWED:
✅ type="work" → Schedule tasks here

FORBIDDEN - NEVER SCHEDULE HERE:
❌ type="blocked" → User is unavailable
❌ type="sleep" → User is sleeping
❌ type="hobby" → Personal hobby time
❌ type="leisure" → Relaxation time
❌ type="exercise" → Exercise time

VALIDATION CHECKLIST FOR EVERY TASK:
[ ] Is the slot type="work"? If NO, skip this slot
[ ] Has this time already passed today? If YES, skip this slot
[ ] Does it fit the stress-based work hour limits? If NO, skip
[ ] Is it before the task deadline? If NO, add to warnings

If a day has NO "work" type slots, leave that day empty in the schedule!

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
6. if the person is too stress do not schdeule tasks at theat time.

1. Calculate days until deadline for each task
2. HIGH STRESS (≥7) + FAR DEADLINE (>7 days):
   - Do NOT schedule immediately
   - Start from day 3-4 of the week
   - Spread across multiple sessions
   
3. URGENT TASKS (deadline ≤2 days):
   - Schedule FIRST in earliest available "work" slots
   - Takes priority over everything
   
4. NORMAL TASKS (3-7 days):
   - Balance across the week
   - Respect stress limits

═══════════════════════════════════════════════════════════════
🚫 ABSOLUTE CONSTRAINTS
═══════════════════════════════════════════════════════════════
- NEVER EVER schedule ANY task during "blocked" or "sleep" slots
- NEVER schedule work tasks during "hobby", "leisure", or "exercise" slots
- ONLY use time slots marked as "work" type for task scheduling
- NEVER exceed stress-based daily work hour limits
- NEVER schedule tasks after their deadline
- ALWAYS include buffers between tasks
- ALWAYS respect user's routine commitments

CRITICAL: If a slot type is NOT "work", you CANNOT schedule a task there!

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
🧠 INTELLIGENT STRESS-BASED TASK DISTRIBUTION
═══════════════════════════════════════════════════════════════

HIGH STRESS (7-10) + FAR DEADLINE (>7 days):
- DO NOT schedule immediately
- Spread the task across multiple days
- Start scheduling from day 3-4 of the week
- Break large tasks into smaller sessions
- Prioritize urgent tasks with near deadlines FIRST

MEDIUM STRESS (4-6) + FAR DEADLINE (>5 days):
- Can schedule earlier but not urgent priority
- Balance with urgent tasks
- Use 2-3 day buffer from today

LOW STRESS (1-3):
- Normal scheduling - can start immediately if slots available
- Still prioritize by deadline urgency

DEADLINE URGENCY LEVELS:
- CRITICAL: 0-2 days → Schedule IMMEDIATELY in first available slots
- HIGH: 3-4 days → Schedule in first 2 days
- MEDIUM: 5-7 days → Schedule across 3-4 days  
- LOW: 8+ days → Spread across the week, avoid immediate scheduling if stress is high

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
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        

        start_date = max(week_date, today)  # Start from today or later
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        task_index = 0
        # Get current time for TODAY's scheduling
        now = datetime.now()
        current_hour_minute = now.hour * 60 + now.minute  # Convert to minutes

        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime('%Y-%m-%d')
            day_name = days[current_date.weekday()]

            if current_date < today:
                print(f"⏭️ Skipping {day_name} ({date_str}) - in the past")
                continue
            
            is_today = (current_date.date() == today.date())

            day_schedule = {
                'day': day_name,
                'date': date_str,
                'slots': [],
                'total_work_hours': 0
            }
            
            routine_slots = user_routine.get(day_name, [])
            
            work_slots = [slot for slot in routine_slots if slot.get('type') == 'work']

            print(f"📅 {day_name}: Found {len(work_slots)} work slots (filtered from {len(routine_slots)} total)")

            daily_hours = 0
            for slot in work_slots:
                # TIME CHECK: Skip slots that have already passed TODAY
                if is_today:
                    slot_end_time = slot['end']  # Format: "HH:MM"
                    slot_end_parts = slot_end_time.split(':')
                    slot_end_minutes = int(slot_end_parts[0]) * 60 + int(slot_end_parts[1])
                    
                    if slot_end_minutes <= current_hour_minute:
                        print(f"  ⏭️ Skipping {slot['start']}-{slot['end']} (already passed)")
                        continue
                
                # Ensure this is a WORK slot (double check)
                if slot.get('type') != 'work':
                    print(f"  ❌ Skipping {slot['start']}-{slot['end']} (type: {slot.get('type')})")
                    continue
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