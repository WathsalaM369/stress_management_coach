from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, session
from flask_cors import CORS
from agents.activity_recommender_flask import activity_bp
from agents.stress_estimator import StressEstimator
from datetime import datetime, timedelta
import requests
import json
import os
import secrets
import hashlib

app = Flask(__name__)
app.secret_key = 'mindsoothe-secret-key-2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Enhanced CORS with Gemini support
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://localhost:5001'])

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
            return {"stress_level": "Medium", "score": 0.6, "message": "You appear to have moderate stress"}
        else:
            return {"stress_level": "Low", "score": 0.3, "message": "You seem to be doing well"}

agent = MockStressEstimator()

# Register activity recommender blueprint
app.register_blueprint(activity_bp, url_prefix='/api/activity_recommender')

# =============================================================================
# WATHSALA'S STRESS ESTIMATOR SETUP
# =============================================================================

# Initialize stress estimator with Gemini
use_llm = os.getenv('USE_LLM', 'true').lower() == 'true'
print(f"🔧 LLM Mode: {use_llm}")

if use_llm:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key or api_key == 'your_actual_google_api_key_here':
        print("❌ No valid Google API key found. Disabling LLM.")
        use_llm = False

estimator = StressEstimator(use_database=True, use_llm=use_llm)

# In-memory user store (in production, use a real database)
users_db = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

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

@app.route('/')
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

@app.route('/stress-assessment')
def stress_assessment():
    """Wathsala's stress assessment interface"""
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        return jsonify({"error": "Stress assessment frontend not found"}), 404

@app.route('/activity-recommender')
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

@app.route('/onboard', methods=['GET', 'POST'])
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

@app.route('/recommend-success/<int:user_id>')
def recommend_success(user_id):
    return render_template('activity_rec_result.html', user_id=user_id, message="Account created successfully!")

@app.route('/recommend', methods=['GET', 'POST'])
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

@app.route('/users')
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

@app.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        response = requests.get('http://localhost:5001/api/activity_recommender/users')
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify([])
    except:
        return jsonify([])

@app.route('/api/estimate_stress', methods=['POST'])
def estimate_stress():
    data = request.get_json()
    text = data.get('text', '')
    result = agent.estimate_stress_level(text)
    return jsonify(result)

@app.route('/api/get-activity-recommendations', methods=['POST', 'OPTIONS'])
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

@app.route('/api/register', methods=['POST'])
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

@app.route('/api/login', methods=['POST'])
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

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username')
    session.clear()
    print(f"✅ User logged out: {username}")
    return jsonify({"message": "Logout successful"})

@app.route('/api/current-user', methods=['GET'])
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

@app.route('/api/analyze-mood', methods=['POST', 'OPTIONS'])
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
        result = estimator.enhanced_comprehensive_analysis(data, user_id)
        
        # Get updated trend after analysis
        trend = get_user_trend_fixed(user_id)
        result['trend'] = trend
        
        print(f"✅ Analysis complete: {result['stress_level']} ({result['stress_score']}/10)")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Error in analyze_mood: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-comprehensive', methods=['POST', 'OPTIONS'])
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
        result = estimator.enhanced_comprehensive_analysis(analysis_data, user_id)
        
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
        history = estimator.db_manager.get_user_history(user_id, 100)
        
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

@app.route('/api/history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    try:
        print(f"📊 Getting history for user: {user_id}")
        history = estimator.db_manager.get_user_history(user_id)
        
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

@app.route('/api/chart-data/<user_id>', methods=['GET'])
def get_chart_data(user_id):
    try:
        print(f"📈 Getting chart data for user: {user_id}")
        history = estimator.db_manager.get_user_history(user_id, 30)
        
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

@app.route('/api/stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    try:
        print(f"📊 Getting stats for user: {user_id}")
        history = estimator.db_manager.get_user_history(user_id, 100)
        
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

# =============================================================================
# SHARED/COMMON ROUTES
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Combined: Activity Recommender + Stress Estimator",
        "version": "3.0.0",
        "llm_enabled": estimator.use_llm,
        "llm_provider": "Gemini 1.5 Flash" if estimator.use_llm else "None",
        "database_connected": True,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/database-stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        stats = estimator.db_manager.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cleanup-database', methods=['POST'])
def cleanup_database():
    """Manual database cleanup"""
    try:
        estimator.db_manager.auto_cleanup()
        stats = estimator.db_manager.get_database_stats()
        return jsonify({
            "message": "Database cleanup completed",
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        "message": "Backend is working!",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "gemini_enabled": estimator.use_llm,
        "has_api_key": bool(os.getenv('GOOGLE_API_KEY'))
    })

@app.route('/api/test-gemini', methods=['GET'])
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

@app.route('/api/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to see all registered users"""
    return jsonify({
        "total_users": len(users_db),
        "users": users_db
    })

@app.route('/api/debug/session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session"""
    return jsonify({
        "session_data": dict(session),
        "user_id": session.get('user_id'),
        "username": session.get('username')
    })

@app.route('/<path:path>')
def serve_static_files(path):
    try:
        return send_from_directory('frontend', path)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

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
    print("🌐 Running on: http://localhost:5001")
    print("=" * 60)
    print("")
    print("🤖 AI CAPABILITIES:")
    print(f"   ✅ Gemini Analysis: {estimator.use_llm}")
    print("")
    print("💾 Database: SQLite with user storage")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
