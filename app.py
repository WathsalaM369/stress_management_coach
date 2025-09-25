from flask import Flask, request, jsonify, render_template
from agents.stress_estimator import StressEstimator
from datetime import datetime, timedelta
import json
from agents.task_scheduler import AdaptiveTaskScheduler, Task, TaskPriority, MoodState, TimeBlock, BreakActivity
from config import config

app = Flask(__name__)
agent = StressEstimator()
task_scheduler = AdaptiveTaskScheduler()

# Serve the main page
@app.route('/')
def index():
    return render_template('task_scheduler.html')

# API Routes - UPDATED TO MATCH YOUR JAVASCRIPT
@app.route('/api/schedule', methods=['POST'])  # Changed to match your JS
def api_schedule():
    data = request.get_json()
    
    # Extract parameters from your JavaScript request
    user_text = data.get('user_text', '')
    user_stress_level = data.get('user_stress_level', 5)
    tasks = data.get('tasks', [])
    mood = data.get('mood', 'focused')
    available_blocks = data.get('available_blocks', [])
    
    # Use text-based stress estimation if text provided
    if user_text:
        try:
            stress_result = agent.estimate_stress_level(user_text)
            stress_level = stress_result.get('stress_level', 5)
        except:
            stress_level = user_stress_level
    else:
        stress_level = user_stress_level
    
    # Validate required fields
    if not tasks or not available_blocks:
        return jsonify({'error': 'Tasks and available_blocks are required'}), 400
    
    try:
        # Process the scheduling request using your existing method
        result = task_scheduler.analyze_and_schedule(
            stress_data={'stress_level': stress_level, 'reasons': []},
            tasks=tasks,
            mood=mood,
            available_blocks=available_blocks
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Scheduling failed: {str(e)}'}), 500

# Keep your existing endpoints for compatibility
@app.route('/estimate_stress', methods=['POST'])
def estimate_stress():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = agent.estimate_stress_level(text)
    return jsonify(result)

@app.route('/schedule_tasks', methods=['POST'])
def schedule_tasks():
    data = request.get_json()
    stress_level = data.get('stress_level', 5)
    tasks_data = data.get('tasks', [])
    mood_state = data.get('mood_state', 'focused')
    time_blocks = data.get('time_blocks', [])
    break_activities = data.get('break_activities', [])
    
    if not tasks_data or not time_blocks:
        return jsonify({'error': 'Tasks and time_blocks are required'}), 400
    
    try:
        mood_enum = MoodState[mood_state.upper()]
        
        result = task_scheduler.process_inputs(
            stress_level=stress_level,
            tasks=tasks_data,
            mood_state=mood_enum,
            time_blocks=time_blocks,
            break_activities=break_activities
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Scheduling failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)