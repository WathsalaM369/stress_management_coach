import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np

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
        
        # Stress-based scheduling rules
        self.stress_rules = {
            "high_stress": {
                "threshold": 7,
                "actions": ["simplify_tasks", "add_breaks", "postpone_non_urgent"],
                "max_work_hours": 6
            },
            "medium_stress": {
                "threshold": 4,
                "actions": ["balance_tasks", "moderate_breaks"],
                "max_work_hours": 8
            },
            "low_stress": {
                "threshold": 0,
                "actions": ["challenge_optimal", "minimal_breaks"],
                "max_work_hours": 10
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
            
            # Analyze tasks and their properties
            analyzed_tasks = self._analyze_tasks(tasks, stress_level, mood_state)
            
            # Apply stress-based scheduling rules
            prioritized_tasks = self._apply_stress_rules(analyzed_tasks, stress_level, stress_reasons)
            
            # Schedule tasks considering time compatibility
            schedule = self._create_optimized_schedule(prioritized_tasks, available_blocks, stress_level, mood_state)
            
            # Generate insights and recommendations
            insights = self._generate_insights(schedule, stress_level, mood_state)
            
            return {
                "optimized_schedule": schedule,
                "stress_analysis": {
                    "level": stress_level,
                    "impact_on_schedule": self._assess_stress_impact(stress_level),
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
        """Analyze each task for stress compatibility and scheduling factors"""
        analyzed_tasks = []
        
        for task in tasks:
            # Calculate multiple scoring factors
            urgency_score = self._calculate_urgency_score(task)
            importance_score = self._calculate_importance_score(task)
            stress_compatibility = self._calculate_stress_compatibility(task, stress_level, mood_state)
            complexity_score = self._assess_complexity(task)
            
            # Calculate overall priority score (weighted average)
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
        """Calculate how urgent a task is based on deadline"""
        if 'deadline' not in task:
            return 0.5  # Medium urgency if no deadline
        
        try:
            deadline_str = task['deadline'].replace('Z', '+00:00')
            deadline = datetime.fromisoformat(deadline_str)
            now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
            
            time_until_deadline = (deadline - now).total_seconds()
            
            # Convert to hours and calculate urgency
            hours_until_deadline = time_until_deadline / 3600
            
            if hours_until_deadline <= 24:  # 1 day
                return 1.0
            elif hours_until_deadline <= 72:  # 3 days
                return 0.8
            elif hours_until_deadline <= 168:  # 1 week
                return 0.6
            else:
                return 0.4
                
        except (ValueError, TypeError):
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
        category = task.get('category', 'personal')
        category_score = category_weights.get(category, 0.5)
        
        return (priority_score * 0.6 + category_score * 0.4)
    
    def _calculate_stress_compatibility(self, task: Dict, stress_level: int, mood_state: MoodState) -> float:
        """Calculate how compatible a task is with current stress level"""
        # Base compatibility decreases as stress increases
        base_compatibility = 1.0 - (stress_level / 20)  # 0.5 at stress level 10
        
        # Adjust based on task complexity
        complexity = self._assess_complexity(task)
        if stress_level > 6 and complexity > 0.7:
            base_compatibility *= 0.6  # Reduce compatibility for complex tasks under high stress
        
        # Adjust based on mood
        mood_adjustment = self._get_mood_adjustment(mood_state, task)
        base_compatibility *= mood_adjustment
        
        # Adjust based on task duration (longer tasks less compatible with high stress)
        duration = task.get('estimated_duration', 60)
        if stress_level > 5 and duration > 120:  # More than 2 hours
            base_compatibility *= 0.8
        
        return max(0.1, min(1.0, base_compatibility))
    
    def _assess_complexity(self, task: Dict) -> float:
        """Assess task complexity based on various factors"""
        duration = task.get('estimated_duration', 60)
        description = task.get('description', '').lower()
        title = task.get('title', '').lower()
        
        complexity = 0.5  # Base complexity
        
        # Adjust based on duration
        if duration > 180:  # 3+ hours
            complexity += 0.3
        elif duration > 120:  # 2+ hours
            complexity += 0.2
        elif duration > 60:  # 1+ hours
            complexity += 0.1
        
        # Adjust based on keywords in description/title
        complex_keywords = ['complex', 'difficult', 'challenging', 'detailed', 'analysis', 'technical', 'report']
        simple_keywords = ['simple', 'easy', 'quick', 'routine', 'basic', 'shopping', 'sync']
        
        text = f"{title} {description}"
        if any(keyword in text for keyword in complex_keywords):
            complexity += 0.2
        if any(keyword in text for keyword in simple_keywords):
            complexity -= 0.2
        
        return max(0.1, min(1.0, complexity))
    
    def _get_mood_adjustment(self, mood_state: MoodState, task: Dict) -> float:
        """Get adjustment factor based on mood and task type"""
        adjustments = {
            MoodState.ENERGETIC: {
                'complex': 1.2,  # Good for complex tasks
                'physical': 1.1,  # Good for physical tasks
                'creative': 1.3   # Great for creative tasks
            },
            MoodState.TIRED: {
                'complex': 0.6,   # Bad for complex tasks
                'physical': 0.7,  # Bad for physical tasks
                'simple': 1.1     # Good for simple tasks
            },
            MoodState.FOCUSED: {
                'complex': 1.4,   # Excellent for complex tasks
                'detailed': 1.3,  # Great for detailed work
                'creative': 0.9   # Okay for creative tasks
            },
            MoodState.SCATTERED: {
                'complex': 0.5,   # Bad for complex tasks
                'simple': 1.2,    # Good for simple tasks
                'varied': 1.1     # Good for varied tasks
            }
        }
        
        # Determine task type
        task_type = self._classify_task_type(task)
        adjustment = adjustments[mood_state].get(task_type, 1.0)
        
        return adjustment
    
    def _classify_task_type(self, task: Dict) -> str:
        """Classify task into a type based on its properties"""
        description = task.get('description', '').lower()
        title = task.get('title', '').lower()
        category = task.get('category', '').lower()
        
        text = f"{title} {description} {category}"
        
        if any(word in text for word in ['analy', 'complex', 'detail', 'calculat', 'report', 'technical']):
            return 'complex'
        elif any(word in text for word in ['creative', 'design', 'write', 'compose', 'presentation']):
            return 'creative'
        elif any(word in text for word in ['physical', 'exercise', 'walk', 'move', 'shopping']):
            return 'physical'
        elif any(word in text for word in ['simple', 'routine', 'basic', 'quick', 'sync', 'meeting']):
            return 'simple'
        elif any(word in text for word in ['varied', 'multiple', 'different']):
            return 'varied'
        else:
            return 'general'
    
    def _apply_stress_rules(self, tasks: List[Dict], stress_level: int, stress_reasons: List[str]) -> List[Dict]:
        """Apply stress-based rules to prioritize and modify tasks"""
        # Sort by overall priority
        tasks.sort(key=lambda x: x['analysis']['overall_priority'], reverse=True)
        
        # Apply stress-specific modifications
        if stress_level >= self.stress_rules["high_stress"]["threshold"]:
            tasks = self._apply_high_stress_rules(tasks, stress_reasons)
        elif stress_level >= self.stress_rules["medium_stress"]["threshold"]:
            tasks = self._apply_medium_stress_rules(tasks)
        else:
            tasks = self._apply_low_stress_rules(tasks)
        
        return tasks
    
    def _apply_high_stress_rules(self, tasks: List[Dict], stress_reasons: List[str]) -> List[Dict]:
        """Apply rules for high stress situations"""
        modified_tasks = []
        
        for task in tasks:
            # For high stress, simplify complex tasks
            if task['analysis']['complexity_score'] > 0.7:
                modified_task = self._simplify_task_for_stress(task, stress_reasons)
                modified_tasks.append(modified_task)
            else:
                modified_tasks.append(task)
        
        return modified_tasks
    
    def _simplify_task_for_stress(self, task: Dict, stress_reasons: List[str]) -> Dict:
        """Simplify a complex task for high stress situations"""
        simplified_task = task.copy()
        
        # Add simplification suggestions
        simplification_notes = [
            "Consider breaking this complex task into smaller steps",
            "Focus on the most critical parts first",
            "Take frequent breaks during this task"
        ]
        
        if 'analysis' not in simplified_task:
            simplified_task['analysis'] = {}
        
        simplified_task['analysis']['simplification_notes'] = simplification_notes
        simplified_task['analysis']['recommended_duration'] *= 1.2  # Add buffer time
        
        return simplified_task
    
    def _apply_medium_stress_rules(self, tasks: List[Dict]) -> List[Dict]:
        """Apply rules for medium stress situations"""
        # For medium stress, just return tasks as-is but sorted by priority
        return tasks
    
    def _apply_low_stress_rules(self, tasks: List[Dict]) -> List[Dict]:
        """Apply rules for low stress situations"""
        # For low stress, we can be more ambitious
        for task in tasks:
            if task['analysis']['complexity_score'] > 0.6:
                # Add challenge note for low stress
                if 'analysis' not in task:
                    task['analysis'] = {}
                task['analysis']['challenge_note'] = "Good opportunity to tackle this challenging task"
        
        return tasks
    
    def _create_optimized_schedule(self, tasks: List[Dict], time_blocks: List[Dict], 
                                 stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Create an optimized schedule considering all factors"""
        schedule = []
        
        # Simple scheduling: just assign tasks to available blocks in priority order
        available_blocks = [block for block in time_blocks if block.get('is_available', True)]
        
        for task in tasks:
            if available_blocks:
                # Use the first available block
                time_block = available_blocks.pop(0)
                scheduled_item = {
                    'task': task,
                    'time_block': time_block,
                    'scheduling_notes': self._generate_scheduling_notes(task, time_block, stress_level, mood_state)
                }
                schedule.append(scheduled_item)
        
        return schedule
    
    def _generate_scheduling_notes(self, task: Dict, time_block: Dict, 
                                 stress_level: int, mood_state: MoodState) -> List[str]:
        """Generate scheduling notes for a task"""
        notes = []
        
        if stress_level > 7:
            notes.append("High stress level - consider simplifying this task")
        
        if task['analysis']['complexity_score'] > 0.7:
            notes.append("Complex task - allocate focused time")
        
        if 'deadline' in task:
            notes.append(f"Deadline: {task['deadline']}")
        
        return notes
    
    def _generate_insights(self, schedule: List[Dict], stress_level: int, mood_state: MoodState) -> Dict:
        """Generate insights about the schedule"""
        total_work_time = sum(
            item['task'].get('estimated_duration', 0) 
            for item in schedule 
        ) / 60  # Convert to hours
        
        return {
            "total_work_hours": total_work_time,
            "stress_impact": self._assess_stress_impact(stress_level),
            "mood_compatibility": self._assess_mood_compatibility(mood_state, schedule),
            "recommended_adjustments": self._generate_recommendations(stress_level, total_work_time)
        }
    
    def _assess_stress_impact(self, stress_level: int) -> str:
        """Assess how stress impacts scheduling"""
        if stress_level >= 8:
            return "High stress significantly limits task capacity and requires simplification"
        elif stress_level >= 5:
            return "Moderate stress affects task selection and requires careful scheduling"
        else:
            return "Low stress allows for optimal task scheduling and productivity"
    
    def _assess_mood_compatibility(self, mood_state: MoodState, schedule: List[Dict]) -> str:
        """Assess mood compatibility with scheduled tasks"""
        return f"Tasks are generally compatible with {mood_state.value} mood"
    
    def _generate_recommendations(self, stress_level: int, total_hours: float) -> List[str]:
        """Generate recommendations based on stress level"""
        recommendations = []
        
        if stress_level >= 8:
            recommendations.extend([
                "Limit work to 6 hours or less",
                "Break complex tasks into smaller steps",
                "Schedule frequent short breaks",
                "Consider postponing non-urgent tasks"
            ])
        elif stress_level >= 5:
            recommendations.extend([
                "Maintain reasonable 8-hour work limit",
                "Balance complex and simple tasks",
                "Include moderate breaks",
                "Monitor energy levels throughout day"
            ])
        
        if total_hours > 8:
            recommendations.append("Consider reducing total work hours to prevent burnout")
        
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
        return total_urgency / len(tasks)
    
    def _get_stress_actions(self, stress_level: int) -> List[str]:
        """Get recommended actions based on stress level"""
        if stress_level >= 7:
            return self.stress_rules["high_stress"]["actions"]
        elif stress_level >= 4:
            return self.stress_rules["medium_stress"]["actions"]
        else:
            return self.stress_rules["low_stress"]["actions"]

    # Helper methods
    def _parse_mood_state(self, mood: str) -> MoodState:
        """Parse mood string into MoodState enum"""
        try:
            return MoodState[mood.upper()]
        except KeyError:
            return MoodState.FOCUSED  # Default to focused
    
    def _adjust_duration_for_stress(self, duration: int, stress_level: int) -> int:
        """Adjust task duration based on stress level"""
        adjustment_factor = 1.0 + (stress_level * 0.1)  # 10% longer per stress level
        return int(duration * adjustment_factor)