import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MoodState(Enum):
    ENERGETIC = "energetic"
    TIRED = "tired"
    FOCUSED = "focused"
    SCATTERED = "scattered"

class TaskPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AdaptiveTaskScheduler:
    def __init__(self):
        self.scheduled_tasks = []
        self.break_activities = []
        self.workload_alerts = []
        self.postponement_suggestions = []
    
    def process_inputs(self, stress_level: int, tasks: List[Dict], 
                      mood_state: MoodState, time_blocks: List[Dict],
                      break_activities: List[Dict]) -> Dict[str, Any]:
        """
        Main method to process all inputs and generate an optimized schedule
        """
        try:
            # Validate inputs
            self._validate_inputs(stress_level, tasks, mood_state, time_blocks, break_activities)
            
            # Store break activities
            self.break_activities = break_activities
            
            # Apply scheduling rules based on stress and mood
            prioritized_tasks = self._prioritize_tasks(tasks, stress_level, mood_state)
            
            # Schedule tasks with breaks
            optimized_schedule = self._schedule_tasks_with_breaks(
                prioritized_tasks, time_blocks, stress_level, mood_state
            )
            
            # Generate workload alerts if needed
            self._generate_workload_alerts(optimized_schedule, stress_level)
            
            # Generate postponement suggestions if stress is too high
            self._generate_postponement_suggestions(optimized_schedule, stress_level)
            
            return self._format_output(optimized_schedule)
            
        except Exception as e:
            logger.error(f"Error in processing inputs: {str(e)}")
            raise
    
    def _validate_inputs(self, stress_level: int, tasks: List[Dict], 
                        mood_state: MoodState, time_blocks: List[Dict],
                        break_activities: List[Dict]):
        """Validate all input parameters"""
        if not (1 <= stress_level <= 10):
            raise ValueError("Stress level must be between 1 and 10")
        
        if not tasks:
            raise ValueError("Task list cannot be empty")
        
        if not time_blocks:
            raise ValueError("Time blocks cannot be empty")
        
        if not isinstance(mood_state, MoodState):
            raise ValueError("Invalid mood state")
    
    def _prioritize_tasks(self, tasks: List[Dict], stress_level: int, 
                         mood_state: MoodState) -> List[Dict]:
        """
        Prioritize tasks based on stress level, mood, and deadlines
        """
        # Calculate priority scores for each task
        prioritized = []
        for task in tasks:
            # Base priority (higher number = higher priority)
            priority_score = 0
            
            # Priority based on task priority
            priority = task.get('priority', 'medium')
            if priority == 'high':
                priority_score += 3
            elif priority == 'medium':
                priority_score += 2
            else:
                priority_score += 1
            
            # Adjust based on deadline proximity (sooner deadlines get higher priority)
            if 'deadline' in task:
                deadline = datetime.fromisoformat(task['deadline'])
                days_until_deadline = (deadline - datetime.now()).days
                if days_until_deadline <= 1:
                    priority_score += 4
                elif days_until_deadline <= 3:
                    priority_score += 3
                elif days_until_deadline <= 7:
                    priority_score += 2
            
            # Adjust based on stress compatibility
            stress_compatibility = self._calculate_stress_compatibility(task, stress_level, mood_state)
            priority_score += stress_compatibility * 2  # Weight stress compatibility
            
            prioritized.append((task, priority_score))
        
        # Sort by priority score (descending)
        prioritized.sort(key=lambda x: x[1], reverse=True)
        
        return [task for task, score in prioritized]
    
    def _calculate_stress_compatibility(self, task: Dict, stress_level: int, 
                                      mood_state: MoodState) -> float:
        """
        Calculate how compatible a task is with current stress level and mood
        Returns a score between 0 and 1 (higher is more compatible)
        """
        compatibility = 0.5  # Base compatibility
        
        # Adjust based on stress level
        if stress_level >= 8:  # Very high stress
            # Better compatibility with shorter, less complex tasks
            estimated_duration = task.get('estimated_duration', 60)
            if estimated_duration <= 60:  # 1 hour or less
                compatibility += 0.2
            else:
                compatibility -= 0.3
        elif stress_level >= 5:  # Medium stress
            compatibility += 0.1
        else:  # Low stress
            # Better compatibility with longer, more complex tasks
            estimated_duration = task.get('estimated_duration', 60)
            if estimated_duration > 120:  # More than 2 hours
                compatibility += 0.2
        
        # Adjust based on mood
        if mood_state == MoodState.ENERGETIC:
            # Good for challenging tasks
            if task.get('priority') == 'high':
                compatibility += 0.2
        elif mood_state == MoodState.TIRED:
            # Better for simpler, routine tasks
            if task.get('priority') == 'low':
                compatibility += 0.2
            else:
                compatibility -= 0.1
        elif mood_state == MoodState.FOCUSED:
            # Good for complex tasks requiring concentration
            compatibility += 0.1
        elif mood_state == MoodState.SCATTERED:
            # Better for simpler, broken-down tasks
            description = task.get('description', '').lower()
            if "chunk" in description or "simple" in description:
                compatibility += 0.2
            else:
                compatibility -= 0.1
        
        # Ensure compatibility is between 0 and 1
        return max(0, min(1, compatibility))
    
    def _schedule_tasks_with_breaks(self, prioritized_tasks: List[Dict], 
                                   time_blocks: List[Dict], stress_level: int,
                                   mood_state: MoodState) -> List[Dict]:
        """
        Schedule tasks into time blocks with appropriate breaks
        """
        scheduled_tasks = []
        available_blocks = self._prepare_time_blocks(time_blocks)
        
        for task in prioritized_tasks:
            # Find the best time block for this task
            best_block, compatibility = self._find_best_time_block(
                task, available_blocks, stress_level, mood_state
            )
            
            if best_block:
                # Schedule the task
                scheduled_task = {
                    "task": task,
                    "time_block": best_block,
                    "stress_compatibility": compatibility,
                    "notes": self._generate_task_notes(task, stress_level, mood_state)
                }
                scheduled_tasks.append(scheduled_task)
                
                # Mark block as unavailable
                best_block['is_available'] = False
                best_block['assigned_task'] = task
                
                # Schedule breaks if needed (based on stress level and task duration)
                self._schedule_breaks_after_task(scheduled_task, available_blocks, stress_level)
        
        return scheduled_tasks
    
    def _prepare_time_blocks(self, time_blocks: List[Dict]) -> List[Dict]:
        """Prepare time blocks for scheduling by sorting and ensuring availability"""
        # Sort time blocks by start time
        sorted_blocks = sorted(time_blocks, key=lambda x: x['start_time'])
        
        # Only consider available blocks
        return [block for block in sorted_blocks if block.get('is_available', True)]
    
    def _find_best_time_block(self, task: Dict, available_blocks: List[Dict],
                             stress_level: int, mood_state: MoodState) -> (Optional[Dict], float):
        """
        Find the best time block for a task based on multiple factors
        """
        best_block = None
        best_compatibility = -1
        
        task_duration = task.get('estimated_duration', 60)
        
        for block in available_blocks:
            block_duration = self._calculate_block_duration(block)
            
            if block_duration >= task_duration:
                # Calculate time compatibility (time of day factors)
                time_compatibility = self._calculate_time_compatibility(task, block, mood_state)
                
                # Calculate overall compatibility
                compatibility = time_compatibility
                
                if compatibility > best_compatibility:
                    best_compatibility = compatibility
                    best_block = block
        
        return best_block, best_compatibility
    
    def _calculate_block_duration(self, time_block: Dict) -> int:
        """Calculate duration of a time block in minutes"""
        start_time = datetime.fromisoformat(time_block['start_time'])
        end_time = datetime.fromisoformat(time_block['end_time'])
        return int((end_time - start_time).total_seconds() / 60)
    
    def _calculate_time_compatibility(self, task: Dict, time_block: Dict,
                                    mood_state: MoodState) -> float:
        """
        Calculate how compatible a time block is with a task based on time of day
        """
        compatibility = 0.5  # Base compatibility
        
        start_time = datetime.fromisoformat(time_block['start_time'])
        hour = start_time.hour
        
        # Morning (6am-12pm) - good for focused work
        if 6 <= hour < 12:
            if mood_state == MoodState.FOCUSED and task.get('priority') == 'high':
                compatibility += 0.3
            elif task.get('category') in ["creative", "planning"]:
                compatibility += 0.2
        
        # Afternoon (12pm-5pm) - good for collaborative work
        elif 12 <= hour < 17:
            if task.get('category') in ["meeting", "collaboration"]:
                compatibility += 0.3
            elif mood_state == MoodState.ENERGETIC:
                compatibility += 0.2
        
        # Evening (5pm-10pm) - good for routine tasks
        elif 17 <= hour < 22:
            if task.get('priority') == 'low' or task.get('category') in ["routine", "maintenance"]:
                compatibility += 0.3
            else:
                compatibility -= 0.2
        
        # Night (10pm-6am) - generally not ideal for most tasks
        else:
            compatibility -= 0.4
        
        return max(0, min(1, compatibility))
    
    def _schedule_breaks_after_task(self, scheduled_task: Dict,
                                   available_blocks: List[Dict], stress_level: int):
        """
        Schedule breaks after tasks based on stress level and task duration
        """
        task = scheduled_task['task']
        time_block = scheduled_task['time_block']
        
        task_duration = task.get('estimated_duration', 60)
        start_time = datetime.fromisoformat(time_block['start_time'])
        task_end_time = start_time + timedelta(minutes=task_duration)
        
        # Determine break need based on stress level and task duration
        break_needed = False
        break_duration = 5  # Default short break in minutes
        
        if stress_level >= 7 or task_duration >= 60:
            break_needed = True
            if stress_level >= 7:
                break_duration = 15  # Longer break for high stress
            elif task_duration >= 120:
                break_duration = 10  # Medium break for long tasks
        
        if break_needed:
            # Find a time block right after the task for the break
            for block in available_blocks:
                if (block.get('is_available', True) and 
                    datetime.fromisoformat(block['start_time']) >= task_end_time and
                    self._calculate_block_duration(block) >= break_duration):
                    
                    # Select appropriate break activity
                    break_activity = self._select_break_activity(stress_level, break_duration)
                    
                    if break_activity:
                        # Schedule the break
                        break_block = {
                            'start_time': block['start_time'],
                            'end_time': (datetime.fromisoformat(block['start_time']) + 
                                        timedelta(minutes=break_duration)).isoformat(),
                            'is_available': False,
                            'label': f"Break: {break_activity.get('title', 'Rest')}"
                        }
                        scheduled_task['time_block']['assigned_task'] = break_activity
                        break
    
    def _select_break_activity(self, stress_level: int, 
                              available_duration: int) -> Optional[Dict]:
        """
        Select an appropriate break activity based on stress level and available time
        """
        if not self.break_activities:
            return None
            
        suitable_activities = [
            activity for activity in self.break_activities
            if activity.get('duration', 5) <= available_duration
        ]
        
        if not suitable_activities:
            return None
        
        # Sort by stress reduction effectiveness (descending)
        suitable_activities.sort(key=lambda x: x.get('stress_reduction', 0), reverse=True)
        
        # For high stress, prioritize high stress reduction activities
        if stress_level >= 7:
            return suitable_activities[0] if suitable_activities else None
        
        # For medium stress, balance duration and effectiveness
        if stress_level >= 4:
            # Prefer activities that use most of the available time but are effective
            suitable_activities.sort(
                key=lambda x: (x.get('stress_reduction', 0), 
                              x.get('duration', 5)/available_duration), 
                reverse=True
            )
            return suitable_activities[0] if suitable_activities else None
        
        # For low stress, any activity is fine
        return suitable_activities[0] if suitable_activities else None
    
    def _generate_workload_alerts(self, scheduled_tasks: List[Dict], stress_level: int):
        """
        Generate alerts if the schedule becomes overwhelming
        """
        total_work_minutes = 0
        
        for task in scheduled_tasks:
            if not task['time_block'].get('label', '').startswith("Break:"):
                total_work_minutes += task['task'].get('estimated_duration', 0)
        
        total_work_hours = total_work_minutes / 60
        
        # Alert if high stress and more than 6 hours of work
        if stress_level >= 7 and total_work_hours > 6:
            self.workload_alerts.append({
                "type": "high_stress_heavy_workload",
                "message": "High stress level combined with heavy workload detected",
                "suggested_action": "Consider rescheduling non-urgent tasks or adding more breaks",
                "total_work_hours": total_work_hours,
                "stress_level": stress_level
            })
        
        # Alert if more than 8 hours of work regardless of stress
        if total_work_hours > 8:
            self.workload_alerts.append({
                "type": "excessive_workload",
                "message": "Schedule exceeds recommended daily work hours",
                "suggested_action": "Consider postponing some tasks to maintain productivity and wellbeing",
                "total_work_hours": total_work_hours,
                "stress_level": stress_level
            })
    
    def _generate_postponement_suggestions(self, scheduled_tasks: List[Dict], 
                                          stress_level: int):
        """
        Generate suggestions for task postponement when stress is too high
        """
        if stress_level >= 8:  # Very high stress
            # Suggest postponing non-urgent tasks
            for task in scheduled_tasks:
                task_data = task['task']
                if (task_data.get('priority') == 'low' and 
                    task_data.get('is_flexible', True)):
                    self.postponement_suggestions.append({
                        "task_id": task_data.get('id', 'unknown'),
                        "task_title": task_data.get('title', 'Unknown Task'),
                        "reason": "High stress level reduces effectiveness for non-urgent tasks",
                        "suggested_new_time": "Tomorrow or when stress level decreases"
                    })
    
    def _generate_task_notes(self, task: Dict, stress_level: int, 
                            mood_state: MoodState) -> str:
        """
        Generate helpful notes for each scheduled task
        """
        notes = []
        
        # High stress suggestions
        if stress_level >= 7:
            if task.get('estimated_duration', 0) > 60:
                notes.append("Consider breaking this task into smaller chunks due to high stress")
            notes.append("Take short breaks every 25 minutes to maintain focus")
        
        # Mood-based suggestions
        if mood_state == MoodState.TIRED:
            notes.append("This might feel challenging given your current energy level")
        elif mood_state == MoodState.ENERGETIC:
            notes.append("Good time to tackle this with your current energy")
        elif mood_state == MoodState.SCATTERED:
            notes.append("Try minimizing distractions while working on this task")
        
        # Task-specific suggestions
        if task.get('priority') == 'high':
            notes.append("High priority task - focus on completion")
        
        return "; ".join(notes)
    
    def _format_output(self, scheduled_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Format the output for the scheduler
        """
        total_work_minutes = 0
        total_break_minutes = 0
        
        for task in scheduled_tasks:
            if task['time_block'].get('label', '').startswith("Break:"):
                total_break_minutes += task['task'].get('estimated_duration', 0)
            else:
                total_work_minutes += task['task'].get('estimated_duration', 0)
        
        return {
            "optimized_schedule": scheduled_tasks,
            "workload_alerts": self.workload_alerts,
            "postponement_suggestions": self.postponement_suggestions,
            "schedule_metadata": {
                "total_scheduled_tasks": len(scheduled_tasks),
                "total_work_hours": total_work_minutes / 60,
                "total_break_time": total_break_minutes / 60,
                "generated_at": datetime.now().isoformat()
            }
        }