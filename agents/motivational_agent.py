import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from utils.llm_client import llm_client
from config import Config

logger = logging.getLogger(__name__)

class MotivationRequest(BaseModel):
    stress_level: float
    recommended_activity: str
    user_message: str
    user_preferences: Optional[Dict[str, Any]] = None

class MotivationResponse(BaseModel):
    motivational_message: str
    success: bool

class MotivationalAgent:
    def __init__(self):
        self.config = Config()
        self.motivation_prompts = {
            "high_stress": """
            You are a compassionate stress management coach. The user is experiencing high stress level ({stress_level}/10) 
            and has mentioned: "{user_message}". They've been recommended to try: {recommended_activity}.
            
            Please provide a gentle, empathetic, and supportive message that:
            
            2. Encourages them gently to try the recommended activity
            3. Offers hope and reassurance
            4. Is concise (2-3 sentences maximum)
            
            Avoid being overly cheerful or dismissive of their stress.
            """,
            
            "medium_stress": """
            You are an encouraging stress management coach. The user is experiencing moderate stress level ({stress_level}/10) 
            and has mentioned: "{user_message}". They've been recommended to try: {recommended_activity}.
            
            Please provide a balanced, motivating message that:
            1. Acknowledges their current state
            2. Positively reinforces trying the recommended activity
            3. Highlights the benefits of the activity
            4. Is encouraging but not overwhelming (2-3 sentences)
            """,
            
            "low_stress": """
            You are an uplifting stress management coach. The user is experiencing low stress level ({stress_level}/10) 
            and has mentioned: "{user_message}". They've been recommended to try: {recommended_activity}.
            
            Please provide an energetic, positive message that:
            1. Celebrates their good stress management
            2. Encourages maintaining healthy habits with the recommended activity
            3. Reinforces positive behavior
            4. Is brief and uplifting (2-3 sentences)
            """
        }
    
    def _select_prompt_template(self, stress_level: float) -> str:
        """Select the appropriate prompt template based on stress level"""
        if stress_level >= 7:
            return self.motivation_prompts["high_stress"]
        elif stress_level >= 4:
            return self.motivation_prompts["medium_stress"]
        else:
            return self.motivation_prompts["low_stress"]
    
    def generate_motivation(self, request: MotivationRequest) -> MotivationResponse:
        """
        Generate a motivational message based on stress level and recommended activity
        """
        try:
            # Validate input
            if not (0 <= request.stress_level <= 10):
                return MotivationResponse(
                    motivational_message="I'm here to support you. Let's try to manage your stress together.",
                    success=False
                )
            
            logger.info(f"Generating motivation for stress level: {request.stress_level}")
            
            # Select appropriate prompt template
            prompt_template = self._select_prompt_template(request.stress_level)
            
            # Format the prompt
            prompt = prompt_template.format(
                stress_level=request.stress_level,
                recommended_activity=request.recommended_activity,
                user_message=request.user_message
            )
            
            # Generate motivational message using LLM
            message = llm_client.generate_text(
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            # Fallback message if LLM fails
            if not message:
                message = self._get_fallback_message(request.stress_level, request.recommended_activity)
            
            return MotivationResponse(
                motivational_message=message,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in generate_motivation: {e}")
            return MotivationResponse(
                motivational_message="I'm here to support you. Remember to take things one step at a time.",
                success=False
            )
    
    def _get_fallback_message(self, stress_level: float, activity: str) -> str:
        """Provide fallback messages if LLM generation fails"""
        if stress_level >= 7:
            return f"I can see you're going through a tough time. Trying {activity} might help provide some relief. You're not alone in this."
        elif stress_level >= 4:
            return f"Managing stress is a process, and you're taking good steps. {activity} could be really helpful right now."
        else:
            return f"Great job maintaining your well-being! {activity} will help you continue feeling your best."

# Create a singleton instance
motivational_agent = MotivationalAgent()