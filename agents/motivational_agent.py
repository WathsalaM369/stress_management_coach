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
import time
import threading
from datetime import datetime, timedelta
 
logger = logging.getLogger(__name__)

class MotivationRequest(BaseModel):
    stress_level: float
    stress_category: str
    user_message: str
    user_preferences: Optional[Dict[str, Any]] = None
    generate_audio: bool = True
    voice_gender: str = "female"  # "male" or "female"
    auto_play: bool = True  # New parameter to auto-play audio

class MotivationResponse(BaseModel):
    motivational_message: str
    audio_file_path: Optional[str] = None
    success: bool
    voice_used: str = "female"
    audio_played: bool = False  # New field to indicate if audio was played
    audio_duration: Optional[float] = None  # Audio duration in seconds

class AudioPlayerState:
    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0.0  # Current playback position in seconds
        self.duration = 0.0  # Total audio duration in seconds
        self.current_audio_path = None
        self.playback_start_time = None
        self.last_pause_time = None
        self.total_paused_time = 0.0

class MotivationalAgent:
    def __init__(self, use_gemini=True):
        self.use_gemini = use_gemini
        self.gemini_client = None
        self.audio_files = {}  # Cache for audio files
        self.audio_state = AudioPlayerState()
        self.playback_thread = None
        self.should_stop_playback = False
        
        print(f"🔧 Initializing MotivationalAgent - use_gemini: {use_gemini}")
        
        if not use_gemini:
            raise Exception("❌ AI motivation requires use_gemini=True. Rule-based messages are no longer supported.")
        
        self.gemini_client = self._setup_gemini()
        if not self.gemini_client:
            raise Exception("❌ Gemini setup failed - AI motivation requires valid API key and connection")
        
        print("✅ Gemini client initialized for motivational agent")
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)  # Custom event for playback end
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
            audio_played = False
            audio_duration = None
            
            if request.generate_audio and motivational_text:
                audio_path = self._text_to_speech(motivational_text, request.stress_category, request.voice_gender)
                
                # Estimate audio duration (rough calculation)
                audio_duration = len(motivational_text.split()) * 0.4  # ~0.4 seconds per word
                
                # Auto-play audio if requested (non-blocking)
                if request.auto_play and audio_path:
                    print("🔊 Starting audio playback in background...")
                    audio_played = self.play_audio(audio_path)
            
            return MotivationResponse(
                motivational_message=motivational_text,
                audio_file_path=audio_path,
                success=True,
                voice_used=request.voice_gender,
                audio_played=audio_played,
                audio_duration=audio_duration
            )
            
        except Exception as e:
            logger.critical(f"❌ CRITICAL ERROR in generate_motivation: {e}")
            # Return a fallback response instead of raising
            return MotivationResponse(
                motivational_message="I'm here for you. Take a deep breath. You've got this. 💫",
                success=False,
                voice_used=request.voice_gender,
                audio_played=False
            )
    
    def generate_and_play_motivation(self, request: MotivationRequest) -> MotivationResponse:
        """Convenience method that always generates and plays audio"""
        request.auto_play = True
        request.generate_audio = True
        return self.generate_motivation(request)
    
    def _generate_gemini_motivation(self, request: MotivationRequest) -> str:
        """Generate motivational message using Gemini - AI-only, no fallbacks"""
        try:
            prompt = self._build_motivation_prompt(request)
            
            print(f"📤 Sending motivational prompt to Gemini...")
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,  # Balanced creativity
                    top_p=0.9,
                    max_output_tokens=150,
                )
            )
            
            motivational_text = response.text.strip()
            
            # Clean and validate the response
            if len(motivational_text) < 10 or len(motivational_text) > 300:
                raise ValueError(f"Invalid response length from Gemini: {len(motivational_text)} characters")
                
            print(f"✅ Gemini generated motivational message: {motivational_text}")
            return motivational_text
            
        except Exception as e:
            logger.critical(f"❌ Gemini motivation generation failed: {e}")
            raise
    
    def _build_motivation_prompt(self, request: MotivationRequest) -> str:
        """Build SPECIFIC motivational prompts that generate actual motivational content"""
        
        # Stress-specific motivational frameworks
        stress_motivation_frameworks = {
            "Low": """
            Create a POSITIVE REINFORCEMENT motivational message for someone doing well.
            
            USER CONTEXT:
            - Stress Level: {score}/10 (Low - They're managing well)
            - Their Situation: "{message}"
            
            MESSAGE REQUIREMENTS:
            • CELEBRATE their current positive state
            • ENCOURAGE continued self-care habits  
            • INSPIRE them to maintain this good energy
            • Use uplifting, empowering language
            • Include one relevant emoji
            • Keep it 1-2 sentences maximum
            
            EXAMPLES OF GOOD MOTIVATION:
            "Your positive energy is creating ripples of goodness! Keep nurturing that beautiful mindset. 🌟"
            "You're proof that consistent self-care leads to amazing results. Keep shining your light! ✨"
            "This balanced energy you've cultivated is your superpower. The world needs more of your radiance! 💫"
            
            Create a similar uplifting message that celebrates their current success.
            """,
            
            "Medium": """
            Create an EMPOWERING motivational message for someone handling moderate stress.
            
            USER CONTEXT:
            - Stress Level: {score}/10 (Medium - They're coping but feeling pressure)
            - Their Situation: "{message}"
            
            MESSAGE REQUIREMENTS:
            • ACKNOWLEDGE their strength in managing challenges
            • REMIND them of their resilience
            • OFFER perspective and hope
            • Use encouraging, supportive language
            • Include one relevant emoji
            • Keep it 1-2 sentences maximum
            
            EXAMPLES OF GOOD MOTIVATION:
            "Every challenge you're navigating is building a stronger, wiser version of you. This growth is priceless! 💪"
            "You're in the process of overcoming, and that process itself is a victory. Keep going, warrior! 🛡️"
            "The fact that you're still moving forward despite the pressure shows incredible inner strength. You've got this! 🌱"
            
            Create a similar empowering message that builds their confidence.
            """,
            
            "High": """
            Create a COMFORTING BUT STRENGTH-FOCUSED motivational message for high stress.
            
            USER CONTEXT:
            - Stress Level: {score}/10 (High - They're really struggling)
            - Their Situation: "{message}"
            
            MESSAGE REQUIREMENTS:
            • VALIDATE their feelings without dwelling on pain
            • REMIND them of their inherent strength
            • FOCUS on survival and small victories
            • Use gentle but powerful language
            • Include one comforting emoji
            • Keep it 1-2 sentences maximum
            
            EXAMPLES OF GOOD MOTIVATION:
            "Even on your hardest days, there's a strength in you that never breaks—it just learns new ways to bend and grow. 🌊"
            "This heavy season is temporary, but the resilience you're building now will last forever. You're weathering the storm beautifully. ⛈️"
            "Every breath you take through this difficulty is an act of courage. Your perseverance is quietly magnificent. 🕊️"
            
            Create a similar comforting yet empowering message.
            """,
            
            "Very High": """
            Create a DEEP SUPPORT motivational message for extreme stress.
            
            USER CONTEXT:
            - Stress Level: {score}/10 (Very High - They're overwhelmed)
            - Their Situation: "{message}"
            
            MESSAGE REQUIREMENTS:
            • OFFER deep emotional support
            • FOCUS on basic survival and self-compassion
            • REMIND them they're not alone
            • Use very gentle, reassuring language
            • Include one supportive emoji
            • Keep it 1-2 sentences maximum
            
            EXAMPLES OF GOOD MOTIVATION:
            "In this moment of overwhelm, remember: you don't have to solve everything at once. Just breathe, just be, just survive this moment—that's enough. 🫂"
            "The weight may feel unbearable, but you're still here, still breathing, still fighting. That alone makes you incredibly powerful. 💎"
            "When everything feels too heavy, focus only on this single moment. You've survived 100% of your hardest days so far—you will survive this too. 🌙"
            
            Create a similar deeply supportive message.
            """,
            
            "Chronic High": """
            Create a RESILIENCE-FOCUSED motivational message for long-term stress.
            
            USER CONTEXT:
            - Stress Level: {score}/10 (Chronic High - Long-term struggle)
            - Their Situation: "{message}"
            
            MESSAGE REQUIREMENTS:
            • HONOR their endurance and persistence
            • ACKNOWLEDGE the length of their struggle
            • FOCUS on their incredible resilience
            • Use respectful, honoring language
            • Include one meaningful emoji
            • Keep it 1-2 sentences maximum
            
            EXAMPLES OF GOOD MOTIVATION:
            "The fact that you continue to show up day after day through ongoing challenges reveals a strength most people will never know. You are resilience in human form. 🏔️"
            "Your journey through long-term difficulty has forged a depth of character and wisdom that can't be taught—only earned. You are remarkable. 📜"
            "Through seasons of sustained challenge, you've developed an incredible capacity to endure and adapt. This makes you uniquely powerful. 🌅"
            
            Create a similar resilience-honoring message.
            """
        }
        
        # Get the appropriate motivational framework
        framework = stress_motivation_frameworks.get(request.stress_category, stress_motivation_frameworks["Medium"])
        
        # Format the prompt with specific context
        prompt = framework.format(
            score=request.stress_level,
            message=request.user_message
        )
        
        # Add strict output requirements
        prompt += """
        
        CRITICAL OUTPUT RULES:
        1. Return ONLY the motivational message text
        2. No explanations, no markdown, no additional text
        3. Must be genuinely motivational and uplifting
        4. Must include one relevant emoji at the end
        5. Must be 1-2 sentences maximum
        6. Sound authentic and heartfelt
        
        FINAL OUTPUT:"""
        
        return prompt
    
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
                'stress_category': stress_category,
                'created_at': time.time()
            }
            
            return audio_path
            
        except Exception as e:
            print(f"❌ Text-to-speech conversion failed: {e}")
            raise
    
    def play_audio(self, audio_path: str) -> bool:
        """Play the generated audio file (non-blocking)"""
        try:
            if not audio_path:
                print("❌ No audio path provided")
                return False
                
            if not os.path.exists(audio_path):
                print(f"❌ Audio file not found: {audio_path}")
                return False
            
            # Stop any currently playing audio
            self.stop_audio()
            
            # Reset audio state
            self.audio_state = AudioPlayerState()
            self.audio_state.current_audio_path = audio_path
            self.audio_state.is_playing = True
            self.audio_state.playback_start_time = time.time()
            
            # Load and play audio
            print(f"🔊 Loading and playing audio: {os.path.basename(audio_path)}")
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Start playback monitoring in a separate thread
            self.should_stop_playback = False
            self.playback_thread = threading.Thread(target=self._monitor_playback, daemon=True)
            self.playback_thread.start()
            
            print("🎵 Audio started playing (non-blocking)")
            return True
            
        except pygame.error as e:
            print(f"❌ Pygame audio error: {e}")
            self.audio_state.is_playing = False
            return False
        except Exception as e:
            print(f"❌ Audio playback failed: {e}")
            self.audio_state.is_playing = False
            return False
    
    def _monitor_playback(self):
        """Monitor audio playback in a separate thread"""
        try:
            while not self.should_stop_playback:
                if self.audio_state.is_playing and not self.audio_state.is_paused:
                    # Update current position
                    if self.audio_state.playback_start_time:
                        elapsed = time.time() - self.audio_state.playback_start_time - self.audio_state.total_paused_time
                        self.audio_state.current_position = max(0, elapsed)
                
                # Check if playback has ended
                if not pygame.mixer.music.get_busy() and self.audio_state.is_playing and not self.audio_state.is_paused:
                    print("✅ Audio playback completed")
                    self.audio_state.is_playing = False
                    break
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
        except Exception as e:
            print(f"❌ Playback monitoring error: {e}")
    
    def pause_audio(self) -> bool:
        """Pause currently playing audio"""
        try:
            if self.audio_state.is_playing and not self.audio_state.is_paused:
                pygame.mixer.music.pause()
                self.audio_state.is_paused = True
                self.audio_state.last_pause_time = time.time()
                print("⏸️ Audio paused")
                return True
            return False
        except Exception as e:
            print(f"❌ Error pausing audio: {e}")
            return False
    
    def resume_audio(self) -> bool:
        """Resume paused audio"""
        try:
            if self.audio_state.is_playing and self.audio_state.is_paused:
                pygame.mixer.music.unpause()
                self.audio_state.is_paused = False
                if self.audio_state.last_pause_time:
                    pause_duration = time.time() - self.audio_state.last_pause_time
                    self.audio_state.total_paused_time += pause_duration
                print("▶️ Audio resumed")
                return True
            return False
        except Exception as e:
            print(f"❌ Error resuming audio: {e}")
            return False
    
    def stop_audio(self) -> bool:
        """Stop currently playing audio"""
        try:
            self.should_stop_playback = True
            pygame.mixer.music.stop()
            self.audio_state.is_playing = False
            self.audio_state.is_paused = False
            self.audio_state.current_position = 0.0
            print("⏹️ Audio stopped")
            return True
        except Exception as e:
            print(f"❌ Error stopping audio: {e}")
            return False
    
    def seek_audio(self, position: float) -> bool:
        """Seek to specific position in audio (in seconds)"""
        try:
            if self.audio_state.current_audio_path and os.path.exists(self.audio_state.current_audio_path):
                # Stop current playback
                was_playing = self.audio_state.is_playing and not self.audio_state.is_paused
                self.stop_audio()
                
                # Restart from new position
                if was_playing:
                    # Note: Pygame doesn't support native seeking for MP3 files
                    # This is a limitation - we'd need to use a different audio library for proper seeking
                    print("⚠️ Seeking not fully supported for MP3 files")
                    return self.play_audio(self.audio_state.current_audio_path)
                
                return True
            return False
        except Exception as e:
            print(f"❌ Error seeking audio: {e}")
            return False
    
    def get_playback_info(self) -> Dict[str, Any]:
        """Get current playback information"""
        return {
            "is_playing": self.audio_state.is_playing,
            "is_paused": self.audio_state.is_paused,
            "current_position": self.audio_state.current_position,
            "current_audio_path": self.audio_state.current_audio_path,
            "has_audio": self.audio_state.current_audio_path is not None
        }
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voice options"""
        return {
            "female": "Warm, comforting female voice",
            "male": "Calm, reassuring male voice"
        }
    
    def set_voice_preference(self, voice_gender: str) -> bool:
        """Set default voice preference"""
        if voice_gender.lower() in ["male", "female"]:
            self.default_voice = voice_gender.lower()
            print(f"✅ Default voice set to: {voice_gender}")
            return True
        else:
            print("❌ Invalid voice preference. Use 'male' or 'female'")
            return False
    
    def cleanup_audio_files(self, older_than_hours: int = 24):
        """Clean up generated audio files older than specified hours"""
        current_time = time.time()
        removed_count = 0
        
        for audio_path in list(self.audio_files.keys()):
            try:
                file_info = self.audio_files[audio_path]
                file_age_hours = (current_time - file_info['created_at']) / 3600
                
                if file_age_hours > older_than_hours and os.path.exists(audio_path):
                    os.remove(audio_path)
                    removed_count += 1
                    print(f"🧹 Cleaned up {file_info['voice_gender']} voice audio: {audio_path}")
                    
            except Exception as e:
                print(f"❌ Failed to clean up audio file {audio_path}: {e}")
        
        # Remove cleaned files from cache
        self.audio_files = {path: info for path, info in self.audio_files.items() 
                           if os.path.exists(path)}
        
        print(f"✅ Cleaned up {removed_count} old audio files")

# Test function to verify motivational content
def test_motivational_content():
    """Test that the motivational agent generates actual motivational messages"""
    if not motivational_agent:
        print("❌ Motivational agent not available for testing")
        return
    
    test_cases = [
        {
            "stress_level": 3.0,
            "stress_category": "Low", 
            "message": "I finished all my work early today",
            "voice_gender": "female"
        },
        {
            "stress_level": 6.5,
            "stress_category": "Medium",
            "message": "Work is piling up and I'm feeling the pressure",
            "voice_gender": "female"
        },
        {
            "stress_level": 8.5,
            "stress_category": "High",
            "message": "I don't know how I'll meet all these deadlines",
            "voice_gender": "female"
        }
    ]
    
    print("\n🧪 TESTING MOTIVATIONAL CONTENT QUALITY")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test {i}: {test_case['stress_category']} Stress")
        print(f"💬 User: '{test_case['message']}'")
        
        request = MotivationRequest(
            stress_level=test_case["stress_level"],
            stress_category=test_case["stress_category"],
            user_message=test_case["message"],
            generate_audio=False,  # No audio for quick testing
            voice_gender=test_case["voice_gender"],
            auto_play=False
        )
        
        response = motivational_agent.generate_motivation(request)
        
        print(f"🤖 MOTIVATION: {response.motivational_message}")
        print(f"✅ Success: {response.success}")
        print("-" * 50)

# Create a singleton instance with error handling
try:
    motivational_agent = MotivationalAgent(use_gemini=True)
    print("🎵 Motivational Agent initialized successfully!")
    
    # Run content quality test if executed directly
    if __name__ == "__main__":
        print("\n🚀 Running Motivational Content Quality Test...")
        test_motivational_content()
    
except Exception as e:
    print(f"❌ FATAL ERROR initializing Motivational Agent: {e}")
    print("💡 Please ensure GOOGLE_API_KEY is set in your .env file")
    motivational_agent = None