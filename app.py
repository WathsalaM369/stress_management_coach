from flask import Flask, request, jsonify, render_template, redirect, url_for
from agents.activity_recommender_flask import activity_bp
import requests
import json



app = Flask(__name__)

# Simple mock for stress estimation
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

# Register  activity recommender blueprint
app.register_blueprint(activity_bp, url_prefix='/api/activity_recommender')

# Web Routes
@app.route('/')
def index():
    return render_template('activity_rec_index.html')  # Updated filename

@app.route('/onboard', methods=['GET', 'POST'])
def onboard():
    if request.method == 'POST':
        username = request.form.get('username')
        likes = request.form.getlist('likes')
        default_time = int(request.form.get('default_time', 10))
        
        print(f"DEBUG: Creating user '{username}' with likes: {likes}")  # Debug line
        
        try:
            # Create user via API
            response = requests.post(
                'http://localhost:5000/api/activity_recommender/users',
                json={'username': username},
                timeout=5
            )
            
            print(f"DEBUG: Response status: {response.status_code}")  # Debug line
            print(f"DEBUG: Response content: {response.text}")  # Debug line
            
            if response.status_code == 201:
                user_data = response.json()
                user_id = user_data['id']
                
                # Set preferences
                pref_response = requests.put(
                    f'http://localhost:5000/api/activity_recommender/users/{user_id}/preferences',
                    json={
                        'likes': likes, 
                        'default_available_minutes': default_time
                    },
                    timeout=5
                )
                
                print(f"DEBUG: Preferences response: {pref_response.status_code}")  # Debug line
                
                if pref_response.status_code == 200:
                    return redirect(url_for('recommend_success', user_id=user_id))
                else:
                    return render_template('user_onboard.html', error="Error setting preferences")
            else:
                # Try to get error message from response
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
    return render_template('activity_rec_result.html', user_id=user_id, message="Account created successfully!")  # Updated filename

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
        
        # First, get user ID from username by checking each user
        try:
            # Get all users
            response = requests.get('http://localhost:5000/api/activity_recommender/users')
            
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
                    'http://localhost:5000/api/activity_recommender/recommend',
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

# Add a new endpoint to get all users (for the form)
@app.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        response = requests.get('http://localhost:5000/api/activity_recommender/users')
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify([])
    except:
        return jsonify([])
    
# API Routes (keep these for external access)
@app.route('/api/estimate_stress', methods=['POST'])
def estimate_stress():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = agent.estimate_stress_level(text)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/users')
def users_list():
    """Display all registered users"""
    try:
        # Get all users from the API
        response = requests.get('http://localhost:5000/api/activity_recommender/users')
        if response.status_code == 200:
            users = response.json()
            return render_template('users_list.html', users=users)
        else:
            return render_template('users_list.html', users=[], error="Cannot fetch users")
    except requests.exceptions.RequestException as e:
        return render_template('users_list.html', users=[], error=f"Connection error: {str(e)}")