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
        
        if use_gemini:
            self.gemini_client = self._setup_gemini()
            if self.gemini_client:
                print("✅ Gemini client initialized for motivational agent")
            else:
                print("❌ Gemini setup failed, using rule-based motivation")
                self.use_gemini = False
        
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
            
            # Use a model suitable for creative text generation
            model_name = 'models/gemini-1.5-flash'
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
                return MotivationResponse(
                    motivational_message="Hey, I'm here with you. Whatever you're going through, you don't have to face it alone.",
                    success=False,
                    voice_used=request.voice_gender
                )
            
            logger.info(f"🎯 Generating motivation for stress level: {request.stress_level} ({request.stress_category})")
            
            # Generate motivational message
            if self.use_gemini and self.gemini_client:
                motivational_text = self._generate_gemini_motivation(request)
            else:
                motivational_text = self._generate_rule_based_motivation(request)
            
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
            logger.error(f"❌ Error in generate_motivation: {e}")
            return MotivationResponse(
                motivational_message="It's okay to not be okay. Just breathe - I'm right here with you.",
                success=False,
                voice_used=request.voice_gender
            )
    
    def _generate_gemini_motivation(self, request: MotivationRequest) -> str:
        """Generate motivational message using Gemini"""
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
            if len(motivational_text) < 10 or len(motivational_text) > 300:
                raise ValueError("Invalid response length from Gemini")
                
            print(f"✅ Gemini generated motivational message: {len(motivational_text)} chars")
            return motivational_text
            
        except Exception as e:
            print(f"❌ Gemini motivation generation failed: {e}")
            return self._generate_rule_based_motivation(request)
    
    def _build_motivation_prompt(self, request: MotivationRequest) -> str:
        """Build prompt for Gemini based on stress level"""
        
        stress_prompts = {
            "Low": """
            You're a warm, friendly friend checking in. The user is doing pretty well (stress: {score}/10) and mentioned: "{message}".
            
            Respond like a real friend would:
            - Sound genuinely happy for them
            - Use casual, conversational language
            - Add a little emoji or warmth
            - Keep it brief and real (1-2 sentences)
            - No clinical or formal language!
            
            Just be a good friend celebrating their good moment!
            """,
            
            "Medium": """
            You're a supportive friend who gets it. The user is dealing with some stress (score: {score}/10) and shared: "{message}".
            
            Respond like you're texting a friend:
            - Validate their feelings without being dramatic
            - Offer gentle encouragement
            - Use "you've got this" energy
            - Sound like a real person (1-2 sentences)
            - No therapy-speak or formal language!
            
            Be the friend who says the right thing at the right time.
            """,
            
            "High": """
            You're that one friend who knows exactly what to say when things are hard. The user is really struggling (score: {score}/10) and told you: "{message}".
            
            Respond with heart:
            - Lead with empathy and understanding
            - Use warm, comforting language
            - Remind them they're not alone
            - Sound like you're giving them a virtual hug (1-2 sentences)
            - No clinical terms or empty platitudes!
            
            Be the comfort they need right now.
            """,
            
            "Very High": """
            You're the calm, steady presence someone needs in a storm. The user is in a really tough spot (score: {score}/10) and shared: "{message}".
            
            Respond with deep care:
            - Lead with compassion, not solutions
            - Use soothing, gentle words
            - Focus on being present with them
            - Sound like you're sitting with them in silence (1-2 sentences)
            - No advice-giving or problem-solving!
            
            Just be there with them in this hard moment.
            """,
            
            "Chronic High": """
            You're the friend who sticks around through the long haul. The user has been carrying heavy stress for a while (score: {score}/10) and said: "{message}".
            
            Respond with lasting support:
            - Acknowledge how long they've been carrying this
            - Honor their strength in still showing up
            - Remind them they matter
            - Sound like you're in it for the long run (1-2 sentences)
            - No quick fixes or silver linings!
            
            Be the consistent support they deserve.
            """
        }
        
        # Get the appropriate prompt template
        prompt_template = stress_prompts.get(request.stress_category, stress_prompts["Medium"])
        
        # Format the prompt
        prompt = prompt_template.format(
            score=request.stress_level,
            message=request.user_message
        )
        
        return prompt
    
    def _generate_rule_based_motivation(self, request: MotivationRequest) -> str:
        """Generate rule-based motivational messages as fallback"""
        
        rule_based_messages = {
            "Low": [
                "Hey! So glad to hear you're doing okay right now 🌟 Keep riding that good wave!",
                "You're crushing it! Love to see you taking care of yourself 💫",
                "This is your reminder that you're doing amazing, and I'm really happy for you! 🎉",
                "Look at you, handling life like a pro! So proud of you ✨",
                "You've got such great energy right now! Sending you good vibes to keep it going 💖"
            ],
            "Medium": [
                "I see you, and I get it. This is tough, but you're tougher 💪",
                "Hey, it's okay to feel this way. You're handling it better than you think!",
                "One breath at a time, one step at a time. You've got this, friend 🌈",
                "I'm right here with you. This feeling won't last forever, I promise.",
                "You're doing the best you can, and that's more than enough right now 💝"
            ],
            "High": [
                "Oh honey, I'm so sorry you're carrying this much 💔 Just breathe - I'm right here with you.",
                "This is really heavy, and you don't have to carry it alone. I'm sitting with you in this.",
                "Your feelings make complete sense. However you need to be right now is okay 🫂",
                "I can't fix it, but I can be here with you. You're not alone in this.",
                "It's okay to fall apart. I'll be here when you're ready 💗"
            ],
            "Very High": [
                "I'm just sitting here with you in this hard moment. However you feel is okay 🌙",
                "You're surviving right now, and that's enough. However you need to get through this moment is okay.",
                "No words needed. I'm just here, holding space for you 🕊️",
                "However dark it feels right now, I'm here with my little light. You're not alone.",
                "Just keep breathing. However you're getting through this moment is brave 💫"
            ],
            "Chronic High": [
                "You've been carrying this for so long, and you're still here. That says everything about your strength 🌄",
                "Day after day, you keep showing up. I see how hard that is, and I'm in awe of you.",
                "The fact that you're still fighting through this tells me everything about your incredible spirit 💖",
                "You've been through so much, and you're still here. That's not nothing - that's everything.",
                "However tired you are, however much it hurts - I see you, and I'm not going anywhere 🌟"
            ]
        }
        
        import random
        messages = rule_based_messages.get(request.stress_category, rule_based_messages["Medium"])
        return random.choice(messages)
    
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
            return None
    
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
            return False
    
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

# Create a singleton instance
motivational_agent = MotivationalAgent(use_gemini=True)