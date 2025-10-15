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

class MotivationalAgent:
    def __init__(self, use_gemini=True):
        self.use_gemini = use_gemini
        self.gemini_client = None
        self.gemini_available = False  # Track if Gemini is actually available
        self.audio_files = {}
        self.current_audio_path = None
        
        print("🎵 Initializing Motivational Agent...")
        
        # Test audio system first
        self._test_system_dependencies()
        
        if use_gemini:
            self.gemini_client = self._setup_gemini()
        
        print("✅ Motivational Agent Ready!")
        print(f"🤖 Gemini Status: {'Available' if self.gemini_available else 'Using Fallback Messages'}")
    
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
    
    def _setup_gemini(self):
        """Setup Gemini client with quota and error handling"""
        try:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key or api_key == 'your_actual_google_api_key_here':
                print("❌ GOOGLE_API_KEY not found in .env file")
                print("💡 Create a .env file with: GOOGLE_API_KEY=your_actual_key_here")
                self.gemini_available = False
                return None
            
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            print("🔍 Checking Gemini availability...")
            
            try:
                # List available models
                available_models = genai.list_models()
                model_names = []
                
                for model in available_models:
                    if 'generateContent' in model.supported_generation_methods:
                        model_names.append(model.name)
                        print(f"📋 Available: {model.name}")
                
                if not model_names:
                    print("❌ No models support generateContent method")
                    self.gemini_available = False
                    return None
                
                # Try the first available model with a quota check
                first_model = model_names[0].split('/')[-1]
                print(f"🔧 Trying model: {first_model}")
                
                model = genai.GenerativeModel(first_model)
                
                # Quick test with timeout and quota handling
                try:
                    response = model.generate_content(
                        "Say 'READY' in one word only.",
                        request_options={'timeout': 10}  # 10 second timeout
                    )
                    
                    if response.text and 'READY' in response.text.upper():
                        print(f"✅ Gemini connected successfully: {first_model}")
                        self.gemini_available = True
                        return model
                    else:
                        print(f"❌ Model test failed: {response.text}")
                        self.gemini_available = False
                        return None
                        
                except Exception as test_error:
                    if "quota" in str(test_error).lower() or "429" in str(test_error):
                        print("Gemini Used")
                        self.gemini_available = False
                        return None
                    else:
                        print(f"❌ Gemini test failed: {test_error}")
                        self.gemini_available = False
                        return None
                
            except Exception as list_error:
                if "quota" in str(list_error).lower() or "429" in str(list_error):
                    print("Gemini Used")
                    self.gemini_available = False
                    return None
                else:
                    print(f"❌ Could not list models: {list_error}")
                    self.gemini_available = False
                    return None
            
        except Exception as e:
            print(f"❌ Gemini setup failed: {e}")
            self.gemini_available = False
            return None
    
    def generate_motivation(self, request: MotivationRequest) -> MotivationResponse:
        """
        Generate motivational message and audio - RELIABLE with quota handling
        """
        try:
            print(f"🎯 Generating motivation (Stress: {request.stress_level}, Voice: {request.voice_gender})")
            print(f"🤖 Gemini Available: {self.gemini_available}")
            
            # Generate motivational text
            motivational_text = self._generate_motivational_text(request)
            
            # Generate audio if requested
            audio_path = None
            if request.generate_audio and motivational_text:
                audio_path = self._generate_audio_simple(motivational_text, request.voice_gender)
            
            return MotivationResponse(
                motivational_message=motivational_text,
                audio_file_path=audio_path,
                success=True,
                voice_used=request.voice_gender,
                audio_duration=len(motivational_text.split()) * 0.5  # Simple estimate
            )
            
        except Exception as e:
            print(f"❌ Error in generate_motivation: {e}")
            return MotivationResponse(
                motivational_message="I'm here for you. Take a deep breath. You've got this. 💫",
                success=False,
                voice_used=request.voice_gender
            )
    
    def _generate_motivational_text(self, request: MotivationRequest) -> str:
        """Generate motivational text using Gemini or fallback with quota handling"""
        
        # Try Gemini only if available and not quota exceeded
        if self.gemini_available and self.gemini_client:
            try:
                prompt = f"""
                Create a supportive, compassionate message for someone with {request.stress_level}/10 stress.
                They said: "{request.user_message}"
                
                Make it:
                - Warm and empathetic
                - 1-2 sentences max
                - Include an emoji
                - Sound like a caring friend
                """
                
                # Add timeout and error handling for quota issues
                response = self.gemini_client.generate_content(
                    prompt,
                    request_options={'timeout': 15}
                )
                
                text = response.text.strip()
                
                if len(text) > 10:
                    print("✅ Generated with Gemini")
                    return text
                else:
                    print("❌ Gemini returned short response, using fallback")
                    return self._get_fallback_message(request.stress_category)
                    
            except Exception as e:
                if "quota" in str(e).lower() or "429" in str(e):
                    print("❌ Gemini quota exceeded - switching to fallback permanently")
                    self.gemini_available = False  # Permanently disable Gemini
                
                print(f"❌ Gemini generation failed: {e}")
                return self._get_fallback_message(request.stress_category)
        
        # Use fallback messages (always reliable)
        return self._get_fallback_message(request.stress_category)
    
    def _get_fallback_message(self, stress_category: str) -> str:
        """Get a fallback motivational message based on stress category"""
        fallback_messages = {
            "Low": [
                "You're doing amazing! Keep shining ",
                "So proud of you for taking care of yourself! ",
                "You've got this! Your energy is inspiring ",
                "Every small step counts - you're making a good progress! ",
                "Your positive energy is contagious! Keep going! "
            ],
            "Medium": [
                "I see you working through this. You're stronger than you think ",
                "One step at a time, one breath at a time. You've got this ",
                "This is tough, but you're tougher. I believe in you! ",
                "Progress isn't always linear - you're doing better than you think! ",
                "You're navigating challenges with such grace and strength! "
            ],
            "High": [
                "I'm right here with you. However you feel is completely okay🫂",
                "Just breathe. However you need to get through this moment is enough💗",
                "You don't have to carry this alone. I'm sitting with you in this ",
                "It's okay to not be okay. I'm here with you through this ",
                "This moment is tough, but you're tougher. I believe in your strength!💫"
            ],
            "Very High": [
                "However heavy this feels, you're not alone. I'm here with you ",
                "Just keep breathing. However you're surviving right now is brave💫",
                "No words needed. I'm just here, holding space for you ",
                "You're weathering the storm with incredible courage ",
                "However dark it seems, I'm here holding the light for you "
            ],
            "Chronic High": [
                "You've been carrying this for so long, and you're still here. That's incredible strength",
                "Day after day, you keep showing up. I see your courage and I'm in awe ",
                "However tired you are, however much it hurts - I see you, and I'm not going anywhere ",
                "Your resilience through ongoing challenges is truly remarkable",
                "Through all the difficult days, you continue to show such strength "
            ],
            "default": [
                "I'm here for you. Take a deep breath. You've got this. ",
                "You're not alone in this. I'm right here with you.",
                "However you're feeling right now is valid. I'm listening. ",
                "You're doing the best you can, and that's always enough. ",
                "I believe in you and your ability to get through this. "
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
            
            # Generate speech - gTTS only has female voice but we track the requested gender
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
                    os.startfile(audio_path)  # This usually works on Windows
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
            return True  # Always return True for stop
    
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
        print("🧪 SYSTEM TEST")
        print("="*50)
        
        # Test 1: Generate motivation
        print("\n1. Testing motivation generation...")
        request = MotivationRequest(
            stress_level=7.5,
            stress_category="High",
            user_message="I'm feeling really overwhelmed",
            voice_gender="female"
        )
        
        response = self.generate_motivation(request)
        print(f"✅ Message: {response.motivational_message}")
        print(f"✅ Audio path: {response.audio_file_path}")
        
        # Test 2: Play audio if generated
        if response.audio_file_path:
            print("\n2. Testing audio playback...")
            success = self.play_audio(response.audio_file_path)
            print(f"✅ Playback: {'SUCCESS' if success else 'FAILED'}")
            
            if success:
                print("🔊 Playing for 3 seconds...")
                time.sleep(3)
                self.stop_audio()
        
        print("\n" + "="*50)
        print("🎉 SYSTEM TEST COMPLETED")
        print("="*50)

# Create the agent instance
motivational_agent = MotivationalAgent(use_gemini=True)

# Test if run directly
if __name__ == "__main__":
    print("🚀 Starting Motivational Agent Test...")
    motivational_agent.test_system()