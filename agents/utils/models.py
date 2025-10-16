# agents/utils/models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RecommendationRequest:
    def __init__(self, stress_level: str, user_id: int, context: Optional[Dict[str, Any]] = None):
        self.stress_level = stress_level
        self.user_id = user_id
        self.context = context or {}

class ActivityRecommendation:
    def __init__(self, id: int, name: str, description: str, duration_minutes: int):
        self.id = id
        self.name = name
        self.description = description
        self.duration_minutes = duration_minutes

class UserCreate:
    def __init__(self, username: str):
        self.username = username

class UserPreferencesUpdate:
    def __init__(self, likes: Optional[List[str]] = None, dislikes: Optional[List[str]] = None, 
                 default_available_minutes: Optional[int] = None):
        self.likes = likes or []
        self.dislikes = dislikes or []
        self.default_available_minutes = default_available_minutes