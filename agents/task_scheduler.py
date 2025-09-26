import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import requests
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

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

class AITaskSchedulerAgent:
    """
    Enhanced Agentic AI Task Scheduler with LLM integration, NLP, and intelligent reasoning
    """
    
    def __init__(self, llm_api_key: str = None, use_ai: bool = True):
        self.llm_api_key = llm_api_key
        self.use_ai = use_ai
        self.scheduled_tasks = []
        self.user_history = []
        
        # AI Components Initialization
        self.sia = SentimentIntensityAnalyzer()
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        
        # AI Knowledge Base
        self.ai_knowledge_base = {
            "productivity_patterns": {
                "morning_peak": ["06:00", "10:00"],
                "afternoon_slump": ["14:00", "16:00"], 
                "evening_recovery": ["19:00", "22:00"]
            },
            "task_archetypes": {
                "deep_work": ["writing", "coding", "analysis", "research", "study", "develop"],
                "creative": ["design", "create", "brainstorm", "innovate", "strategize"],
                "administrative": ["email", "meeting", "plan", "organize", "schedule"],
                "routine": ["clean", "update", "maintain", "check", "review"]
            },
            "mood_task_compatibility": {
                "energetic": ["deep_work", "creative"],
                "focused": ["deep_work", "administrative"],
                "tired": ["routine", "administrative"],
                "scattered": ["routine", "creative"]
            }
        }
        
        logger.info(f"AI Task Scheduler Agent initialized - AI Enabled: {use_ai}")

    def _call_llm_api(self, prompt: str, max_tokens: int = 300) -> str:
        """Integrate with LLM API for intelligent reasoning"""
        if not self.use_ai:
            return '{"analysis": "Rule-based decision"}'
            
        try:
            API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            headers = {"Authorization": "Bearer hf_your_token_here"}
            
            payload = {
                "inputs": prompt,
                "parameters": {"max_length": max_tokens, "temperature": 0.7}
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', prompt)
                return result.get('generated_text', prompt)
            else:
                logger.warning(f"LLM API unavailable, using AI fallback: {response.status_code}")
                return self._ai_enhanced_fallback(prompt)
                
        except Exception as e:
            logger.warning(f"LLM call failed, using AI fallback: {str(e)}")
            return self._ai_enhanced_fallback(prompt)

    def _ai_enhanced_fallback(self, prompt: str) -> str:
        """AI-enhanced fallback using NLP techniques"""
        if "complexity" in prompt.lower():
            text = re.search(r'\"(.+?)\"', prompt)
            if text:
                complexity = self._ai_assess_complexity(text.group(1))
                return f'{{"complexity": {complexity}, "reasoning": "NLP-based analysis"}}'
        
        return '{"analysis": "Rule-based decision"}'

    def _ai_assess_complexity(self, text: str) -> float:
        """Use NLP to assess task complexity"""
        sentiment = self.sia.polarity_scores(text)
        words = text.split()
        word_count = len(words)
        
        complex_indicators = ['complex', 'difficult', 'challenging', 'detailed', 'analysis']
        simple_indicators = ['simple', 'easy', 'quick', 'basic']
        
        complexity_score = 0.5
        
        if sentiment['compound'] < -0.2:
            complexity_score += 0.2
        
        if word_count > 15:
            complexity_score += 0.1
        elif word_count < 5:
            complexity_score -= 0.1
            
        for indicator in complex_indicators:
            if indicator in text.lower():
                complexity_score += 0.15
                break
                
        for indicator in simple_indicators:
            if indicator in text.lower():
                complexity_score -= 0.15
                break
        
        return max(0.1, min(1.0, complexity_score))

    def _ai_classify_task_type(self, text: str) -> str:
        """AI-based task type classification"""
        text_lower = text.lower()
        type_scores = {}
        
        for task_type, keywords in self.ai_knowledge_base["task_archetypes"].items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            type_scores[task_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        return "administrative"

    def _calculate_deadline_urgency(self, task: Dict) -> float:
        """Calculate urgency based on deadline - FIXED to work properly"""
        if 'deadline' not in task or not task['deadline']:
            return 0.2  # Low urgency for tasks without deadlines
        
        try:
            deadline_str = str(task['deadline']).replace('Z', '+00:00')
            if 'T' not in deadline_str:
                # Handle date-only format
                deadline_str += 'T23:59:59'
            
            deadline = datetime.fromisoformat(deadline_str)
            now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
            
            hours_until_deadline = (deadline - now).total_seconds() / 3600
            
            # More aggressive deadline scoring
            if hours_until_deadline <= 6:     # Less than 6 hours - CRITICAL
                return 1.0
            elif hours_until_deadline <= 24:  # Today - URGENT
                return 0.95
            elif hours_until_deadline <= 48:  # Tomorrow - HIGH
                return 0.8
            elif hours_until_deadline <= 96:  # 4 days - MEDIUM
                return 0.6
            elif hours_until_deadline <= 168: # 1 week - LOW
                return 0.4
            else:                             # More than 1 week - VERY LOW
                return 0.2
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing deadline for task {task.get('title', 'unknown')}: {e}")
            return 0.2

    def _calculate_importance_score(self, task: Dict) -> float:
        """Calculate importance based on priority"""
        priority_map = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
        priority = str(task.get('priority', 'medium')).lower()
        return priority_map.get(priority, 0.6)

    def _safe_int(self, value) -> int:
        """Safely convert any value to integer"""
        try:
            if isinstance(value, str):
                return int(float(value))
            return int(value)
        except (ValueError, TypeError):
            return 5

    def _parse_mood_state(self, mood: str) -> MoodState:
        """Parse mood string to MoodState enum"""
        try:
            return MoodState[mood.upper()]
        except KeyError:
            return MoodState.FOCUSED

    def analyze_and_schedule(self, stress_data: Dict, tasks: List[Dict], 
                       mood: str, available_blocks: List[Dict]) -> Dict[str, Any]:
        """Main scheduling method - FIXED to handle all tasks properly"""
        try:
            stress_level = self._safe_int(stress_data.get('stress_level', 5))
            mood_state = self._parse_mood_state(str(mood))
            validated_tasks = self._validate_tasks(tasks)
            
            if not isinstance(available_blocks, list):
                available_blocks = []
            
            # Analyze and prioritize tasks with proper deadline handling
            analyzed_tasks = self._analyze_tasks_with_ai(validated_tasks, stress_level, mood_state)
            prioritized_tasks = self._prioritize_by_deadline_and_importance(analyzed_tasks)
            
            # Create schedule that handles ALL tasks
            schedule = self._create_comprehensive_schedule(prioritized_tasks, available_blocks, stress_level, mood_state)
            
            # Generate insights
            insights = self._generate_comprehensive_insights(schedule, stress_level, mood_state, validated_tasks)
            
            return {
                "optimized_schedule": schedule,
                "stress_analysis": {
                    "level": stress_level,
                    "impact": self._assess_stress_impact(stress_level),
                    "recommended_actions": self._get_stress_actions(stress_level)
                },
                "task_analysis": {
                    "total_tasks": len(validated_tasks),
                    "scheduled_tasks": len([item for item in schedule if item.get('task')]),
                    "tasks_with_deadlines": len([t for t in validated_tasks if t.get('deadline')]),
                    "priority_distribution": self._get_priority_distribution(validated_tasks)
                },
                "insights": insights,
                "ai_metadata": {
                    "ai_enabled": self.use_ai,
                    "analysis_method": "AI-enhanced" if self.use_ai else "Rule-based",
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Critical error in scheduling: {str(e)}")
            return self._create_error_response(e, tasks, stress_data)

    def _validate_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Ensure task data has correct types"""
        validated_tasks = []
        for i, task in enumerate(tasks):
            validated_task = task.copy()
            
            # Ensure required fields exist
            if 'title' not in validated_task:
                validated_task['title'] = f"Task {i+1}"
            
            # Fix duration to be integer
            if 'estimated_duration' in validated_task:
                try:
                    validated_task['estimated_duration'] = int(validated_task['estimated_duration'])
                except (ValueError, TypeError):
                    validated_task['estimated_duration'] = 60
            else:
                validated_task['estimated_duration'] = 60
            
            # Ensure priority exists
            if 'priority' not in validated_task:
                validated_task['priority'] = 'medium'
            
            validated_tasks.append(validated_task)
        
        return validated_tasks

    def _analyze_tasks_with_ai(self, tasks: List[Dict], stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Analyze tasks with AI enhancement"""
        analyzed_tasks = []
        
        for task in tasks:
            try:
                # AI Analysis
                task_text = f"{task.get('title', '')} {task.get('description', '')}"
                
                # Calculate individual scores
                deadline_urgency = self._calculate_deadline_urgency(task)
                importance_score = self._calculate_importance_score(task)
                complexity_score = self._ai_assess_complexity(task_text)
                task_type = self._ai_classify_task_type(task_text)
                
                # Create comprehensive analysis
                analyzed_task = {
                    **task,
                    "analysis": {
                        "deadline_urgency": deadline_urgency,
                        "importance_score": importance_score,
                        "complexity_score": complexity_score,
                        "task_type": task_type,
                        "ai_confidence": 0.8 if self.use_ai else 0.3,
                        "stress_compatibility": self._calculate_stress_compatibility(complexity_score, stress_level),
                        # Combined priority score (deadline weighted heavily)
                        "final_priority": (
                            deadline_urgency * 0.5 +      # Deadline is most important
                            importance_score * 0.3 +      # Then task importance  
                            (1 - complexity_score) * 0.2  # Lower complexity = higher priority under stress
                        )
                    }
                }
                
                analyzed_tasks.append(analyzed_task)
                
            except Exception as e:
                logger.warning(f"Error analyzing task {task.get('title', 'unknown')}: {e}")
                analyzed_tasks.append(self._create_fallback_analysis(task))
        
        return analyzed_tasks

    def _calculate_stress_compatibility(self, complexity_score: float, stress_level: int) -> float:
        """Calculate how compatible a task is with current stress level"""
        stress_factor = stress_level / 10.0
        # High stress reduces compatibility with complex tasks
        compatibility = 1.0 - (complexity_score * stress_factor * 0.7)
        return max(0.1, min(1.0, compatibility))

    def _prioritize_by_deadline_and_importance(self, tasks: List[Dict]) -> List[Dict]:
        """Prioritize tasks with proper deadline consideration"""
        try:
            # Sort by final priority score (which includes deadlines)
            tasks.sort(key=lambda x: x['analysis']['final_priority'], reverse=True)
            return tasks
        except (KeyError, TypeError) as e:
            logger.warning(f"Error in prioritization: {e}")
            return tasks

    def _create_comprehensive_schedule(self, tasks: List[Dict], available_blocks: List[Dict], 
                                    stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Create schedule that handles ALL tasks by dividing work across time slots"""
        if not tasks or not available_blocks:
            return []
        
        schedule = []
        
        # Calculate total available time
        total_available_minutes = sum(self._get_block_duration_minutes(block) for block in available_blocks)
        total_task_minutes = sum(task.get('estimated_duration', 60) for task in tasks)
        
        logger.info(f"Total available time: {total_available_minutes} minutes, Total task time: {total_task_minutes} minutes")
        
        if total_task_minutes <= total_available_minutes:
            # Enough time - normal scheduling
            schedule = self._schedule_with_adequate_time(tasks, available_blocks, stress_level, mood_state)
        else:
            # Not enough time - divide tasks across available slots
            schedule = self._schedule_with_time_division(tasks, available_blocks, stress_level, mood_state)
        
        return schedule

    def _schedule_with_adequate_time(self, tasks: List[Dict], available_blocks: List[Dict],
                                   stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Schedule when there's enough time for all tasks"""
        schedule = []
        used_blocks = set()
        
        for task in tasks:
            # Find best available block
            best_block = None
            best_score = -1
            
            for block in available_blocks:
                if id(block) not in used_blocks:
                    block_duration = self._get_block_duration_minutes(block)
                    task_duration = task.get('estimated_duration', 60)
                    
                    if block_duration >= task_duration:
                        score = self._calculate_block_task_compatibility(block, task, stress_level, mood_state)
                        if score > best_score:
                            best_score = score
                            best_block = block
            
            if best_block:
                schedule.append({
                    'task': task,
                    'time_block': best_block,
                    'allocated_duration': task.get('estimated_duration', 60),
                    'scheduling_confidence': best_score,
                    'deadline_urgency': task['analysis']['deadline_urgency'],
                    'notes': self._generate_task_notes(task, stress_level)
                })
                used_blocks.add(id(best_block))
        
        return schedule

    def _schedule_with_time_division(self, tasks: List[Dict], available_blocks: List[Dict],
                                   stress_level: int, mood_state: MoodState) -> List[Dict]:
        """Schedule by intelligently dividing ALL tasks across ALL available time slots"""
        if not tasks or not available_blocks:
            return []
            
        schedule = []
        
        # Calculate total available time across all blocks
        block_durations = [self._get_block_duration_minutes(block) for block in available_blocks]
        total_available_time = sum(block_durations)
        total_task_time = sum(task.get('estimated_duration', 60) for task in tasks)
        
        logger.info(f"Dividing {len(tasks)} tasks ({total_task_time}min) across {len(available_blocks)} blocks ({total_available_time}min)")
        
        # Create a work queue with task segments that need scheduling
        work_segments = []
        
        if total_task_time <= total_available_time:
            # We have enough time - just distribute tasks optimally
            for task in tasks:
                work_segments.append({
                    'task': task,
                    'duration': task.get('estimated_duration', 60),
                    'priority': task['analysis']['final_priority'],
                    'deadline_urgency': task['analysis']['deadline_urgency'],
                    'original_duration': task.get('estimated_duration', 60),
                    'part_number': 1,
                    'total_parts': 1
                })
        else:
            # Not enough time - we need to scale down or split tasks
            time_ratio = total_available_time / total_task_time
            logger.info(f"Time constraint ratio: {time_ratio:.2f} - scaling down task durations")
            
            for task in tasks:
                original_duration = task.get('estimated_duration', 60)
                # Scale down duration but ensure minimum 15 minutes per task
                scaled_duration = max(15, int(original_duration * time_ratio))
                
                work_segments.append({
                    'task': task,
                    'duration': scaled_duration,
                    'priority': task['analysis']['final_priority'],
                    'deadline_urgency': task['analysis']['deadline_urgency'],
                    'original_duration': original_duration,
                    'part_number': 1,
                    'total_parts': 1,
                    'scaled': True
                })
        
        # Sort work segments by priority (deadline urgency is part of final_priority)
        work_segments.sort(key=lambda x: x['priority'], reverse=True)
        
        # Now assign segments to blocks
        current_block_idx = 0
        remaining_time_in_block = block_durations[0] if block_durations else 0
        
        for segment in work_segments:
            segment_duration = segment['duration']
            assigned = False
            
            # Try to fit this segment in current or subsequent blocks
            while current_block_idx < len(available_blocks) and not assigned:
                
                if remaining_time_in_block >= segment_duration:
                    # Segment fits in current block
                    schedule.append({
                        'task': {
                            **segment['task'],
                            'title': self._generate_segment_title(segment),
                        },
                        'time_block': available_blocks[current_block_idx],
                        'allocated_duration': segment_duration,
                        'completion_status': 'complete' if not segment.get('scaled') else 'scaled',
                        'scheduling_confidence': self._calculate_block_task_compatibility(
                            available_blocks[current_block_idx], segment['task'], stress_level, mood_state
                        ),
                        'deadline_urgency': segment['deadline_urgency'],
                        'notes': self._generate_segment_notes(segment, stress_level)
                    })
                    
                    remaining_time_in_block -= segment_duration
                    assigned = True
                    
                elif remaining_time_in_block >= 15:  # Minimum chunk size
                    # Split the segment - use available time in current block
                    allocated_time = remaining_time_in_block
                    
                    schedule.append({
                        'task': {
                            **segment['task'],
                            'title': f"{segment['task']['title']} (Part 1)",
                        },
                        'time_block': available_blocks[current_block_idx],
                        'allocated_duration': allocated_time,
                        'completion_status': 'partial',
                        'scheduling_confidence': self._calculate_block_task_compatibility(
                            available_blocks[current_block_idx], segment['task'], stress_level, mood_state
                        ),
                        'deadline_urgency': segment['deadline_urgency'],
                        'notes': self._generate_segment_notes(segment, stress_level) + [f"Split task: {allocated_time}min of {segment_duration}min"]
                    })
                    
                    # Create remaining segment
                    remaining_duration = segment_duration - allocated_time
                    if remaining_duration > 0:
                        work_segments.append({
                            **segment,
                            'duration': remaining_duration,
                            'task': {
                                **segment['task'],
                                'title': f"{segment['task']['title']} (Part 2)"
                            }
                        })
                    
                    remaining_time_in_block = 0
                    assigned = True
                    
                else:
                    # Move to next block
                    current_block_idx += 1
                    if current_block_idx < len(available_blocks):
                        remaining_time_in_block = block_durations[current_block_idx]
            
            # If we couldn't assign this segment, add it as unscheduled
            if not assigned:
                schedule.append({
                    'task': segment['task'],
                    'time_block': None,
                    'allocated_duration': 0,
                    'completion_status': 'not_scheduled',
                    'scheduling_confidence': 0.0,
                    'deadline_urgency': segment['deadline_urgency'],
                    'notes': ["Insufficient time available - consider extending schedule or reducing task scope"]
                })
        
        return schedule

    def _generate_segment_title(self, segment: Dict) -> str:
        """Generate appropriate title for task segment"""
        base_title = segment['task']['title']
        
        if segment.get('scaled'):
            return f"{base_title} (Condensed: {segment['duration']}min)"
        elif segment['total_parts'] > 1:
            return f"{base_title} (Part {segment['part_number']})"
        else:
            return base_title

    def _generate_segment_notes(self, segment: Dict, stress_level: int) -> List[str]:
        """Generate notes for task segment"""
        notes = self._generate_task_notes(segment['task'], stress_level).copy()
        
        if segment.get('scaled'):
            original = segment['original_duration']
            current = segment['duration']
            notes.append(f"Task condensed from {original}min to {current}min due to time constraints")
        
        if segment['deadline_urgency'] > 0.8:
            notes.append("HIGH PRIORITY: Deadline approaching - focus on core deliverables")
            
        return notes

    def _get_block_duration_minutes(self, time_block: Dict) -> int:
        """Get duration of time block in minutes"""
        try:
            start_str = time_block.get('start_time', '')
            end_str = time_block.get('end_time', '')
            
            if start_str and end_str:
                start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                return max(0, int((end_time - start_time).total_seconds() / 60))
        except Exception as e:
            logger.warning(f"Error calculating block duration: {e}")
        return 60  # Default duration

    def _calculate_block_task_compatibility(self, block: Dict, task: Dict, 
                                          stress_level: int, mood_state: MoodState) -> float:
        """Calculate how well a task fits a time block"""
        score = 0.5
        
        # Time of day preferences
        try:
            start_time = datetime.fromisoformat(block.get('start_time', '').replace('Z', '+00:00'))
            hour = start_time.hour
            task_type = task['analysis']['task_type']
            
            # Morning (6-10) - good for focused work
            if 6 <= hour <= 10 and task_type in ['deep_work', 'administrative']:
                score += 0.2
            # Afternoon (14-16) - good for routine tasks
            elif 14 <= hour <= 16 and task_type == 'routine':
                score += 0.1
            # Evening (19-22) - good for creative tasks
            elif 19 <= hour <= 22 and task_type == 'creative':
                score += 0.1
        except:
            pass
        
        # Deadline urgency boost for earlier slots
        deadline_urgency = task['analysis']['deadline_urgency']
        if deadline_urgency > 0.8:
            score += 0.2
        elif deadline_urgency > 0.6:
            score += 0.1
        
        # Stress compatibility
        stress_compatibility = task['analysis']['stress_compatibility']
        score += (stress_compatibility - 0.5) * 0.3
        
        return max(0.0, min(1.0, score))

    def _generate_task_notes(self, task: Dict, stress_level: int) -> List[str]:
        """Generate helpful notes for scheduled tasks"""
        notes = []
        
        if task.get('deadline'):
            notes.append(f"Deadline: {task['deadline']}")
        
        if task['analysis']['deadline_urgency'] > 0.8:
            notes.append("HIGH PRIORITY: Deadline approaching soon!")
        
        if stress_level > 7 and task['analysis']['complexity_score'] > 0.6:
            notes.append("Consider breaking this complex task into smaller parts due to high stress")
        
        if task['analysis']['complexity_score'] > 0.7:
            notes.append("Complex task - ensure focused environment")
        
        return notes

    def _generate_comprehensive_insights(self, schedule: List[Dict], stress_level: int, 
                                       mood_state: MoodState, tasks: List[Dict]) -> Dict:
        """Generate comprehensive insights about the schedule"""
        scheduled_items = [item for item in schedule if item.get('allocated_duration', 0) > 0]
        total_scheduled_time = sum(item.get('allocated_duration', 0) for item in scheduled_items) / 60
        
        # Count tasks by completion status
        complete_tasks = len([item for item in schedule if item.get('completion_status') == 'complete'])
        partial_tasks = len([item for item in schedule if item.get('completion_status') == 'partial'])
        unscheduled_tasks = len([item for item in schedule if item.get('completion_status') == 'not_scheduled'])
        
        # Deadline analysis
        urgent_tasks = len([t for t in tasks if self._calculate_deadline_urgency(t) > 0.8])
        scheduled_urgent = len([item for item in scheduled_items 
                              if item.get('deadline_urgency', 0) > 0.8])
        
        return {
            "scheduling_summary": {
                "total_work_hours": round(total_scheduled_time, 1),
                "tasks_fully_scheduled": complete_tasks,
                "tasks_partially_scheduled": partial_tasks,
                "tasks_not_scheduled": unscheduled_tasks,
                "average_scheduling_confidence": round(
                    sum(item.get('scheduling_confidence', 0) for item in scheduled_items) / 
                    len(scheduled_items) if scheduled_items else 0, 2
                )
            },
            "deadline_analysis": {
                "urgent_tasks_total": urgent_tasks,
                "urgent_tasks_scheduled": scheduled_urgent,
                "deadline_coverage": f"{scheduled_urgent}/{urgent_tasks}" if urgent_tasks > 0 else "No urgent deadlines"
            },
            "stress_impact": self._assess_stress_impact(stress_level),
            "mood_optimization": f"Schedule optimized for {mood_state.value} mood",
            "recommendations": self._generate_actionable_recommendations(schedule, stress_level, tasks)
        }

    def _generate_actionable_recommendations(self, schedule: List[Dict], stress_level: int, tasks: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        unscheduled_count = len([item for item in schedule if item.get('completion_status') == 'not_scheduled'])
        if unscheduled_count > 0:
            recommendations.append(f"{unscheduled_count} tasks couldn't be scheduled - consider extending work hours or postponing non-urgent items")
        
        partial_count = len([item for item in schedule if item.get('completion_status') == 'partial'])
        if partial_count > 0:
            recommendations.append(f"{partial_count} tasks are split across time blocks - plan transition time between sessions")
        
        if stress_level >= 7:
            recommendations.append("High stress detected - take 10-15 minute breaks between tasks")
            
        urgent_unscheduled = len([item for item in schedule 
                                if item.get('completion_status') == 'not_scheduled' 
                                and item.get('deadline_urgency', 0) > 0.8])
        if urgent_unscheduled > 0:
            recommendations.append(f"ALERT: {urgent_unscheduled} urgent tasks with deadlines are not scheduled!")
        
        return recommendations

    def _create_fallback_analysis(self, task: Dict) -> Dict:
        """Create fallback analysis when AI analysis fails"""
        return {
            **task,
            "analysis": {
                "deadline_urgency": self._calculate_deadline_urgency(task),
                "importance_score": self._calculate_importance_score(task),
                "complexity_score": 0.5,
                "task_type": "administrative",
                "ai_confidence": 0.3,
                "stress_compatibility": 0.7,
                "final_priority": 0.5
            }
        }

    def _create_error_response(self, error: Exception, tasks: List[Dict], stress_data: Dict) -> Dict:
        """Create error response when scheduling fails"""
        return {
            "error": f"Scheduling failed: {str(error)}",
            "optimized_schedule": [],
            "task_analysis": {
                "total_tasks": len(tasks),
                "scheduled_tasks": 0,
                "error_occurred": True
            },
            "stress_analysis": {
                "level": self._safe_int(stress_data.get('stress_level', 5)),
                "impact": "Could not analyze due to error"
            },
            "insights": {
                "error": "Analysis unavailable due to scheduling error"
            },
            "ai_metadata": {
                "ai_enabled": self.use_ai,
                "analysis_method": "Error occurred",
                "generated_at": datetime.now().isoformat()
            }
        }

    # Helper methods
    def _assess_stress_impact(self, stress_level: int) -> str:
        if stress_level >= 8: 
            return "High stress significantly limits task capacity"
        elif stress_level >= 5: 
            return "Moderate stress affects task selection"
        else: 
            return "Low stress allows for optimal productivity"

    def _get_stress_actions(self, stress_level: int) -> List[str]:
        if stress_level >= 7: 
            return ["simplify_tasks", "add_breaks", "postpone_non_urgent"]
        elif stress_level >= 4: 
            return ["balance_tasks", "moderate_breaks"]
        else: 
            return ["challenge_optimal", "minimal_breaks"]

    def _get_priority_distribution(self, tasks: List[Dict]) -> Dict[str, int]:
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        for task in tasks:
            priority = str(task.get('priority', 'medium')).lower()
            if priority in distribution: 
                distribution[priority] += 1
        return distribution

# For backward compatibility
AdaptiveTaskScheduler = AITaskSchedulerAgent