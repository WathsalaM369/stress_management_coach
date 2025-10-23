import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pygame
from gtts import gTTS
import tempfile
import uuid

logger = logging.getLogger(__name__)

class MotivationRequest(BaseModel):
    stress_level: float
    stress_category: str
    user_message: str
    user_preferences: Optional[Dict[str, Any]] = None
    generate_audio: bool = True
    voice_gender: str = "female"  # "male" or "female"

class MotivationResponse(BaseModel):
    motivational_message: str
    audio_file_path: Optional[str] = None
    success: bool
    voice_used: str = "female"

class MotivationalAgent:
    def __init__(self, use_gemini=True):
        self.use_gemini = use_gemini
        self.gemini_client = None
        self.audio_files = {}  # Cache for audio files
        
        print(f"🔧 Initializing MotivationalAgent - use_gemini: {use_gemini}")
        
        if not use_gemini:
            raise Exception("❌ AI motivation requires use_gemini=True. Rule-based messages are no longer supported.")
        
        self.gemini_client = self._setup_gemini()
        if not self.gemini_client:
            raise Exception("❌ Gemini setup failed - AI motivation requires valid API key and connection")
        
        print("✅ Gemini client initialized for motivational agent")
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            print("✅ Audio system initialized")
        except Exception as e:
            print(f"❌ Audio system initialization failed: {e}")
    
    def _setup_gemini(self):
        """Setup Gemini client for motivational messages"""
        try:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                print("❌ GOOGLE_API_KEY not found for motivational agent")
                return None
            
            genai.configure(api_key=api_key)
            
            # Use the model from .env file, fallback to gemini-2.0-flash-001
            model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.0-flash-001')
            print(f"📱 Using Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Test the connection
            test_response = model.generate_content("Say only 'MOTIVATION_READY'")
            if "MOTIVATION_READY" in test_response.text:
                print("✅ Gemini motivational agent ready")
                return model
            else:
                print("❌ Gemini test failed")
                return None
                
        except Exception as e:
            print(f"❌ Error in Gemini setup for motivational agent: {str(e)}")
            return None
    
    def generate_motivation(self, request: MotivationRequest) -> MotivationResponse:
        """
        Generate motivational message based on stress level and convert to audio
        """
        try:
            # Validate input
            if not (0 <= request.stress_level <= 10):
                raise ValueError("Stress level must be between 0 and 10")
            
            logger.info(f"🎯 Generating motivation for stress level: {request.stress_level} ({request.stress_category})")
            
            # Generate motivational message using Gemini AI
            motivational_text = self._generate_gemini_motivation(request)
            
            # Generate audio if requested
            audio_path = None
            if request.generate_audio and motivational_text:
                audio_path = self._text_to_speech(motivational_text, request.stress_category, request.voice_gender)
            
            return MotivationResponse(
                motivational_message=motivational_text,
                audio_file_path=audio_path,
                success=True,
                voice_used=request.voice_gender
            )
            
        except Exception as e:
            logger.critical(f"❌ CRITICAL ERROR in generate_motivation: {e}")
            raise
    
    def _generate_gemini_motivation(self, request: MotivationRequest) -> str:
        """Generate motivational message using Gemini - AI-only, no fallbacks"""
        try:
            prompt = self._build_motivation_prompt(request)
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.9,  # More creative and conversational
                    'top_p': 0.95,
                    'max_output_tokens': 120,
                }
            )
            
            motivational_text = response.text.strip()
            
            # Clean and validate the response
            if len(motivational_text) < 10 or len(motivational_text) > 400:
                raise ValueError(f"Invalid response length from Gemini: {len(motivational_text)} characters")
                
            print(f"✅ Gemini generated motivational message: {len(motivational_text)} chars")
            return motivational_text
            
        except Exception as e:
            logger.critical(f"❌ Gemini motivation generation failed: {e}")
            raise
    
    def _build_motivation_prompt(self, request: MotivationRequest) -> str:
        """Build prompt for Gemini based on stress level - generates direct motivational messages"""
        
        stress_prompts = {
            "Low": """
            You're a warm, encouraging motivational coach. The user is doing well with low stress (score: {score}/10).
            
            Generate a brief, uplifting motivational message (2-3 sentences):
            - Celebrate their positive state
            - Encourage them to maintain this momentum
            - Use warm, friendly language with light emoji
            - Focus on gratitude and positive energy
            - Sound genuine and conversational
            
            Example tone: "You're in a great place right now! 🌟 Keep embracing this positive energy and remember to appreciate these calm moments. You've earned this peace!"
            
            Generate a similar encouraging message now.
            """,
            
            "Medium": """
            You're a supportive motivational coach. The user is experiencing moderate stress (score: {score}/10).
            
            Generate a supportive motivational message (2-3 sentences):
            - Acknowledge they're managing things well despite the pressure
            - Remind them of their inner strength
            - Offer gentle encouragement to keep going
            - Use "you've got this" energy
            - Include a practical mindset tip
            
            Example tone: "You're handling more than you realize, and you're doing great! 💪 Take a deep breath - you have the strength to navigate this. Remember, progress over perfection always wins."
            
            Generate a similar motivational message now.
            """,
            
            "High": """
            You're a compassionate motivational coach. The user is experiencing high stress (score: {score}/10).
            
            Generate a comforting yet empowering message (2-3 sentences):
            - Start with empathy and validation
            - Remind them they're stronger than they feel right now
            - Offer hope without minimizing their struggle
            - Use warm, soothing language
            - Include a gentle reminder to be kind to themselves
            
            Example tone: "I know things feel overwhelming right now, and that's completely valid. 💙 You're stronger than you realize, even when you don't feel it. Take this one moment at a time - you don't have to carry it all at once."
            
            Generate a similar compassionate message now.
            """,
            
            "Very High": """
            You're a deeply caring motivational coach. The user is experiencing very high stress (score: {score}/10).
            
            Generate a gentle, grounding message (2-3 sentences):
            - Lead with deep compassion and presence
            - Focus on immediate comfort, not solutions
            - Remind them they're not alone in this
            - Use soft, calming language
            - Encourage one small breath or moment of rest
            
            Example tone: "Right now, just focus on breathing. 🕊️ You're carrying so much, and it's okay to feel overwhelmed. You're not alone in this - take it one tiny moment at a time, and that's enough."
            
            Generate a similar soothing message now.
            """,
            
            "Chronic High": """
            You're a steadfast, understanding motivational coach. The user has been experiencing prolonged high stress (score: {score}/10).
            
            Generate a message of lasting support (2-3 sentences):
            - Honor the weight they've been carrying
            - Recognize their resilience in continuing to show up
            - Offer sustained hope and validation
            - Use language that shows long-term care
            - Remind them that their feelings are valid and they matter
            
            Example tone: "You've been carrying this weight for so long, and the fact that you're still here matters deeply. 🌿 Your strength isn't measured by how you feel - it's shown in how you keep going. You deserve support, rest, and to know that you're enough, exactly as you are."
            
            Generate a similar message of enduring support now.
            """
        }
        
        # Get appropriate prompt based on stress category
        category = request.stress_category
        if category not in stress_prompts:
            # Default to Medium if category not found
            category = "Medium"
        
        prompt_template = stress_prompts[category]
        
        # Format the prompt with actual values
        formatted_prompt = prompt_template.format(
            score=request.stress_level,
            message=request.user_message if request.user_message else "checking in on their stress"
        )
        
        return formatted_prompt
    
    def _text_to_speech(self, text: str, stress_category: str, voice_gender: str = "female") -> str:
        """Convert text to speech and return audio file path"""
        try:
            # Create a temporary audio file
            temp_dir = tempfile.gettempdir()
            audio_filename = f"motivation_{stress_category.lower()}_{voice_gender}_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = os.path.join(temp_dir, audio_filename)
            
            # Generate speech with appropriate pacing based on stress level
            slow = stress_category in ["High", "Very High", "Chronic High"]
            
            # For gTTS, we can't directly control gender, but we can adjust parameters
            # Male voices tend to be slightly deeper, female voices slightly higher
            tts = gTTS(
                text=text,
                lang='en',
                slow=slow,  # Slower speech for high stress messages
                lang_check=False
            )
            
            tts.save(audio_path)
            print(f"✅ Audio generated with {voice_gender} voice: {audio_path}")
            
            # Cache the audio file path
            self.audio_files[audio_path] = {
                'text': text,
                'voice_gender': voice_gender,
                'stress_category': stress_category
            }
            
            return audio_path
            
        except Exception as e:
            print(f"❌ Text-to-speech conversion failed: {e}")
            raise
    
    def play_audio(self, audio_path: str):
        """Play the generated audio file"""
        try:
            if audio_path and os.path.exists(audio_path):
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                    
                print("✅ Audio playback completed")
                return True
            else:
                print("❌ Audio file not found")
                return False
                
        except Exception as e:
            print(f"❌ Audio playback failed: {e}")
            raise
    
    def get_available_voices(self):
        """Get available voice options"""
        return {
            "female": "Warm, comforting female voice",
            "male": "Calm, reassuring male voice"
        }
    
    def set_voice_preference(self, voice_gender: str):
        """Set default voice preference"""
        if voice_gender.lower() in ["male", "female"]:
            self.default_voice = voice_gender.lower()
            print(f"✅ Default voice set to: {voice_gender}")
            return True
        else:
            print("❌ Invalid voice preference. Use 'male' or 'female'")
            return False
    
    def cleanup_audio_files(self):
        """Clean up generated audio files"""
        for audio_path in list(self.audio_files.keys()):
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    voice_info = self.audio_files[audio_path]
                    print(f"🧹 Cleaned up {voice_info['voice_gender']} voice audio: {audio_path}")
            except Exception as e:
                print(f"❌ Failed to clean up audio file {audio_path}: {e}")
        
        self.audio_files.clear()

# Create a singleton instance with error handling
try:
    motivational_agent = MotivationalAgent(use_gemini=True)
except Exception as e:
    print(f"FATAL ERROR: {e}")
    print("Please ensure GOOGLE_API_KEY is set in your .env file")
    motivational_agent = None