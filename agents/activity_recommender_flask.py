# agents/activity_recommender_flask.py
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from agents.utils.database import get_db, DBActivity, DBUser, DBCustomActivity

activity_bp = Blueprint('activity_recommender', __name__)

def rank_activities(db_activities, custom_activities, stress_level, context, user_preferences):
    # Combine predefined and custom activities
    all_activities = []
    
    # Add predefined activities
    for activity in db_activities:
        all_activities.append({
            'id': activity.id,
            'name': activity.name,
            'description': activity.description,
            'duration_minutes': activity.duration_minutes,
            'recommended_stress_level': activity.recommended_stress_level,
            'category': activity.category,
            'type': 'predefined'
        })
    
    # Add custom activities
    for activity in custom_activities:
        all_activities.append({
            'id': activity['id'] + 1000,  # Offset to avoid ID conflicts
            'name': activity['name'],
            'description': activity['description'],
            'duration_minutes': activity['duration_minutes'],
            'recommended_stress_level': activity.get('recommended_stress_level', 'Medium'),
            'category': activity.get('category', 'custom'),
            'type': 'custom'
        })
    
    # Rank all activities
    ranked = []
    for activity in all_activities:
        score = 0

        # 1. Match stress level (Most important factor)
        if activity['recommended_stress_level'] == stress_level:
            score += 100

        # 2. Filter by available time
        if context and "available_minutes" in context:
            available_time = context["available_minutes"]
            if activity['duration_minutes'] <= available_time:
                score += 5
            else:
                score -= 100

        # 3. Check User Preferences - HIGH priority to liked activities
        if activity['name'] in user_preferences.get("likes", []):
            score += 50  # Very high bonus for liked activities
        
        # 4. Extra bonus for CUSTOM activities that user added
        if activity['type'] == 'custom':
            score += 30  # Bonus for custom activities
        
        # 5. Penalty for disliked activities
        if activity['name'] in user_preferences.get("dislikes", []):
            score -= 100

        ranked.append((score, activity))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [activity for (score, activity) in ranked if score > 0]

@activity_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Check if data is None (empty request)
        if data is None:
            return jsonify({'error': 'No JSON data received'}), 400
            
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
        
    except Exception as e:
        # Log the actual error
        print(f"ERROR in create_user: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    

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
    try:
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
        
    except Exception as e:
        print(f"ERROR in update_preferences: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
    

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
    
    # Get all predefined activities
    db_activities = db.query(DBActivity).all()
    if not db_activities:
        return jsonify({'error': 'No activities found'}), 404
    
    # Get custom activities for this user
    custom_activities = []
    try:
        db_custom_activities = db.query(DBCustomActivity).filter(
            DBCustomActivity.user_id == user_id
        ).all()
        
        for activity in db_custom_activities:
            custom_activities.append({
                'id': activity.id,
                'name': activity.name,
                'description': activity.description,
                'duration_minutes': activity.duration_minutes,
                'category': activity.category,
                'recommended_stress_level': 'Medium'
            })
    except Exception as e:
        print(f"Error fetching custom activities: {e}")
        # Continue without custom activities if there's an error
    
    # Set default available time if not provided
    if not context:
        context = {}
    if 'available_minutes' not in context:
        context['available_minutes'] = user_preferences.get('default_available_minutes', 10)
    
    # Rank activities (both predefined and custom)
    ranked_activities = rank_activities(db_activities, custom_activities, stress_level, context, user_preferences)
    
    # Format response
    recommendations = [
        {
            'id': activity['id'],
            'name': activity['name'],
            'description': activity['description'],
            'duration_minutes': activity['duration_minutes'],
            'category': activity['category'],
            'type': activity['type']  # Add type to distinguish custom vs predefined
        }
        for activity in ranked_activities
    ]
    
    return jsonify({
        'recommendations': recommendations,
        'total_activities': len(ranked_activities),
        'custom_activities_count': len(custom_activities)
    })

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

@activity_bp.route('/custom_activities', methods=['POST'])
def create_custom_activity():
    """Create a custom activity for a user"""
    data = request.get_json()
    db = next(get_db())
    
    try:
        # Check if user exists
        db_user = db.query(DBUser).filter(DBUser.id == data['user_id']).first()
        if not db_user:
            return jsonify({'error': 'User not found'}), 404
        
        custom_activity = DBCustomActivity(
            user_id=data['user_id'],
            name=data['name'],
            description=data.get('description', f"Your custom activity: {data['name']}"),
            duration_minutes=data.get('duration_minutes', 10),
            category=data.get('category', 'custom')
        )
        
        db.add(custom_activity)
        db.commit()
        db.refresh(custom_activity)
        
        return jsonify({
            'id': custom_activity.id,
            'name': custom_activity.name,
            'description': custom_activity.description,
            'duration_minutes': custom_activity.duration_minutes,
            'category': custom_activity.category
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400

@activity_bp.route('/users/<int:user_id>/custom_activities', methods=['GET'])
def get_user_custom_activities(user_id):
    """Get custom activities for a specific user"""
    db = next(get_db())
    
    # Check if user exists
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        return jsonify({'error': 'User not found'}), 404
    
    custom_activities = db.query(DBCustomActivity).filter(
        DBCustomActivity.user_id == user_id
    ).all()
    
    activities_list = []
    for activity in custom_activities:
        activities_list.append({
            'id': activity.id,
            'name': activity.name,
            'description': activity.description,
            'duration_minutes': activity.duration_minutes,
            'category': activity.category,
            'recommended_stress_level': 'Medium'
        })
    
    return jsonify(activities_list)

@activity_bp.route('/activities/all', methods=['GET'])
def get_all_activities():
    """Get all activities (both predefined and custom) for debugging"""
    db = next(get_db())
    
    # Get predefined activities
    predefined = db.query(DBActivity).all()
    predefined_list = []
    for activity in predefined:
        predefined_list.append({
            'id': activity.id,
            'name': activity.name,
            'type': 'predefined',
            'stress_level': activity.recommended_stress_level
        })
    
    # Get custom activities
    custom = db.query(DBCustomActivity).all()
    custom_list = []
    for activity in custom:
        custom_list.append({
            'id': activity.id,
            'name': activity.name,
            'type': 'custom',
            'user_id': activity.user_id
        })
    
    return jsonify({
        'predefined_activities': predefined_list,
        'custom_activities': custom_list,
        'total_predefined': len(predefined_list),
        'total_custom': len(custom_list)
    })