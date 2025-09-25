import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"

class MoodState(Enum):
    ENERGETIC = "energetic"
    TIRED = "tired" 
    FOCUSED = "focused"
    SCATTERED = "scattered"

class Task:
    """Represents a task with priority and time requirements"""
    def __init__(self, name: str, duration: int, priority: TaskPriority, deadline: Optional[datetime] = None):
        self.name = name
        self.duration = duration  # in minutes
        self.priority = priority
        self.deadline = deadline
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "duration": self.duration,
            "priority": self.priority.value,
            "deadline": self.deadline.isoformat() if self.deadline else None
        }

class TimeBlock:
    """Represents a time block for scheduling"""
    def __init__(self, start_time: datetime, end_time: datetime, task: Optional[Task] = None):
        self.start_time = start_time
        self.end_time = end_time
        self.task = task
        self.duration = (end_time - start_time).total_seconds() / 60  # minutes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "task": self.task.to_dict() if self.task else None,
            "duration": self.duration
        }

class BreakActivity:
    """Represents a break activity"""
    def __init__(self, name: str, duration: int, type: str = "relaxation"):
        self.name = name
        self.duration = duration
        self.type = type
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "duration": self.duration,
            "type": self.type
        }

class AdaptiveTaskScheduler:
    def __init__(self):
        self.scheduled_tasks = []
        self.stress_rules = {
            "high_stress": {
                "threshold": 7,
                "max_work_hours": 6,
                "break_frequency": 30,  # minutes
                "complexity_penalty": 0.5
            },
            "medium_stress": {
                "threshold": 4,
                "max_work_hours": 8,
                "break_frequency": 60,
                "complexity_penalty": 0.8
            },
            "low_stress": {
                "threshold": 0,
                "max_work_hours": 10,
                "break_frequency": 90,
                "complexity_penalty": 1.0
            }
        }
    
    def analyze_and_schedule(self, stress_data: Dict, tasks: List[Dict], 
                           mood: str, available_blocks: List[Dict]) -> Dict[str, Any]:
        """
        Main method that analyzes stress and schedules tasks intelligently
        """
        try:
            # Extract stress information
            stress_level = stress_data.get('stress_level', 5)
            stress_reasons = stress_data.get('reasons', [])
            
            # Convert mood to enum
            mood_state = self._parse_mood_state(mood)
            
            # Analyze tasks
            analyzed_tasks = self._analyze_tasks(tasks, stress_level, mood_state)
            
            # Apply stress-based scheduling rules
            prioritized_tasks = self._apply_stress_rules(analyzed_tasks, stress_level)
            
            # Create schedule
            schedule = self._create_schedule(prioritized_tasks, available_blocks, stress_level, mood_state)
            
            # Generate insights
            insights = self._generate_insights(schedule, stress_level, mood_state)
            
            return {
                "optimized_schedule": schedule,
                "stress_analysis": {
                    "level": stress_level,
                    "impact": self._assess_stress_impact(stress_level),
                    "recommended_actions": self._get_stress_actions(stress_level)
                },
                "task_analysis": {
                    "total_tasks": len(tasks),
                    "scheduled_tasks": len(schedule),
                    "priority_distribution": self._get_priority_distribution(tasks),
                    "deadline_pressure": self._calculate_deadline_pressure(tasks)
                },
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in analysis and scheduling: {str(e)}")
            raise
    
    def _analyze_tasks(self, tasks: List[Dict], stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Analyze each task for scheduling compatibility"""
        analyzed_tasks = []
        
        for task in tasks:
            urgency_score = self._calculate_urgency_score(task)
            importance_score = self._calculate_importance_score(task)
            stress_compatibility = self._calculate_stress_compatibility(task, stress_level, mood_state)
            complexity_score = self._assess_complexity(task)
            
            overall_score = (
                urgency_score * 0.35 +
                importance_score * 0.3 +
                stress_compatibility * 0.25 +
                complexity_score * 0.1
            )
            
            analyzed_task = {
                **task,
                "analysis": {
                    "urgency_score": urgency_score,
                    "importance_score": importance_score,
                    "stress_compatibility": stress_compatibility,
                    "complexity_score": complexity_score,
                    "overall_priority": overall_score,
                    "recommended_duration": self._adjust_duration_for_stress(
                        task.get('estimated_duration', 60), stress_level
                    )
                }
            }
            
            analyzed_tasks.append(analyzed_task)
        
        return analyzed_tasks
    
    def _calculate_urgency_score(self, task: Dict) -> float:
        """Calculate task urgency based on deadline"""
        if 'deadline' not in task or not task['deadline']:
            return 0.5
        
        try:
            if isinstance(task['deadline'], str):
                deadline_str = task['deadline'].replace('Z', '+00:00')
                deadline = datetime.fromisoformat(deadline_str)
            else:
                deadline = task['deadline']
                
            now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
            time_until_deadline = (deadline - now).total_seconds()
            hours_until_deadline = time_until_deadline / 3600
            
            if hours_until_deadline <= 24:
                return 1.0
            elif hours_until_deadline <= 72:
                return 0.8
            elif hours_until_deadline <= 168:
                return 0.6
            else:
                return 0.4
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing deadline: {e}")
            return 0.5
    
    def _calculate_importance_score(self, task: Dict) -> float:
        """Calculate importance based on priority and category"""
        priority_map = {
            'high': 1.0,
            'medium': 0.7,
            'low': 0.4
        }
        
        category_weights = {
            'work': 0.9,
            'health': 0.95,
            'finance': 0.85,
            'education': 0.8,
            'personal': 0.6,
            'leisure': 0.4
        }
        
        priority_score = priority_map.get(task.get('priority', 'medium'), 0.5)
        category_score = category_weights.get(task.get('category', 'personal'), 0.5)
        
        return (priority_score * 0.6 + category_score * 0.4)
    
    def _calculate_stress_compatibility(self, task: Dict, stress_level: int, mood_state: MoodState) -> float:
        """Calculate how compatible a task is with current stress level"""
        base_compatibility = 1.0 - (stress_level / 20)
        
        complexity = self._assess_complexity(task)
        if stress_level > 6 and complexity > 0.7:
            base_compatibility *= 0.6
        
        mood_adjustment = self._get_mood_adjustment(mood_state, task)
        base_compatibility *= mood_adjustment
        
        duration = task.get('estimated_duration', 60)
        if stress_level > 5 and duration > 120:
            base_compatibility *= 0.8
        
        return max(0.1, min(1.0, base_compatibility))
    
    def _assess_complexity(self, task: Dict) -> float:
        """Assess task complexity based on duration and keywords"""
        duration = task.get('estimated_duration', 60)
        description = task.get('description', '').lower()
        title = task.get('title', '').lower()
        
        complexity = 0.5  # Base complexity
        
        # Adjust based on duration
        if duration > 180:
            complexity += 0.3
        elif duration > 120:
            complexity += 0.2
        elif duration > 60:
            complexity += 0.1
        
        # Adjust based on keywords
        text = f"{title} {description}"
        complex_keywords = ['complex', 'difficult', 'challenging', 'detailed', 'analysis', 'technical', 'report']
        simple_keywords = ['simple', 'easy', 'quick', 'routine', 'basic']
        
        if any(keyword in text for keyword in complex_keywords):
            complexity += 0.2
        if any(keyword in text for keyword in simple_keywords):
            complexity -= 0.2
        
        return max(0.1, min(1.0, complexity))
    
    def _get_mood_adjustment(self, mood_state: MoodState, task: Dict) -> float:
        """Get adjustment factor based on mood and task type"""
        adjustments = {
            MoodState.ENERGETIC: 1.2 if self._assess_complexity(task) > 0.6 else 1.0,
            MoodState.TIRED: 0.6 if self._assess_complexity(task) > 0.6 else 1.1,
            MoodState.FOCUSED: 1.4 if self._assess_complexity(task) > 0.6 else 1.0,
            MoodState.SCATTERED: 0.5 if self._assess_complexity(task) > 0.6 else 1.2
        }
        
        return adjustments.get(mood_state, 1.0)
    
    def _apply_stress_rules(self, tasks: List[Dict], stress_level: int) -> List[Dict]:
        """Apply stress-based rules and sort by priority"""
        # Sort by overall priority
        tasks.sort(key=lambda x: x['analysis']['overall_priority'], reverse=True)
        
        # Apply stress-specific modifications
        stress_category = self._get_stress_category(stress_level)
        rules = self.stress_rules[stress_category]
        
        for task in tasks:
            if task['analysis']['complexity_score'] > 0.7 and stress_level >= 7:
                task['analysis']['stress_note'] = "Consider breaking this complex task into smaller parts"
                task['analysis']['recommended_duration'] *= 1.3
        
        return tasks
    
    def _create_schedule(self, tasks: List[Dict], time_blocks: List[Dict], 
                        stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Create optimized schedule"""
        schedule = []
        available_blocks = [block for block in time_blocks if block.get('is_available', True)]
        
        for i, task in enumerate(tasks):
            if i < len(available_blocks):
                time_block = available_blocks[i]
                scheduled_item = {
                    'task': task,
                    'time_block': time_block,
                    'scheduling_notes': self._generate_scheduling_notes(task, stress_level)
                }
                schedule.append(scheduled_item)
        
        return schedule
    
    def _generate_scheduling_notes(self, task: Dict, stress_level: int) -> List[str]:
        """Generate scheduling notes for a task"""
        notes = []
        
        if stress_level > 7:
            notes.append("High stress detected - take regular breaks")
        
        if task['analysis']['complexity_score'] > 0.7:
            notes.append("Complex task - allocate focused time")
        
        if 'deadline' in task and task['deadline']:
            notes.append(f"Deadline: {task['deadline']}")
        
        return notes
    
    def _generate_insights(self, schedule: List[Dict], stress_level: int, mood_state: MoodState) -> Dict:
        """Generate insights about the schedule"""
        total_work_time = sum(
            item['task'].get('estimated_duration', 0) 
            for item in schedule 
        ) / 60
        
        return {
            "total_work_hours": round(total_work_time, 1),
            "stress_impact": self._assess_stress_impact(stress_level),
            "mood_compatibility": f"Schedule optimized for {mood_state.value} mood",
            "recommended_adjustments": self._generate_recommendations(stress_level, total_work_time)
        }
    
    def _assess_stress_impact(self, stress_level: int) -> str:
        """Assess how stress impacts scheduling"""
        if stress_level >= 8:
            return "High stress significantly limits task capacity"
        elif stress_level >= 5:
            return "Moderate stress affects task selection"
        else:
            return "Low stress allows for optimal productivity"
    
    def _generate_recommendations(self, stress_level: int, total_hours: float) -> List[str]:
        """Generate recommendations based on stress level"""
        recommendations = []
        
        if stress_level >= 8:
            recommendations.extend([
                "Limit work to 6 hours or less",
                "Break complex tasks into smaller steps",
                "Schedule frequent breaks every 30 minutes",
                "Consider postponing non-urgent tasks"
            ])
        elif stress_level >= 5:
            recommendations.extend([
                "Maintain reasonable 8-hour work limit",
                "Include breaks every hour",
                "Balance complex and simple tasks"
            ])
        
        if total_hours > 8:
            recommendations.append("Consider reducing total work hours")
        
        return recommendations
    
    def _get_priority_distribution(self, tasks: List[Dict]) -> Dict[str, int]:
        """Get distribution of task priorities"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        for task in tasks:
            priority = task.get('priority', 'medium')
            if priority in distribution:
                distribution[priority] += 1
        return distribution
    
    def _calculate_deadline_pressure(self, tasks: List[Dict]) -> float:
        """Calculate overall deadline pressure"""
        if not tasks:
            return 0.0
        
        total_urgency = sum(self._calculate_urgency_score(task) for task in tasks)
        return round(total_urgency / len(tasks), 2)
    
    def _get_stress_actions(self, stress_level: int) -> List[str]:
        """Get recommended actions based on stress level"""
        if stress_level >= 7:
            return ["simplify_tasks", "add_breaks", "postpone_non_urgent"]
        elif stress_level >= 4:
            return ["balance_tasks", "moderate_breaks"]
        else:
            return ["challenge_optimal", "minimal_breaks"]
    
    def _get_stress_category(self, stress_level: int) -> str:
        """Get stress category for rules"""
        if stress_level >= 7:
            return "high_stress"
        elif stress_level >= 4:
            return "medium_stress"
        else:
            return "low_stress"
    
    def _parse_mood_state(self, mood: str) -> MoodState:
        """Parse mood string into MoodState enum"""
        try:
            return MoodState[mood.upper()]
        except KeyError:
            return MoodState.FOCUSED
    
    def _adjust_duration_for_stress(self, duration: int, stress_level: int) -> int:
        """Adjust task duration based on stress level"""
        adjustment_factor = 1.0 + (stress_level * 0.05)
        return int(duration * adjustment_factor)

