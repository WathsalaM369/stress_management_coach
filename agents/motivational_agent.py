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
        self.gemini_model = None
        self.gemini_available = False
        self.audio_files = {}
        self.current_audio_path = None
        
        print(f"🎵 Initializing Motivational Agent - use_gemini: {use_gemini}")
        
        # Test audio system first
        self._test_system_dependencies()
        
        # Gemini configuration
        if use_gemini:
            self.gemini_model = self._setup_gemini()
            if self.gemini_model:
                print("✅ Gemini model initialized successfully")
                self.gemini_available = True
            else:
                print("❌ Gemini setup failed, using fallback messages")
                self.gemini_available = False
        
        print("✅ Motivational Agent Ready!")
        print(f"🤖 Gemini Status: {'Available' if self.gemini_available else 'Using Fallback Messages'}")
    
    def _setup_gemini(self):
        """Setup Gemini client with proper error handling"""
        try:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment variables")
                print("💡 Create a .env file with: GOOGLE_API_KEY=your_api_key_here")
                return None
            
            print(f"🔑 API Key found: {api_key[:12]}...")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Use specific model or default - CORRECTED MODEL NAMES
            model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.0-flash-001')
            print(f"🤖 Attempting to use Gemini model: {model_name}")
            
            # Try different model formats - CORRECTED LIST
            model_variations = [
                'models/gemini-2.0-flash-001',  # Your preferred model
                'gemini-2.0-flash-001',
                'models/gemini-2.0-flash',
                'gemini-2.0-flash',
                'models/gemini-1.5-flash',
                'gemini-1.5-flash',
                'models/gemini-1.5-pro', 
                'gemini-1.5-pro',
                'models/gemini-pro',
                'gemini-pro'
            ]
            
            # Remove duplicates and ensure we try the preferred one first
            model_variations = list(dict.fromkeys(model_variations))
            
            successful_model = None
            for model_variant in model_variations:
                try:
                    print(f"🔄 Trying model: {model_variant}")
                    model = genai.GenerativeModel(model_variant)
                    
                    # Test the connection with a simple prompt
                    print("🧪 Testing API connection...")
                    test_response = model.generate_content(
                        "Say only 'SUCCESS'",
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=10
                        )
                    )
                    
                    test_result = test_response.text.strip()
                    print(f"✅ API test successful with {model_variant}! Response: '{test_result}'")
                    successful_model = model
                    break  # Stop at first successful model
                    
                except Exception as e:
                    print(f"❌ Model {model_variant} failed: {str(e)}")
                    continue
            
            if successful_model:
                print(f"🎯 Successfully initialized with model: {model_variant}")
                return successful_model
            else:
                print("❌ All model variations failed")
                return None
            
        except Exception as e:
            print(f"❌ Error in Gemini setup: {str(e)}")
            traceback.print_exc()
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
        Generate motivational message with Gemini (fallback to templates if unavailable)
        """
        print(f"🎯 Generating motivation (Stress: {request.stress_level}, Category: {request.stress_category})")
        print(f"🤖 Gemini Available: {self.gemini_available}")
        print(f"📝 User Message: {request.user_message}")
        
        try:
            # Use Gemini if available, otherwise fallback
            if self.gemini_available and self.gemini_model:
                print("🤖 Using Gemini for motivational message...")
                motivational_text = self._gemini_motivation(request)
                llm_used = True
            else:
                print("🔄 Using fallback motivational messages...")
                motivational_text = self._fallback_motivation(request)
                llm_used = False
            
            # Generate audio if requested
            audio_path = None
            audio_duration = None
            if request.generate_audio and motivational_text:
                audio_path = self._generate_audio_simple(motivational_text, request.voice_gender)
                if audio_path:
                    # Estimate duration (rough calculation)
                    audio_duration = len(motivational_text.split()) * 0.5
            
            return MotivationResponse(
                motivational_message=motivational_text,
                audio_file_path=audio_path,
                success=True,
                voice_used=request.voice_gender,
                audio_duration=audio_duration,
                llm_used=llm_used
            )
            
        except Exception as e:
            print(f"❌ Error in generate_motivation: {e}")
            traceback.print_exc()
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
            # Build comprehensive prompt
            prompt = self._build_motivation_prompt(request)
            
            print("📤 Sending motivation request to Gemini...")
            print(f"📝 Prompt length: {len(prompt)} characters")
            
            # Generate content with Gemini
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,  # More creative
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=150,
                    candidate_count=1
                )
            )
            
            # Extract text from response
            motivational_text = response.text.strip()
            print(f"📨 Gemini raw response: {motivational_text}")
            
            # Validate response
            if self._validate_motivation_response(motivational_text):
                print("✅ Gemini motivation validated successfully")
                return motivational_text
            else:
                print("❌ Gemini response invalid, using fallback")
                return self._fallback_motivation(request)
                
        except Exception as e:
            print(f"❌ Gemini motivation failed: {e}")
            
            # Check for quota issues and disable if needed
            error_str = str(e).lower()
            if "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str:
                print("❌ Gemini quota exceeded - switching to fallback")
                self.gemini_available = False
            elif "not found" in error_str:
                print("❌ Model not found - check model name")
                self.gemini_available = False
            
            return self._fallback_motivation(request)
    
    def _build_motivation_prompt(self, request: MotivationRequest) -> str:
        """Build detailed motivation prompt for Gemini"""
        
        # Define stress-level specific guidance
        stress_guidance = {
            "Low": "Focus on encouragement and celebrating their self-awareness. Keep it light and uplifting.",
            "Medium": "Acknowledge the challenge while reinforcing their strength. Balance empathy with encouragement.",
            "High": "Offer comfort and presence. Validate the difficulty and provide emotional support.",
            "Very High": "Provide calming reassurance and deep emotional support. Make them feel heard and not alone.", 
            "Chronic High": "Acknowledge their endurance and ongoing strength. Honor their resilience through sustained difficulty."
        }
        
        guidance = stress_guidance.get(request.stress_category, "Provide warm, empathetic support")
        
        prompt = f"""Create a brief, supportive motivational message for someone experiencing stress.

CONTEXT:
- Stress Level: {request.stress_level}/10 ({request.stress_category})
- What they shared: "{request.user_message}"

GUIDELINES:
{guidance}

REQUIREMENTS:
• 1-2 sentences maximum (be concise)
• Warm, caring, supportive tone
• Include one relevant emoji at the end  
• Validate their feelings
• Sound genuine and personal
• Focus on emotional support, not advice

IMPORTANT: Return ONLY the motivational message text, nothing else. No explanations."""

        return prompt
    
    def _validate_motivation_response(self, text: str) -> bool:
        """Validate that the Gemini response meets requirements"""
        if not text or len(text.strip()) < 10:
            print("❌ Response too short or empty")
            return False
        
        # Check for reasonable length
        word_count = len(text.split())
        if word_count > 60:  # Too long
            print(f"❌ Response too long: {word_count} words")
            return False
        if word_count < 5:   # Too short
            print(f"❌ Response too short: {word_count} words")
            return False
        
        # Check if it looks like an error message or meta-commentary
        error_indicators = [
            "i cannot", "i can't", "i'm unable", "as an ai",
            "i apologize", "sorry", "i don't have", "i am not",
            "cannot create", "unable to", "here is", "the following"
        ]
        
        text_lower = text.lower()
        for indicator in error_indicators:
            if indicator in text_lower:
                print(f"❌ Response contains error indicator: {indicator}")
                return False
        
        print(f"✅ Response validated: {word_count} words")
        return True
    
    def _fallback_motivation(self, request: MotivationRequest) -> str:
        """Fallback motivational messages"""
        print("🔄 Falling back to template messages")
        return self._get_fallback_message(request.stress_category)
    
    def _get_fallback_message(self, stress_category: str) -> str:
        """Get a fallback motivational message based on stress category"""
        fallback_messages = {
            "Low": [
                "You're doing amazing! Keep shining ✨",
                "So proud of you for taking care of yourself! 🌟",
                "You've got this! Your energy is inspiring 💫",
                "Every small step counts - you're making great progress! 🎯",
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
                "I'm here for you. Take a deep breath. You've got this 💫",
                "You're not alone in this. I'm right here with you 🤝",
                "However you're feeling right now is valid. I'm listening 👂",
                "You're doing the best you can, and that's always enough 💚",
                "I believe in you and your ability to get through this 🌟"
            ]
        }
        
        import random
        messages = fallback_messages.get(stress_category, fallback_messages["default"])
        selected = random.choice(messages)
        print(f"✅ Using fallback message: {selected}")
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
            traceback.print_exc()
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
    
    def test_gemini_directly(self):
        """Test Gemini directly to see if it works"""
        print("\n" + "="*50)
        print("🧪 DIRECT GEMINI TEST")
        print("="*50)
        
        if not self.gemini_available:
            print("❌ Gemini not available")
            return
        
        try:
            # Test with a simple prompt
            test_prompt = "Create a short motivational message for someone feeling stressed. Include one emoji."
            print(f"📤 Testing with prompt: {test_prompt}")
            
            response = self.gemini_model.generate_content(
                test_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=100
                )
            )
            
            print(f"📨 Direct test response: {response.text}")
            print("✅ Direct Gemini test successful!")
            
        except Exception as e:
            print(f"❌ Direct Gemini test failed: {e}")
            traceback.print_exc()
    
    def test_system(self):
        """Test the complete system"""
        print("\n" + "="*50)
        print("🧪 MOTIVATIONAL AGENT SYSTEM TEST")
        print("="*50)
        
        # First test Gemini directly
        self.test_gemini_directly()
        
        # Test with different stress levels
        test_cases = [
            ("Low", 3.0, "I'm feeling pretty good today"),
            ("Medium", 5.5, "Work is getting a bit stressful"),
            ("High", 7.5, "I'm feeling really overwhelmed with deadlines"),
            ("Very High", 9.0, "I don't know how to handle this pressure"),
        ]
        
        for stress_category, stress_level, user_message in test_cases:
            print(f"\n🧪 Testing {stress_category} stress...")
            
            request = MotivationRequest(
                stress_level=stress_level,
                stress_category=stress_category,
                user_message=user_message,
                voice_gender="female",
                generate_audio=False  # Disable audio for testing
            )
            
            response = self.generate_motivation(request)
            print(f"✅ Message: {response.motivational_message}")
            print(f"✅ LLM Used: {response.llm_used}")
            print(f"✅ Success: {response.success}")
        
        print("\n" + "="*50)
        print("🎉 MOTIVATIONAL AGENT TEST COMPLETED")
        print("="*50)

# Create the agent instance
motivational_agent = MotivationalAgent(use_gemini=True)

# Test if run directly
if __name__ == "__main__":
    print("🚀 Starting Motivational Agent Test...")
    motivational_agent.test_system()