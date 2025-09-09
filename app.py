from flask import Flask, request, jsonify
from agents.stress_estimator import StressEstimatorAgent

from datetime import datetime, timedelta
import json
from agents.task_scheduler import AdaptiveTaskScheduler, Task, TaskPriority, MoodState, TimeBlock, BreakActivity
from config import config

app = Flask(__name__)
agent = StressEstimatorAgent()
task_scheduler = AdaptiveTaskScheduler()

@app.route('/estimate_stress', methods=['POST'])
def estimate_stress():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = agent.estimate_stress_level(text)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route('/schedule_tasks', methods=['POST'])
def schedule_tasks():
    data = request.get_json()
    
    # Extract parameters
    stress_level = data.get('stress_level', 5)
    tasks_data = data.get('tasks', [])
    mood_state = data.get('mood_state', 'focused')
    time_blocks = data.get('time_blocks', [])
    break_activities = data.get('break_activities', [])
    
    # Validate required fields
    if not tasks_data or not time_blocks:
        return jsonify({'error': 'Tasks and time_blocks are required'}), 400
    
    try:
        # Convert mood state string to enum
        mood_enum = MoodState[mood_state.upper()]
        
        # Process the scheduling request
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