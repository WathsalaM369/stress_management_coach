from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from flask import Flask, request, jsonify, send_from_directory, session
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, session
from flask_cors import CORS
import uvicorn

# Try to import the stress estimator with multiple fallbacks
try:
    from agents.stress_estimator import StressEstimator
    print("✅ Imported StressEstimator successfully")
except ImportError:
    try:
        # Try common alternative class names
        from agents.stress_estimator import StressEstimationAgent as StressEstimator
        print("✅ Imported StressEstimationAgent as StressEstimator")
    except ImportError:
        try:
            from agents.stress_estimator import StressAnalysis as StressEstimator
            print("✅ Imported StressAnalysis as StressEstimator")
        except ImportError:
            try:
                from agents.stress_estimator import StressDetector as StressEstimator
                print("✅ Imported StressDetector as StressEstimator")
            except ImportError:
                # Final fallback - import module and find class
                try:
                    from agents import stress_estimator
                    import inspect
                    
                    # Find all classes in the module
                    classes = []
                    for name, obj in inspect.getmembers(stress_estimator):
                        if inspect.isclass(obj) and obj.__module__ == 'agents.stress_estimator':
                            classes.append((name, obj))
                    
                    if classes:
                        # Use the first class found
                        class_name, class_obj = classes[0]
                        StressEstimator = class_obj
                        print(f"✅ Imported {class_name} as StressEstimator")
                    else:
                        raise ImportError("No classes found in stress_estimator module")
                        
                except Exception as e:
                    print(f"❌ All import attempts failed: {e}")
                    # Create a simple fallback class
                    class StressEstimator:
                        def __init__(self, use_database=True, use_llm=True):
                            self.use_database = use_database
                            self.use_llm = use_llm
                            print("⚠️ Using fallback StressEstimator")
                        
                        def enhanced_comprehensive_analysis(self, data, user_id):
                            return {
                                "stress_score": 5.0,
                                "stress_level": "Medium", 
                                "explanation": "Fallback analysis - original estimator not available",
                                "success": True
                            }

from agents.motivational_agent import motivational_agent, MotivationRequest
from config import Config
from agents.activity_recommender_flask import activity_bp
from agents.stress_estimator import StressEstimator
from agents.adaptive_scheduler_agent import scheduler_agent
from datetime import datetime, timedelta
import requests
import json
import os
import secrets
import hashlib
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# FastAPI App (Vinusha's version)
fastapi_app = FastAPI(title="Stress Management Coach API")

# CORS middleware for FastAPI
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config()

# Flask App (Wathsala's version)
flask_app = Flask(__name__)
flask_app.secret_key = 'mindsoothe-secret-key-2024'
flask_app.config['SESSION_TYPE'] = 'filesystem'
flask_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Enhanced CORS with Gemini support for Flask
CORS(flask_app, supports_credentials=True, origins=['http://localhost:3000', 'http://localhost:5001'])
# Enhanced CORS with Gemini support
CORS(flask_app, supports_credentials=True, origins=['http://localhost:3000', 'http://localhost:5001'])

# =============================================================================
# SENUTHI'S ACTIVITY RECOMMENDER SETUP
# =============================================================================

# Simple mock for stress estimation (used by activity recommender)
class MockStressEstimator:
    def estimate_stress_level(self, text):
        if not text:
            return {"stress_level": "Medium", "score": 0.5, "message": "No text provided"}
        
        text_lower = text.lower()
        if any(word in text_lower for word in ['stress', 'anxious', 'overwhelm', 'pressure', 'worry']):
            return {"stress_level": "High", "score": 0.8, "message": "You seem to be experiencing high stress levels"}
        elif any(word in text_lower for word in ['tired', 'busy', 'hectic', 'lot to do']):
            return {"stress_level": "Medium", "score": 0.6, "message": "You flask_appear to have moderate stress"}
        else:
            return {"stress_level": "Low", "score": 0.3, "message": "You seem to be doing well"}

agent = MockStressEstimator()

# Register activity recommender blueprint
flask_app.register_blueprint(activity_bp, url_prefix='/api/activity_recommender')

# =============================================================================
# WATHSALA'S STRESS ESTIMATOR SETUP
# =============================================================================

# Initialize stress estimator with Gemini for Flask
use_llm = os.getenv('USE_LLM', 'true').lower() == 'true'
print(f"🔧 LLM Mode: {use_llm}")

if use_llm:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key or api_key == 'your_actual_google_api_key_here':
        print("❌ No valid Google API key found. Disabling LLM.")
        use_llm = False

# Initialize the stress estimator
flask_estimator = StressEstimator(use_database=True, use_llm=use_llm)

# In-memory user store (in production, use a real database)
users_db = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

# FastAPI Routes (Vinusha's endpoints)
@fastapi_app.post("/estimate-stress")
async def estimate_stress_endpoint(text: str):
    try:
        result = flask_estimator.estimate_stress_level(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/generate-motivation")
async def generate_motivation_endpoint(request: MotivationRequest):
    try:
        result = motivational_agent.generate_motivation(request)
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/")
async def root():
    return {"message": "Stress Management Coach API is running"}

@fastapi_app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Flask Routes (Wathsala's endpoints)
@flask_app.route('/api/register', methods=['POST'])
def get_current_user_id():
    """Get current user ID or create temporary one"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = f"temp_{secrets.token_hex(8)}"
        session['user_id'] = user_id
        session['username'] = 'Guest'
        print(f"🆕 Created temporary user: {user_id}")
    return user_id

# =============================================================================
# SENUTHI'S ACTIVITY RECOMMENDER WEB ROUTES
# =============================================================================

@flask_app.route('/')
def index():
    """Serve Wathsala's stress estimator frontend"""
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        # Fallback: if frontend folder doesn't exist, show a simple menu
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>MindSoothe - Stress Management System</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    color: #333;
                }
                h1 { color: #667eea; margin-bottom: 30px; }
                .btn {
                    display: inline-block;
                    padding: 15px 30px;
                    margin: 10px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-size: 16px;
                    transition: all 0.3s;
                }
                .btn:hover {
                    background: #764ba2;
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }
                .btn-secondary {
                    background: #48bb78;
                }
                .btn-secondary:hover {
                    background: #38a169;
                }
                p { font-size: 18px; line-height: 1.6; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧠 MindSoothe - Stress Management System</h1>
                <p>Welcome! Choose a feature to get started:</p>
                
                <div style="margin-top: 30px;">
                    <a href="/stress-assessment" class="btn">
                        📊 Stress Assessment (Wathsala's Feature)
                    </a>
                    <br>
                    <a href="/activity-recommender" class="btn btn-secondary">
                        🎯 Get Activity Recommendations (Senuthi's Feature)
                    </a>
                </div>
                
                <div style="margin-top: 40px; padding: 20px; background: #f7fafc; border-radius: 8px;">
                    <h3 style="color: #667eea;">📍 Quick Links:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li>✅ <a href="/api/health">System Health Check</a></li>
                        <li>✅ <a href="/users">View All Users</a></li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''

@flask_app.route('/stress-assessment')
def stress_assessment():
    """Wathsala's stress assessment interface"""
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        return jsonify({"error": "Stress assessment frontend not found"}), 404

@flask_app.route('/activity-recommender')
def activity_recommender():
    """Senuthi's activity recommender interface with AI"""
    try:
        # First try templates folder
        return render_template('activity_recommendations.html')
    except:
        # Then try root directory
        try:
            with open('activity_recommendations.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Activity Recommendations</title>
                <style>
                    body { font-family: Arial; text-align: center; padding: 50px; }
                    .error { color: red; }
                </style>
            </head>
            <body>
                <h1 class="error">⚠️ Activity Recommendations Page Not Found</h1>
                <p>The file 'activity_recommendations.html' is missing.</p>
                <p>Please check:</p>
                <ul style="text-align: left; max-width: 500px; margin: 20px auto;">
                    <li>File exists in 'templates' folder OR</li>
                    <li>File exists in root directory (same as app.py)</li>
                </ul>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            ''', 404

@flask_app.route('/onboard', methods=['GET', 'POST'])
def onboard():
    if request.method == 'POST':
        username = request.form.get('username')
        likes = request.form.getlist('likes')
        default_time = int(request.form.get('default_time', 10))
        
        print(f"DEBUG: Creating user '{username}' with likes: {likes}")
        
        try:
            # Create user via API
            response = requests.post(
                'http://localhost:5001/api/activity_recommender/users',
                json={'username': username},
                timeout=5
            )
            
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response content: {response.text}")
            
            if response.status_code == 201:
                user_data = response.json()
                user_id = user_data['id']
                
                # Set preferences
                pref_response = requests.put(
                    f'http://localhost:5001/api/activity_recommender/users/{user_id}/preferences',
                    json={
                        'likes': likes, 
                        'default_available_minutes': default_time
                    },
                    timeout=5
                )
                
                print(f"DEBUG: Preferences response: {pref_response.status_code}")
                
                if pref_response.status_code == 200:
                    return redirect(url_for('recommend_success', user_id=user_id))
                else:
                    return render_template('user_onboard.html', error="Error setting preferences")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                except:
                    error_msg = f"Server returned status {response.status_code}"
                
                return render_template('user_onboard.html', error=error_msg)
                
        except requests.exceptions.RequestException as e:
            return render_template('user_onboard.html', error=f"Connection error: {str(e)}")
        except Exception as e:
            return render_template('user_onboard.html', error=f"Unexpected error: {str(e)}")
    
    return render_template('user_onboard.html')

@flask_app.route('/recommend-success/<int:user_id>')
def recommend_success(user_id):
    return render_template('activity_rec_result.html', user_id=user_id, message="Account created successfully!")

@flask_app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        username = request.form.get('username')
        stress_level = request.form.get('stress_level')
        available_minutes = int(request.form.get('available_minutes', 10))
        user_text = request.form.get('user_text', '')
        
        if not username:
            return render_template('activity_rec_form.html', error="Username is required")
        
        # Get stress level from text if provided
        stress_result = None
        if user_text:
            stress_result = agent.estimate_stress_level(user_text)
            stress_level = stress_result['stress_level']
        
        try:
            # Get all users
            response = requests.get('http://localhost:5001/api/activity_recommender/users')
            
            if response.status_code == 200:
                users = response.json()
                user_id = None
                user_found = None
                
                # Find user by username (case-insensitive)
                for user in users:
                    if user['username'].lower() == username.lower():
                        user_id = user['id']
                        user_found = user
                        break
                
                if not user_id:
                    return render_template('activity_rec_form.html', 
                                         error=f"User '{username}' not found. Please check the username or create a new account.")
                
                # Get recommendations
                rec_response = requests.post(
                    'http://localhost:5001/api/activity_recommender/recommend',
                    json={
                        'stress_level': stress_level,
                        'user_id': user_id,
                        'context': {'available_minutes': available_minutes}
                    }
                )
                
                if rec_response.status_code == 200:
                    result = rec_response.json()
                    recommendations = result.get('recommendations', [])
                    
                    return render_template('activity_rec_result.html',
                                         recommendations=recommendations,
                                         stress_result=stress_result,
                                         username=username,
                                         user=user_found)
                else:
                    error_msg = rec_response.json().get('error', 'Unknown error')
                    return render_template('activity_rec_form.html', 
                                         error=f"Error getting recommendations: {error_msg}")
            else:
                return render_template('activity_rec_form.html', 
                                     error="Cannot access user database. Please try again.")
                
        except requests.exceptions.RequestException as e:
            return render_template('activity_rec_form.html', 
                                 error=f"Connection error: {str(e)}")
    
    # For GET requests, check if username is provided in URL parameters
    username = request.args.get('username', '')
    return render_template('activity_rec_form.html', username=username)

@flask_app.route('/users')
def users_list():
    """Display all registered users"""
    try:
        response = requests.get('http://localhost:5001/api/activity_recommender/users')
        if response.status_code == 200:
            users = response.json()
            return render_template('users_list.html', users=users)
        else:
            return render_template('users_list.html', users=[], error="Cannot fetch users")
    except requests.exceptions.RequestException as e:
        return render_template('users_list.html', users=[], error=f"Connection error: {str(e)}")

@flask_app.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        response = requests.get('http://localhost:5001/api/activity_recommender/users')
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify([])
    except:
        return jsonify([])

@flask_app.route('/api/estimate_stress', methods=['POST'])
def estimate_stress():
    data = request.get_json()
    text = data.get('text', '')
    result = agent.estimate_stress_level(text)
    return jsonify(result)

@flask_app.route('/api/get-activity-recommendations', methods=['POST', 'OPTIONS'])
def get_activity_recommendations():
    """Generate AI-powered activity recommendations based on stress level"""
    try:
        data = request.get_json()
        print(f"📥 Received recommendation request: {data}")
        
        stress_score = data.get('stress_score', 5.0)
        stress_level = data.get('stress_level', 'Medium')
        available_minutes = data.get('available_minutes', 15)
        preferences = data.get('preferences', ['physical', 'creative', 'mindful', 'social'])
        
        print(f"🎯 Generating recommendations for stress level: {stress_level} ({stress_score}/10)")
        print(f"⏰ Available time: {available_minutes} minutes")
        print(f"🎨 Preferences: {preferences}")
        
        # Use Gemini AI to generate recommendations
        if estimator.use_llm:
            print("🤖 Using Gemini AI for recommendations...")
            import google.generativeai as genai
            
            # Configure API with the same key as the rest of the system
            api_key = os.getenv('GOOGLE_API_KEY')
            genai.configure(api_key=api_key)
            
            # Use the model from .env or default to gemini-2.0-flash-001
            model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.0-flash-001')
            print(f"🤖 Using model: {model_name}")
            
            prompt = f"""You are a stress management expert. Generate 4-5 personalized activity recommendations for someone with:

Stress Level: {stress_level} ({stress_score}/10)
Available Time: {available_minutes} minutes
Preferred Activity Types: {', '.join(preferences)}

For each activity, provide:
1. Name (short, catchy)
2. Description (2-3 sentences explaining benefits)
3. Duration (in minutes, should fit within {available_minutes} minutes)
4. Category (one of: physical, creative, mindful, social)
5. Difficulty (Easy, Moderate, or Challenging)
6. Icon (single emoji that represents the activity)
7. Steps (3-5 simple steps to do the activity)

Also provide a brief AI insight (2-3 sentences) explaining why these activities are good for their current stress level.

Return ONLY a valid JSON object with this structure:
{{
    "ai_insight": "Brief explanation here",
    "recommendations": [
        {{
            "name": "Activity Name",
            "description": "Why this helps",
            "duration": 10,
            "category": "mindful",
            "difficulty": "Easy",
            "icon": "🧘",
            "steps": ["Step 1", "Step 2", "Step 3"]
        }}
    ]
}}

Make activities practical, evidence-based, and immediately actionable. Focus on activities that can reduce {stress_level.lower()} stress."""

            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                print("✅ Gemini response received")
                
                # Parse the JSON response
                import re
                response_text = response.text.strip()
                print(f"📄 Raw response length: {len(response_text)} characters")
                
                # Remove markdown code blocks if present
                response_text = re.sub(r'```json\s*|\s*```', '', response_text)
                
                recommendations_data = json.loads(response_text)
                
                print(f"✅ Generated {len(recommendations_data.get('recommendations', []))} AI recommendations")
                return jsonify(recommendations_data)
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"📄 Response text: {response_text[:500]}...")
                # Fallback to simple recommendations
                print("⚠️ Falling back to simple recommendations")
                
        else:
            print("⚠️ LLM disabled, using fallback recommendations")
        
        # Fallback: Simple rule-based recommendations
        fallback_recommendations = {
            "ai_insight": f"Based on your {stress_level.lower()} stress level ({stress_score}/10), here are some evidence-based activities that can help you feel better right now.",
            "recommendations": [
                {
                    "name": "Deep Breathing Exercise",
                    "description": "Calm your nervous system with controlled breathing. This simple technique activates your body's relaxation response and can reduce stress hormones within minutes.",
                    "duration": 5,
                    "category": "mindful",
                    "difficulty": "Easy",
                    "icon": "🌬️",
                    "steps": [
                        "Sit comfortably with your back straight",
                        "Breathe in slowly through your nose for 4 counts",
                        "Hold your breath for 4 counts",
                        "Exhale slowly through your mouth for 6 counts",
                        "Repeat 10 times, focusing on your breath"
                    ]
                },
                {
                    "name": "Quick Walk Outside",
                    "description": "Physical movement and fresh air can instantly boost your mood and reduce stress hormones. Walking combines exercise with a change of environment.",
                    "duration": min(15, available_minutes),
                    "category": "physical",
                    "difficulty": "Easy",
                    "icon": "🚶‍♂️",
                    "steps": [
                        "Put on comfortable shoes",
                        "Step outside and take a brisk walk",
                        "Focus on your surroundings - notice 5 things you can see",
                        "Take deep breaths of fresh air",
                        "Return feeling refreshed"
                    ]
                },
                {
                    "name": "Creative Journaling",
                    "description": "Express your thoughts and feelings on paper. Journaling helps process emotions and gain clarity about what's bothering you.",
                    "duration": 10,
                    "category": "creative",
                    "difficulty": "Easy",
                    "icon": "📝",
                    "steps": [
                        "Grab a notebook or open a document",
                        "Write freely about what's on your mind",
                        "Don't worry about grammar or structure",
                        "Include both feelings and thoughts",
                        "Read it back if helpful, or just let it out"
                    ]
                },
                {
                    "name": "Progressive Muscle Relaxation",
                    "description": "Release physical tension by systematically tensing and relaxing muscle groups. This helps you become aware of tension and learn to release it.",
                    "duration": 10,
                    "category": "mindful",
                    "difficulty": "Easy",
                    "icon": "💆‍♂️",
                    "steps": [
                        "Lie down or sit comfortably",
                        "Tense your feet for 5 seconds, then release",
                        "Move up through legs, stomach, arms, and face",
                        "Notice the difference between tension and relaxation",
                        "Breathe deeply throughout"
                    ]
                }
            ]
        }
        
        print(f"✅ Returning {len(fallback_recommendations['recommendations'])} fallback recommendations")
        return jsonify(fallback_recommendations)
            
    except Exception as e:
        print(f"❌ Error generating recommendations: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "ai_insight": "We encountered an error generating personalized recommendations.",
            "recommendations": [
                {
                    "name": "Take a Deep Breath",
                    "description": "Let's start simple. Take 5 deep breaths right now.",
                    "duration": 2,
                    "category": "mindful",
                    "difficulty": "Easy",
                    "icon": "🌬️",
                    "steps": [
                        "Breathe in for 4 counts",
                        "Hold for 4 counts",
                        "Breathe out for 6 counts",
                        "Repeat 5 times"
                    ]
                }
            ]
        }), 500

# =============================================================================
# WATHSALA'S STRESS ESTIMATOR API ROUTES
# =============================================================================

@flask_app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        if username in users_db:
            return jsonify({"error": "Username already exists"}), 400

        user_id = f"user_{secrets.token_hex(8)}"
        users_db[username] = {
            'user_id': user_id,
            'password': hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat()
        }

        # Set session
        session.permanent = True
        session['user_id'] = user_id
        session['username'] = username

        print(f"✅ User registered: {username}, user_id: {user_id}")
        print(f"📊 Total users: {len(users_db)}")

        return jsonify({
            "message": "Registration successful",
            "user_id": user_id,
            "username": username
        })

    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        user = users_db.get(username)
        if not user or not verify_password(user['password'], password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Set session
        session.permanent = True
        session['user_id'] = user['user_id']
        session['username'] = username

        print(f"✅ User logged in: {username}, user_id: {user['user_id']}")

        return jsonify({
            "message": "Login successful",
            "user_id": user['user_id'],
            "username": username
        })

    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username')
    session.clear()
    print(f"✅ User logged out: {username}")
    return jsonify({"message": "Logout successful"})

@flask_app.route('/api/current-user', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    username = session.get('username')
    
    print(f"🔍 Checking current user - user_id: {user_id}, username: {username}")
    
    if user_id and username:
        return jsonify({
            "logged_in": True,
            "user_id": user_id,
            "username": username
        })
    else:
        return jsonify({"logged_in": False})

def get_current_user_id():
    """Get current user ID or create temporary one"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = f"temp_{secrets.token_hex(8)}"
        session['user_id'] = user_id
        session['username'] = 'Guest'
        print(f"🆕 Created temporary user: {user_id}")
    return user_id

@flask_app.route('/api/analyze-mood', methods=['POST', 'OPTIONS'])
@flask_app.route('/api/analyze-mood', methods=['POST', 'OPTIONS'])
def analyze_mood():
    if request.method == 'OPTIONS':
        return jsonify({"status": "preflight"})
        
    try:
        print("📥 Received mood analysis request")
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = get_current_user_id()
        data['user_id'] = user_id
        
        print(f"🔍 Analyzing data for user: {user_id}")
        print(f"📊 Data type: {data.get('input_method')}")
        
        if is_duplicate_request(user_id, data):
            print("🔄 Duplicate request detected, skipping...")
            return jsonify({"error": "Duplicate request"}), 400
        
        # Use Gemini for analysis
        result = flask_estimator.enhanced_comprehensive_analysis(data, user_id)
        
        # Get updated trend after analysis
        trend = get_user_trend_fixed(user_id)
        result['trend'] = trend
        
        print(f"✅ Analysis complete: {result['stress_level']} ({result['stress_score']}/10)")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Error in analyze_mood: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/analyze-comprehensive', methods=['POST', 'OPTIONS'])
def analyze_comprehensive():
    """Enhanced comprehensive analysis with Gemini ONLY"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "preflight"})
        
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        print(f"🧠 Comprehensive analysis for user: {user_id}")
        
        # Prepare data for analysis
        analysis_data = {
            'user_id': user_id,
            'assessment_data': data.get('assessment_data', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        # Use analysis
        result = flask_estimator.enhanced_comprehensive_analysis(analysis_data, user_id)
        
        # Get updated trend
        trend = get_user_trend_fixed(user_id)
        result['trend'] = trend
        
        print(f"✅ Comprehensive analysis complete: {result['stress_score']}/10 - {result['stress_level']}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Comprehensive analysis error: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

last_requests = {}

def is_duplicate_request(user_id, data):
    current_time = datetime.now().timestamp()
    request_key = f"{user_id}_{data.get('input_method')}_{data.get('bubble_type', data.get('emoji', data.get('scene', data.get('color', ''))))}"
    
    if request_key in last_requests:
        time_diff = current_time - last_requests[request_key]
        if time_diff < 2:
            return True
    
    last_requests[request_key] = current_time
    
    # Clean up old requests
    for key in list(last_requests.keys()):
        if current_time - last_requests[key] > 10:
            del last_requests[key]
    
    return False

def get_user_trend_fixed(user_id):
    """Fixed trend calculation without numpy"""
    try:
        history = flask_estimator.db_manager.get_user_history(user_id, 100)
        
        if len(history) < 2:
            return "insufficient_data"
        
        # Get recent entries
        recent_history = history[:5]
        
        if len(recent_history) < 2:
            return "insufficient_data"
        
        # Extract scores
        scores = []
        for record in recent_history:
            try:
                score = float(record['stress_score'])
                scores.append(score)
            except (ValueError, KeyError):
                continue
        
        if len(scores) < 2:
            return "insufficient_data"
        
        # Simple trend calculation
        chronological_scores = list(reversed(scores))
        
        # Calculate average of first half vs second half
        mid_point = len(chronological_scores) // 2
        first_avg = sum(chronological_scores[:mid_point]) / mid_point
        second_avg = sum(chronological_scores[mid_point:]) / (len(chronological_scores) - mid_point)
        
        trend_diff = second_avg - first_avg
        
        if trend_diff > 0.1:
            return "increasing"
        elif trend_diff < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    except Exception as e:
        print(f"❌ Error in trend calculation: {e}")
        return "unknown"
    
@flask_app.route('/api/history/<user_id>', methods=['GET'])

@flask_app.route('/api/history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    try:
        print(f"📊 Getting history for user: {user_id}")
        history = flask_estimator.db_manager.get_user_history(user_id)
        
        print(f"📋 History records found: {len(history)}")
        for i, record in enumerate(history[:3]):
            print(f"  Record {i}: {record.get('stress_score', 'N/A')} - {record.get('timestamp', 'N/A')}")
        
        return jsonify({
            "user_id": user_id,
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        print(f"❌ Error getting history: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/chart-data/<user_id>', methods=['GET'])
def get_chart_data(user_id):
    try:
        print(f"📈 Getting chart data for user: {user_id}")
        history = flask_estimator.db_manager.get_user_history(user_id, 30)
        
        print(f"📋 Database returned {len(history)} records for chart")
        
        if not history:
            print("📊 No user data, returning sample data")
            return jsonify({
                "has_data": False,
                "message": "No history data yet. Complete an assessment to see your stress history!",
                "sample_data": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "scores": [4.2, 5.1, 3.8, 6.2, 7.5, 4.0, 3.5],
                    "is_sample": True
                }
            })
        
        # Get the 7 most recent entries
        recent_history = history[:7]
        chart_data = {
            "has_data": True,
            "is_sample": False,
            "labels": [],
            "scores": [],
            "levels": [],
            "timestamps": [],
            "total_records": len(history)
        }
        
        # Reverse to show chronological order (oldest first)
        for record in reversed(recent_history):
            try:
                timestamp = record['timestamp']
                if 'T' in timestamp:
                    date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                
                chart_data['labels'].append(date_obj.strftime('%m/%d %H:%M'))
                chart_data['scores'].append(float(record['stress_score']))
                chart_data['levels'].append(record['stress_level'])
                chart_data['timestamps'].append(timestamp)
            except Exception as e:
                print(f"Error parsing record: {record}, error: {e}")
                continue
        
        print(f"✅ Chart data prepared: {len(chart_data['scores'])} data points")
        print(f"📊 Chart scores: {chart_data['scores']}")
        return jsonify(chart_data)
        
    except Exception as e:
        print(f"❌ Error in get_chart_data: {e}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    try:
        print(f"📊 Getting stats for user: {user_id}")
        history = flask_estimator.db_manager.get_user_history(user_id, 100)
        
        print(f"📋 Stats: Found {len(history)} records for user {user_id}")
        
        if not history:
            print("📊 No stats data available")
            return jsonify({
                "has_data": False,
                "message": "No data available yet. Complete an assessment to see your statistics!",
                "total_entries": 0,
                "average_stress": 0,
                "trend": "no_data"
            })
        
        scores = []
        levels = []
        
        for record in history:
            try:
                score = float(record['stress_score'])
                scores.append(score)
                levels.append(record['stress_level'])
            except (ValueError, KeyError) as e:
                print(f"⚠️ Error processing record for stats: {record}, error: {e}")
                continue
        
        if not scores:
            return jsonify({
                "has_data": False,
                "message": "No valid data available",
                "total_entries": 0,
                "average_stress": 0,
                "trend": "no_data"
            })
        
        trend = get_user_trend_fixed(user_id)
        
        # Calculate level distribution
        level_distribution = {}
        for level in levels:
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        stats = {
            "has_data": True,
            "total_entries": len(history),
            "average_stress": round(sum(scores) / len(scores), 1),
            "current_stress": scores[0] if scores else 0,
            "level_distribution": level_distribution,
            "trend": trend,
            "first_entry": history[-1]['timestamp'] if history else None,
            "last_entry": history[0]['timestamp'] if history else None
        }
        
        print(f"✅ Stats calculated: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to see all registered users"""
    return jsonify({
        "total_users": len(users_db),
        "users": users_db
    })

@flask_app.route('/api/debug/session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session"""
    return jsonify({
        "session_data": dict(session),
        "user_id": session.get('user_id'),
        "username": session.get('username')
    })



# =============================================================================
# MANUTHI'S TASK SCHEDULER DATABASE SETUP
# =============================================================================
Base = declarative_base()
scheduler_engine = create_engine('sqlite:///scheduler.db')
SchedulerSession = sessionmaker(bind=scheduler_engine)

class UserRoutine(Base):
    __tablename__ = 'user_routines'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    routine_data = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class UserSchedule(Base):
    __tablename__ = 'user_schedules'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    schedule_data = Column(Text)
    week_start = Column(String)
    stress_level = Column(Float)
    mood = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class TaskRecord(Base):
    __tablename__ = 'task_records'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    tasks_data = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

Base.metadata.create_all(scheduler_engine)

# Configure Gemini for Scheduler
gemini_api_key = os.getenv('GOOGLE_API_KEY')
if gemini_api_key and gemini_api_key != 'your_actual_google_api_key_here':
    genai.configure(api_key=gemini_api_key)
    scheduler_model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.0-flash-001')
    scheduler_model = genai.GenerativeModel(scheduler_model_name)
    print(f"✅ Scheduler Gemini configured: {scheduler_model_name}")
else:
    scheduler_model = None
    print("⚠️ Scheduler Gemini not configured - API key missing")

# =============================================================================
# MANUTHI'S TASK SCHEDULER ROUTES
# =============================================================================
@flask_app.route('/task-scheduler')
def task_scheduler():
    """Main Task Scheduler Interface"""
    try:
        with open('task_scheduler.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"error": "Task scheduler page not found"}), 404

@flask_app.route('/api/scheduler/check-status', methods=['GET'])
def check_scheduler_status():
    """Check if user has routine and recent stress assessment"""
    user_id = get_current_user_id()
    
    db_scheduler = SchedulerSession()
    try:
        # Check for existing routine
        existing_routine = db_scheduler.query(UserRoutine).filter_by(user_id=user_id).first()
        has_routine = existing_routine is not None
        
        # Check for recent stress assessment (within 24 hours)
        stress_history = flask_estimator.db_manager.get_user_history(user_id, 1)
        
        has_stress = False
        latest_stress = None
        
        if stress_history and len(stress_history) > 0:
            latest_stress = stress_history[0]
            try:
                assessment_time = datetime.fromisoformat(latest_stress['timestamp'].replace('Z', '+00:00'))
                time_diff = datetime.now() - assessment_time
                if time_diff.total_seconds() < 86400:  # 24 hours
                    has_stress = True
            except:
                has_stress = True
        
        return jsonify({
            'status': 'success',
            'has_routine': has_routine,
            'has_stress_assessment': has_stress,
            'stress_data': latest_stress if has_stress else None
        })
    finally:
        db_scheduler.close()

@flask_app.route('/api/scheduler/save-routine', methods=['POST'])
def save_scheduler_routine():
    """Save or update user's weekly routine"""
    data = request.json
    user_id = get_current_user_id()
    
    db = SchedulerSession()
    try:
        existing = db.query(UserRoutine).filter_by(user_id=user_id).first()
        
        routine_json = json.dumps({
            'weekly_routine': data.get('routine'),
            'work_hours': data.get('work_hours'),
            'sleep_schedule': data.get('sleep_schedule'),
            'preferences': data.get('preferences'),
            'energy_levels': data.get('energy_levels')
        })
        
        if existing:
            existing.routine_data = routine_json
            existing.updated_at = datetime.now()
            message = 'Routine updated successfully'
        else:
            new_routine = UserRoutine(user_id=user_id, routine_data=routine_json)
            db.add(new_routine)
            message = 'Routine saved successfully'
        
        db.commit()
        print(f"✅ {message} for user: {user_id}")
        return jsonify({'status': 'success', 'message': message})
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving routine: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()

@flask_app.route('/api/scheduler/get-routine', methods=['GET'])
def get_scheduler_routine():
    """Get user's saved routine"""
    user_id = get_current_user_id()
    
    db = SchedulerSession()
    try:
        routine_record = db.query(UserRoutine).filter_by(user_id=user_id).first()
        
        if routine_record:
            routine_data = json.loads(routine_record.routine_data)
            return jsonify({
                'status': 'success',
                'routine': routine_data,
                'updated_at': routine_record.updated_at.isoformat()
            })
        else:
            return jsonify({'status': 'error', 'message': 'No routine found'}), 404
    finally:
        db.close()

@flask_app.route('/api/scheduler/generate-schedule', methods=['POST'])
def generate_scheduler_schedule():
    """Generate optimized schedule using Gemini"""
    data = request.json
    user_id = get_current_user_id()
    
    if not scheduler_model:
        return jsonify({'status': 'error', 'message': 'AI scheduling not available. Please check Gemini API configuration.'}), 500
    
    tasks = data.get('tasks', [])
    week_start = data.get('week_start')
    stress_score = data.get('stress_score', 5)
    stress_level = data.get('stress_level', 'Medium')
    mood = data.get('mood', 'neutral')
    
    print(f"🗓️ Generating schedule for {len(tasks)} tasks, stress: {stress_score}/10")
    
    db = SchedulerSession()
    try:
        # Get user's routine
        user_routine_record = db.query(UserRoutine).filter_by(user_id=user_id).first()
        
        if not user_routine_record:
            return jsonify({
                'status': 'error',
                'message': 'No routine found. Please set up your weekly routine first.'
            }), 404
        
        routine_data = json.loads(user_routine_record.routine_data)
        routine = routine_data.get('weekly_routine', {})
        
        # Build enhanced prompt
        prompt = f"""You are an AI Task Scheduler. Create an optimized weekly schedule with STRICT DEADLINE compliance.

USER'S WEEKLY ROUTINE:
{json.dumps(routine, indent=2)}

TASKS TO SCHEDULE (sorted by urgency):
{json.dumps(sorted(tasks, key=lambda x: (x.get('deadline', '9999-12-31'), 0 if x.get('priority')=='high' else 1)), indent=2)}

STRESS CONTEXT:
- Stress Score: {stress_score}/10
- Stress Level: {stress_level}
- Mood: {mood}
- Week Start: {week_start}

SCHEDULING RULES:
1. HIGH PRIORITY + URGENT DEADLINES FIRST (deadline within 2 days)
2. ALL tasks MUST be scheduled BEFORE their deadline
3. High stress (≥7): Max 4-5h work/day, 20min buffers, frequent breaks
4. Medium stress (4-6): Max 6-7h work/day, 10min buffers
5. Low stress (1-3): Up to 8h work/day, standard buffers
6. NEVER schedule during "blocked" or "sleep" time slots
7. Add stress-relief breaks between intense tasks

OUTPUT (JSON only):
{{
  "schedule": [
    {{
      "day": "Monday",
      "date": "2025-10-14",
      "total_work_hours": 5.5,
      "slots": [
        {{
          "time": "09:00-11:00",
          "task": "Task name",
          "priority": "High",
          "type": "work",
          "flexible": false,
          "deadline": "2025-10-16",
          "urgency": "urgent",
          "notes": "High priority - deadline in 2 days"
        }}
      ]
    }}
  ],
  "warnings": ["List any scheduling conflicts or deadline issues"],
  "suggestions": ["Optimization tips"],
  "workload_analysis": {{"Monday": "balanced", "Tuesday": "light"}},
  "stress_adaptations": ["Applied 5h daily limit for high stress"],
  "deadline_compliance": ["All 8 tasks scheduled before deadlines"]
}}

Return ONLY valid JSON, no markdown."""

        # Call Gemini
        response = scheduler_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.rfind('```')
            response_text = response_text[json_start:json_end].strip()
        
        schedule_data = json.loads(response_text)
        
        # Save schedule to database
        new_schedule = UserSchedule(
            user_id=user_id,
            schedule_data=json.dumps(schedule_data),
            week_start=week_start,
            stress_level=stress_score,
            mood=mood
        )
        db.add(new_schedule)
        
        # Save tasks
        new_tasks = TaskRecord(user_id=user_id, tasks_data=json.dumps(tasks))
        db.add(new_tasks)
        
        db.commit()
        
        print(f"✅ Schedule generated and saved for user: {user_id}")
        return jsonify({'status': 'success', 'schedule': schedule_data})
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return jsonify({'status': 'error', 'message': 'AI generated invalid response. Please try again.'}), 500
    except Exception as e:
        db.rollback()
        print(f"❌ Error generating schedule: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()

@flask_app.route('/api/scheduler/get-schedule', methods=['GET'])
def get_scheduler_schedule():
    """Get latest schedule"""
    user_id = get_current_user_id()
    
    db = SchedulerSession()
    try:
        latest_schedule = db.query(UserSchedule).filter_by(user_id=user_id).order_by(UserSchedule.created_at.desc()).first()
        
        if latest_schedule:
            schedule_data = json.loads(latest_schedule.schedule_data)
            return jsonify({
                'status': 'success',
                'schedule': schedule_data,
                'created_at': latest_schedule.created_at.isoformat()
            })
        return jsonify({'status': 'error', 'message': 'No schedule found'}), 404
    finally:
        db.close()

@flask_app.route('/api/scheduler/export-calendar', methods=['POST'])
def export_to_calendar():
    """Export schedule to iCal format for Google Calendar"""
    data = request.json
    schedule = data.get('schedule')
    
    if not schedule:
        return jsonify({'status': 'error', 'message': 'No schedule data provided'}), 400
    
    # Build iCal content
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MindSoothe Task Scheduler//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:MindSoothe Schedule",
        "X-WR-TIMEZONE:UTC",
        "X-WR-CALDESC:AI-optimized task schedule from MindSoothe"
    ]
    
    for day_schedule in schedule.get('schedule', []):
        date_str = day_schedule['date'].replace('-', '')
        
        for slot in day_schedule.get('slots', []):
            if slot.get('type') == 'work':  # Only export work tasks
                time_parts = slot['time'].split('-')
                start_time = time_parts[0].replace(':', '')
                end_time = time_parts[1].replace(':', '')
                
                # Build event
                event_lines = [
                    "BEGIN:VEVENT",
                    f"DTSTART:{date_str}T{start_time}00",
                    f"DTEND:{date_str}T{end_time}00",
                    f"SUMMARY:{slot['task']}",
                    f"DESCRIPTION:Priority: {slot.get('priority', 'Medium')}\\nType: {slot.get('type', 'work')}\\n{slot.get('notes', '')}",
                    "STATUS:CONFIRMED",
                    f"UID:{date_str}T{start_time}00-{slot['task'].replace(' ', '-')}@mindsoothe.app",
                    f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                    "END:VEVENT"
                ]
                ical_lines.extend(event_lines)
    
    ical_lines.append("END:VCALENDAR")
    ical_content = '\n'.join(ical_lines)
    
    filename = f'mindsoothe_schedule_{datetime.now().strftime("%Y%m%d")}.ics'
    
    return jsonify({
        'status': 'success',
        'ical_data': ical_content,
        'filename': filename
    })
# =============================================================================
# SHARED/COMMON ROUTES
# =============================================================================

@flask_app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Combined: Activity Recommender + Stress Estimator",
        "version": "3.0.0",
        "llm_enabled": flask_estimator.use_llm,
        "llm_provider": "Gemini 1.5 Flash" if flask_estimator.use_llm else "None",
        "database_connected": True,
        "timestamp": datetime.now().isoformat()
    })

@flask_app.route('/api/database-stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        stats = flask_estimator.db_manager.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/cleanup-database', methods=['POST'])
def cleanup_database():
    """Manual database cleanup"""
    try:
        flask_estimator.db_manager.auto_cleanup()
        stats = flask_estimator.db_manager.get_database_stats()
        return jsonify({
            "message": "Database cleanup completed",
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        "message": "Backend is working!",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "gemini_enabled": estimator.use_llm,
        "has_api_key": bool(os.getenv('GOOGLE_API_KEY'))
    })

@flask_app.route('/')
def serve_frontend():
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        print(f"❌ Error serving frontend: {e}")
        return "Error loading frontend", 500
    

@flask_app.route('/api/test-gemini', methods=['GET'])
def test_gemini():
    """Test if Gemini is working"""
    try:
        import google.generativeai as genai
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            return jsonify({"error": "No API key found in environment"}), 500
            
        genai.configure(api_key=api_key)
        # Use the model from .env
        model_name = os.getenv('GEMINI_MODEL', 'models/gemini-2.0-flash-001')
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello! Gemini is working!'")
        
        return jsonify({
            "success": True,
            "model_used": model_name,
            "gemini_response": response.text,
            "message": "Gemini API is working correctly!"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@flask_app.route('/api/debug/users', methods=['GET'],endpoint='debug_users_v2')
def debug_users():
    """Debug endpoint to see all registered users"""
    return jsonify({
        "total_users": len(users_db),
        "users": users_db
    })

@flask_app.route('/api/debug/session', methods=['GET'], endpoint='debug_session_v2')
def debug_session():
    """Debug endpoint to check session"""
    return jsonify({
        "session_data": dict(session),
        "user_id": session.get('user_id'),
        "username": session.get('username')
    })

@flask_app.route('/<path:path>')
def serve_static_files(path):
    try:
        return send_from_directory('frontend', path)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404

@flask_app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@flask_app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@flask_app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ==================== MOTIVATION AGENT ROUTES ====================

def generate_motivation_from_stress(stress_result, user_message=""):
    """Generate motivation based on stress analysis result"""
    # Create motivation request from stress result
    motivation_request = MotivationRequest(
        stress_level=stress_result["stress_score"],
        stress_category=stress_result["stress_level"],
        user_message=user_message,
        generate_audio=True
    )
    
    # Generate motivation
    motivation_response = motivational_agent.generate_motivation(motivation_request)
    
    return motivation_response

@flask_app.route('/api/generate-motivation', methods=['POST'])
def generate_motivation_api():
    """Generate motivation from stress level"""
    try:
        data = request.get_json()
        
        print(f"🎯 Generating motivation for stress level: {data.get('stress_level')}")
        
        motivation_request = MotivationRequest(
            stress_level=data.get('stress_level', 5.0),
            stress_category=data.get('stress_category', 'Medium'),
            user_message=data.get('user_message', ''),
            generate_audio=data.get('generate_audio', True)
        )
        
        response = motivational_agent.generate_motivation(motivation_request)
        
        result = {
            "success": response.success,
            "motivational_message": response.motivational_message,
            "audio_file_path": response.audio_file_path,
            "stress_level": data.get('stress_level'),
            "stress_category": data.get('stress_category')
        }
        
        # Play audio if generated and requested
        if response.audio_file_path and data.get('play_audio', True):
            motivational_agent.play_audio(response.audio_file_path)
        
        print("✅ Motivation generated successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error generating motivation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/play-audio', methods=['POST'])
def play_audio_api():
    """Play generated audio"""
    try:
        data = request.get_json()
        audio_path = data.get('audio_path')
        
        if not audio_path:
            return jsonify({"error": "No audio path provided"}), 400
        
        print(f"🔊 Playing audio: {audio_path}")
        
        success = motivational_agent.play_audio(audio_path)
        
        return jsonify({"success": success, "audio_played": audio_path})
        
    except Exception as e:
        print(f"❌ Error playing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/analyze-with-motivation', methods=['POST', 'OPTIONS'])
def enhanced_analysis_with_motivation():
    """Your existing analysis enhanced with motivation"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "preflight"})
        
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        print("🎯 Starting enhanced analysis with motivation...")
        
        # Get stress analysis (your existing code)
        stress_result = flask_estimator.enhanced_comprehensive_analysis(data, user_id)
        
        # Generate motivational message with audio
        user_message = data.get('user_message', '')
        motivation_result = generate_motivation_from_stress(stress_result, user_message)
        
        # Combine results
        combined_result = {
            **stress_result,
            "motivation": {
                "message": motivation_result.motivational_message,
                "audio_available": motivation_result.audio_file_path is not None,
                "audio_path": motivation_result.audio_file_path
            }
        }
        
        # Play audio automatically if generated
        if motivation_result.audio_file_path:
            print(f"🔊 Playing audio motivation: {motivation_result.audio_file_path}")
            motivational_agent.play_audio(motivation_result.audio_file_path)
        
        print(f"✅ Enhanced analysis complete with motivation for user: {user_id}")
        return jsonify(combined_result)
        
    except Exception as e:
        print(f"❌ Error in enhanced analysis with motivation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/analyze-mood-with-motivation', methods=['POST', 'OPTIONS'])
def analyze_mood_with_motivation():
    """Enhanced mood analysis with motivation"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "preflight"})
        
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        print("🎯 Mood analysis with motivation requested...")
        
        # Use the enhanced analysis with motivation
        return enhanced_analysis_with_motivation()
        
    except Exception as e:
        print(f"❌ Error in mood analysis with motivation: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== RUN APPLICATIONS ====================

def run_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=config.STRESS_ESTIMATOR_PORT)

def run_flask():
    print("🧠 MindSoothe Stress Detection System Starting...")
# =============================================================================
# START THE SERVER
# =============================================================================

if __name__ == '__main__':
    print("🚀 Starting Combined System...")
    print("=" * 60)
    print("📍 SENUTHI: Activity Recommender System")
    print("   - Web Routes: /onboard, /recommend, /users")
    print("   - API: /api/activity_recommender/*")
    print("")
    print("📍 WATHSALA: Stress Detection System")
    print("   - API: /api/analyze-mood, /api/register, /api/login")
    print("   - Features: Gemini AI Analysis, Charts, Statistics")
    print("")
    print("📍 MANUTHI: Task Scheduler - Port 5001")
    print("=" * 60)
    print("🗓️  Task Scheduler Features:")
    print("   ✅ Gemini-powered scheduling")
    print("   ✅ Stress-adaptive task placement")
    print("   ✅ Database-stored routines")
    print("   ✅ Dynamic schedule adjustments")
    print("")
    print("🌐 Running on: http://localhost:5001")
    print("=" * 60)
    print("")
    print("🤖 AI CAPABILITIES:")
    print(f"   ✅ Gemini Analysis: {flask_estimator.use_llm}")
    print("   🎵 Audio Motivation: Enabled")
    print("   💬 Personalized Messages: Gemini-powered")
    print("")
    print("🔐 AUTHENTICATION:")
    print("   ✅ User Registration & Login") 
    print("")
    print("📊 FEATURES:")
    print("   ✅ Comprehensive Stress Assessment")
    print("   ✅ Real-time Charts & Statistics")
    print("   ✅ Trend Analysis")
    print("   🎯 Audio Motivational Support")
    print("")
    print("🎵 MOTIVATION ENDPOINTS:")
    print("   POST /api/generate-motivation")
    print("   POST /api/play-audio")
    print("   POST /api/analyze-with-motivation")
    print("   POST /api/analyze-mood-with-motivation")
    print(f"   ✅ Gemini Analysis: {flask_estimator.use_llm}")
    print("")
    print("💾 Database: SQLite with user storage")
    print("=" * 60)
    
    flask_app.run(port=5001, debug=True, host='0.0.0.0')

if __name__ == '__main__':
    # You can choose which one to run, or run both in different processes
    run_flask()  # Running Flask version by default
    # run_fastapi()  # Uncomment to run FastAPI version instead
    flask_app.run(debug=True, host='0.0.0.0', port=5001)
