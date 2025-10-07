#Vinushas
import openai
import logging
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.config = Config()
        openai.api_key = self.config.OPENAI_API_KEY
        
    def generate_text(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using the configured LLM
        """
        try:
            if self.config.LLM_PROVIDER == "openai":
                response = openai.chat.completions.create(
                    model=self.config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a compassionate stress management coach."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            else:
                # Add support for other LLM providers here
                logger.error(f"Unsupported LLM provider: {self.config.LLM_PROVIDER}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating text with LLM: {e}")
            return None

# Create a singleton instance
llm_client = LLMClient()