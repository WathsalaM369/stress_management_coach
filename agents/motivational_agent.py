import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import tempfile
import uuid
import time
import traceback
import subprocess
import sys
import platform
import json
import re
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MotivationRequest(BaseModel):
    stress_level: float
    stress_category: str
    user_message: str
    user_preferences: Optional[Dict[str, Any]] = None
    generate_audio: bool = True
    voice_gender: str = "female"

class MotivationResponse(BaseModel):
    motivational_message: str
    audio_file_path: Optional[str] = None
    success: bool
    voice_used: str = "female"
    audio_duration: Optional[float] = None
    llm_used: bool = False

class MotivationalAgent:
    def __init__(self, use_gemini=True):
        self.use_gemini = use_gemini
        self.gemini_client = None
        self.gemini_available = False
        self.audio_files = {}
        self.current_audio_path = None
        
        print(f"🎵 Initializing Motivational Agent - use_gemini: {use_gemini}")
        
        # Test audio system first
        self._test_system_dependencies()
        
        # Gemini configuration (EXACTLY same pattern as StressEstimator)
        if use_gemini:
            self.gemini_client = self._setup_gemini()
            if self.gemini_client:
                print("✅ Gemini client initialized successfully")
                self.gemini_available = True
            else:
                print("❌ Gemini setup failed, using fallback messages")
                self.gemini_available = False
        
        print("✅ Motivational Agent Ready!")
        print(f"🤖 Gemini Status: {'Available' if self.gemini_available else 'Using Fallback Messages'}")
    
    def _setup_gemini(self):
        """Setup Gemini client with EXACT same logic as StressEstimator"""
        try:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment variables")
                return None
            
            print(f"🔑 API Key found: {api_key[:12]}...")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Get available models
            print("🤖 Discovering available models...")
            available_models = genai.list_models()
            
            # Filter for Gemini text models
            gemini_models = []
            for model in available_models:
                if 'gemini' in model.name.lower() and 'generateContent' in model.supported_generation_methods:
                    gemini_models.append(model.name)
                    print(f"   ✅ {model.name}")
            
            if not gemini_models:
                print("❌ No compatible Gemini models found")
                return None
            
            # Try models in order of preference (EXACTLY same as StressEstimator)
            preferred_models = [
                'models/gemini-2.0-flash-001',  # Fast and capable
                'models/gemini-2.0-flash',      # Alternative flash
                'models/gemini-2.5-flash',      # Latest flash
                'models/gemini-2.5-pro',        # Pro version
                'models/gemini-2.0-flash-lite-001',  # Lite version
            ]
            
            # Filter to only available models
            available_preferred = [model for model in preferred_models if model in gemini_models]
            
            if not available_preferred:
                # Use first available Gemini model
                model_name = gemini_models[0]
            else:
                model_name = available_preferred[0]
            
            print(f"🤖 Using model: {model_name}")
            
            model = genai.GenerativeModel(model_name)
            
            # Test the connection
            print("🧪 Testing API connection...")
            test_response = model.generate_content("Say only the word 'SUCCESS'")
            
            test_result = test_response.text.strip()
            print(f"✅ API test successful! Response: '{test_result}'")
            
            return model
            
        except Exception as e:
            print(f"❌ Error in Gemini setup: {str(e)}")
            return None
    
    def _test_system_dependencies(self):
        """Test and install missing dependencies"""
        print("🔧 Checking system dependencies...")
        
        missing_packages = []
        
        # Test required packages
        try:
            import google.generativeai
        except ImportError:
            missing_packages.append("google-generativeai")
        
        try:
            from gtts import gTTS
        except ImportError:
            missing_packages.append("gtts")
        
        try:
            import pygame
        except ImportError:
            missing_packages.append("pygame")
        
        if missing_packages:
            print(f"❌ Missing packages: {missing_packages}")
            print("💡 Run: pip install " + " ".join(missing_packages))
            return False
        
        # Initialize pygame mixer
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            print("✅ Audio system initialized")
        except Exception as e:
            print(f"❌ Audio system failed: {e}")
            print("💡 Try: pip install pygame --upgrade")
        
        return True
    
    def generate_motivation(self, request: MotivationRequest) -> MotivationResponse:
        """
        Generate motivational message with Gemini fallback pattern
        """
        print(f"🎯 Generating motivation (Stress: {request.stress_level}, Category: {request.stress_category})")
        print(f"🤖 Gemini Available: {self.gemini_available}")
        
        try:
            # Use Gemini if available, otherwise fallback
            if self.gemini_available and self.gemini_client:
                print("🤖 Using Gemini for motivational message...")
                motivational_text = self._gemini_motivation(request)
                llm_used = True
            else:
                print("🔄 Using fallback motivational messages...")
                motivational_text = self._fallback_motivation(request)
                llm_used = False
            
            # Generate audio if requested
            audio_path = None
            if request.generate_audio and motivational_text:
                audio_path = self._generate_audio_simple(motivational_text, request.voice_gender)
            
            return MotivationResponse(
                motivational_message=motivational_text,
                audio_file_path=audio_path,
                success=True,
                voice_used=request.voice_gender,
                audio_duration=len(motivational_text.split()) * 0.5,
                llm_used=llm_used
            )
            
        except Exception as e:
            print(f"❌ Error in generate_motivation: {e}")
            # Always return a fallback message on error
            fallback_text = self._get_fallback_message(request.stress_category)
            return MotivationResponse(
                motivational_message=fallback_text,
                success=False,
                voice_used=request.voice_gender,
                llm_used=False
            )
    
    def _gemini_motivation(self, request: MotivationRequest) -> str:
        """Generate motivational message using Gemini with proper error handling"""
        try:
            prompt = self._build_motivation_prompt(request)
            
            system_instruction = """You are a compassionate, empathetic motivational coach. Create brief, supportive messages for people experiencing stress.

CRITICAL REQUIREMENTS:
- Keep it 1-2 sentences maximum
- Sound warm and caring, like a supportive friend
- Include one relevant emoji at the end
- Be specific to the stress level and user's message
- Focus on validation and support, not advice
- Make it feel personal and genuine

Return ONLY the motivational message text, nothing else."""

            full_prompt = f"{system_instruction}\n\nUser Context:\n{prompt}"
            
            print("📤 Sending motivation request to Gemini...")
            response = self.gemini_client.generate_content(
                full_prompt,
                request_options={'timeout': 15}
            )
            
            motivational_text = response.text.strip()
            print("📨 Gemini motivation response received")
            
            # Validate response
            if self._validate_motivation_response(motivational_text):
                print("✅ Gemini motivation validated")
                return motivational_text
            else:
                print("❌ Gemini response invalid, using fallback")
                return self._fallback_motivation(request)
                
        except Exception as e:
            print(f"❌ Gemini motivation failed: {e}")
            # Check for quota issues and disable if needed
            if "quota" in str(e).lower() or "429" in str(e):
                print("❌ Gemini quota exceeded - switching to fallback")
                self.gemini_available = False
            return self._fallback_motivation(request)
    
    def _build_motivation_prompt(self, request: MotivationRequest) -> str:
        """Build detailed motivation prompt"""
        prompt_parts = [
            "USER STRESS CONTEXT:",
            f"Stress Level: {request.stress_level}/10",
            f"Stress Category: {request.stress_category}",
            f"User Message: '{request.user_message}'",
            "",
            "PERSONALIZATION CONTEXT:",
            f"Voice Preference: {request.voice_gender}",
            f"User Preferences: {request.user_preferences or 'Not specified'}",
            "",
            "MESSAGE REQUIREMENTS:",
            "- 1-2 sentences maximum",
            "- Warm, empathetic tone",
            "- Include one relevant emoji",
            "- Validate their feelings",
            "- Offer genuine support",
            "- Sound like a caring friend"
        ]
        
        # Add stress-level specific guidance
        stress_guidance = {
            "Low": "Focus on encouragement and celebrating their awareness",
            "Medium": "Acknowledge the challenge while reinforcing their strength",
            "High": "Offer comfort and presence, validate the difficulty",
            "Very High": "Provide calming reassurance and emotional support", 
            "Chronic High": "Acknowledge their endurance and ongoing strength"
        }
        
        guidance = stress_guidance.get(request.stress_category, "Provide warm, empathetic support")
        prompt_parts.append(f"SPECIFIC GUIDANCE: {guidance}")
        
        return "\n".join(prompt_parts)
    
    def _validate_motivation_response(self, text: str) -> bool:
        """Validate that the Gemini response meets requirements"""
        if not text or len(text.strip()) < 10:
            return False
        
        # Check for reasonable length (1-2 sentences)
        sentences = text.split('.')
        if len(sentences) > 3:  # Too long
            return False
        
        return True
    
    def _fallback_motivation(self, request: MotivationRequest) -> str:
        """Fallback motivational messages (same as your reliable version)"""
        return self._get_fallback_message(request.stress_category)
    
    def _get_fallback_message(self, stress_category: str) -> str:
        """Get a fallback motivational message based on stress category"""
        fallback_messages = {
            "Low": [
                "You're doing amazing! Keep shining ✨",
                "So proud of you for taking care of yourself! 🌟",
                "You've got this! Your energy is inspiring 💫",
                "Every small step counts - you're making good progress! 🎯",
                "Your positive energy is contagious! Keep going! 🌈"
            ],
            "Medium": [
                "I see you working through this. You're stronger than you think 💪",
                "One step at a time, one breath at a time. You've got this 🌸",
                "This is tough, but you're tougher. I believe in you! ⭐",
                "Progress isn't always linear - you're doing better than you think! 🌱",
                "You're navigating challenges with such grace and strength! 🦋"
            ],
            "High": [
                "I'm right here with you. However you feel is completely okay 🫂",
                "Just breathe. However you need to get through this moment is enough 💗",
                "You don't have to carry this alone. I'm sitting with you in this 🤝",
                "It's okay to not be okay. I'm here with you through this 💙",
                "This moment is tough, but you're tougher. I believe in your strength! 💫"
            ],
            "Very High": [
                "However heavy this feels, you're not alone. I'm here with you 🌙",
                "Just keep breathing. However you're surviving right now is brave 💫",
                "No words needed. I'm just here, holding space for you 🕊️",
                "You're weathering the storm with incredible courage ⛈️",
                "However dark it seems, I'm here holding the light for you 🕯️"
            ],
            "Chronic High": [
                "You've been carrying this for so long, and you're still here. That's incredible strength 🌟",
                "Day after day, you keep showing up. I see your courage and I'm in awe 💎",
                "However tired you are, however much it hurts - I see you, and I'm not going anywhere 🤗",
                "Your resilience through ongoing challenges is truly remarkable 🌺",
                "Through all the difficult days, you continue to show such strength 🦁"
            ],
            "default": [
                "I'm here for you. Take a deep breath. You've got this.💫",
                "You're not alone in this. I'm right here with you. 🤝",
                "However you're feeling right now is valid. I'm listening. 👂",
                "You're doing the best you can, and that's always enough. 💚",
                "I believe in you and your ability to get through this. 🌟"
            ]
        }
        
        import random
        messages = fallback_messages.get(stress_category, fallback_messages["default"])
        selected = random.choice(messages)
        print("✅ Using carefully crafted fallback message")
        return selected
    
    def _generate_audio_simple(self, text: str, voice_gender: str) -> str:
        """
        SIMPLE & RELIABLE audio generation using gTTS
        """
        try:
            from gtts import gTTS
            
            # Create temp file
            temp_dir = tempfile.gettempdir()
            filename = f"motivation_{voice_gender}_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = os.path.join(temp_dir, filename)
            
            print(f"🔊 Generating audio: '{text[:50]}...'")
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_path)
            
            # Verify file
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
                print(f"✅ Audio saved: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                
                # Cache file info
                self.audio_files[audio_path] = {
                    'text': text,
                    'voice_gender': voice_gender,
                    'created_at': time.time()
                }
                
                return audio_path
            else:
                print("❌ Audio file creation failed")
                return None
                
        except Exception as e:
            print(f"❌ Audio generation failed: {e}")
            return None
    
    def play_audio(self, audio_path: str) -> bool:
        """
        SIMPLE & RELIABLE audio playback
        """
        try:
            if not audio_path or not os.path.exists(audio_path):
                print("❌ Audio file not found")
                return False
            
            print(f"🔊 Playing: {os.path.basename(audio_path)}")
            
            # Method 1: Try pygame first
            try:
                import pygame
                
                # Stop any current playback
                pygame.mixer.music.stop()
                
                # Load and play
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Check if playing
                import time
                time.sleep(0.5)
                
                if pygame.mixer.music.get_busy():
                    print("✅ Playing with pygame")
                    return True
                    
            except Exception as e:
                print(f"❌ Pygame failed: {e}")
            
            # Method 2: Try system command
            try:
                system = platform.system()
                
                if system == "Windows":
                    os.startfile(audio_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(['afplay', audio_path], check=False)
                else:  # Linux
                    subprocess.run(['xdg-open', audio_path], check=False)
                
                print("✅ Playing with system command")
                return True
                
            except Exception as e:
                print(f"❌ System command failed: {e}")
            
            print("❌ All playback methods failed")
            return False
            
        except Exception as e:
            print(f"❌ Playback error: {e}")
            return False
    
    def stop_audio(self) -> bool:
        """Stop audio playback"""
        try:
            import pygame
            pygame.mixer.music.stop()
            print("⏹️ Audio stopped")
            return True
        except:
            return True
    
    def is_audio_playing(self) -> bool:
        """Check if audio is playing"""
        try:
            import pygame
            return pygame.mixer.music.get_busy()
        except:
            return False
    
    def test_system(self):
        """Test the complete system"""
        print("\n" + "="*50)
        print("🧪 MOTIVATIONAL AGENT SYSTEM TEST")
        print("="*50)
        
        # Test with different stress levels
        test_cases = [
            ("Low", 3.0, "I'm feeling pretty good today"),
            ("Medium", 5.5, "Work is getting a bit stressful"),
            ("High", 7.5, "I'm feeling really overwhelmed"),
            ("Very High", 9.0, "I don't know how to handle this"),
        ]
        
        for stress_category, stress_level, user_message in test_cases:
            print(f"\n🧪 Testing {stress_category} stress...")
            
            request = MotivationRequest(
                stress_level=stress_level,
                stress_category=stress_category,
                user_message=user_message,
                voice_gender="female"
            )
            
            response = self.generate_motivation(request)
            print(f"✅ Message: {response.motivational_message}")
            print(f"✅ LLM Used: {response.llm_used}")
            print(f"✅ Audio: {'Generated' if response.audio_file_path else 'Not generated'}")
        
        print("\n" + "="*50)
        print("🎉 MOTIVATIONAL AGENT TEST COMPLETED")
        print("="*50)

# Create the agent instance
motivational_agent = MotivationalAgent(use_gemini=True)

# Test if run directly
if __name__ == "__main__":
    print("🚀 Starting Motivational Agent Test...")
    motivational_agent.test_system()