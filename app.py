from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from agents.stress_estimator import StressEstimator
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import json

app = Flask(__name__)
app.secret_key = 'mindsoothe-secret-key-2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Enhanced CORS with Gemini support
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://localhost:5001'])

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

def get_current_user_id():
    """Get current user ID or create temporary one"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = f"temp_{secrets.token_hex(8)}"
        session['user_id'] = user_id
        session['username'] = 'Guest'
        print(f"🆕 Created temporary user: {user_id}")
    return user_id

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
        
        # Debug: Print what we're getting from database
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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "AI Stress Estimator",
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
        "status": "success"
    })

@app.route('/')
def serve_frontend():
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        return jsonify({"error": "Frontend not found"}), 404

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

if __name__ == '__main__':
    print("🧠 MindSoothe Stress Detection System Starting...")
    print("=" * 60)
    print("📍 Backend API: http://localhost:5001")
    print("🎨 Frontend: http://localhost:5001")
    print("")
    print("🤖 AI CAPABILITIES:")
    print(f"   ✅ Gemini Analysis: {estimator.use_llm}")
    print("")
    print("🔐 AUTHENTICATION:")
    print("   ✅ User Registration & Login") 
    print("")
    print("📊 FEATURES:")
    print("   ✅ Comprehensive Stress Assessment")
    print("   ✅ Real-time Charts & Statistics")
    print("   ✅ Trend Analysis")
    print("")
    print("💾 Database: SQLite with user storage")
    print("=" * 60)
    
    app.run(port=5001, debug=True, host='0.0.0.0')