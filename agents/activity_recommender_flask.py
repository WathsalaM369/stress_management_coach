# agents/activity_recommender_flask.py
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from agents.utils.database import get_db, DBActivity, DBUser

activity_bp = Blueprint('activity_recommender', __name__)

def rank_activities(db_activities, stress_level, context, user_preferences):
    ranked = []
    for activity in db_activities:
        score = 0

        # Match stress level
        if activity.recommended_stress_level == stress_level:
            score += 10

        # Filter by available time
        if context and "available_minutes" in context:
            available_time = context["available_minutes"]
            if activity.duration_minutes <= available_time:
                score += 5
            else:
                score -= 100

        # Check User Preferences
        if activity.name in user_preferences.get("likes", []):
            score += 20
        if activity.name in user_preferences.get("dislikes", []):
            score -= 100

        ranked.append((score, activity))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [activity for (score, activity) in ranked if score > 0]

@activity_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    db = next(get_db())
    db_user = db.query(DBUser).filter(DBUser.username == username).first()
    if db_user:
        return jsonify({'error': 'Username already registered'}), 400
    
    new_user = DBUser(username=username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return jsonify({
        'id': new_user.id,
        'username': new_user.username,
        'preferences': new_user.preferences
    }), 201

@activity_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db = next(get_db())
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': db_user.id,
        'username': db_user.username,
        'preferences': db_user.preferences
    })

@activity_bp.route('/users/<int:user_id>/preferences', methods=['PUT'])
def update_preferences(user_id):
    data = request.get_json()
    db = next(get_db())
    
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        return jsonify({'error': 'User not found'}), 404
    
    current_prefs = db_user.preferences
    
    if 'likes' in data:
        current_prefs["likes"] = data['likes']
    if 'dislikes' in data:
        current_prefs["dislikes"] = data['dislikes']
    if 'default_available_minutes' in data:
        current_prefs["default_available_minutes"] = data['default_available_minutes']
    
    db_user.preferences = current_prefs
    db.commit()
    
    return jsonify({
        'id': db_user.id,
        'username': db_user.username,
        'preferences': db_user.preferences
    })

@activity_bp.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    stress_level = data.get('stress_level')
    user_id = data.get('user_id')
    context = data.get('context', {})
    
    if not stress_level or not user_id:
        return jsonify({'error': 'stress_level and user_id are required'}), 400
    
    db = next(get_db())
    
    # Get user preferences
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        return jsonify({'error': 'User not found'}), 404
    
    user_preferences = db_user.preferences
    
    # Get all activities
    db_activities = db.query(DBActivity).all()
    if not db_activities:
        return jsonify({'error': 'No activities found'}), 404
    
    # Set default available time if not provided
    if not context:
        context = {}
    if 'available_minutes' not in context:
        context['available_minutes'] = user_preferences.get('default_available_minutes', 10)
    
    # Rank activities
    ranked_activities = rank_activities(db_activities, stress_level, context, user_preferences)
    
    # Format response
    recommendations = [
        {
            'id': activity.id,
            'name': activity.name,
            'description': activity.description,
            'duration_minutes': activity.duration_minutes
        }
        for activity in ranked_activities
    ]
    
    return jsonify({'recommendations': recommendations})

@activity_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get list of all registered users"""
    try:
        db = next(get_db())
        users = db.query(DBUser).all()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'username': user.username,
                'preferences': user.preferences
            })
        
        return jsonify(users_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500