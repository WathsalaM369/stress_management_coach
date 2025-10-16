# agents/activity_recommender.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from agents.utils.database import get_db, DBActivity, DBUser
from agents.utils.models import (
    RecommendationRequest, RecommendationResponse, 
    ActivityRecommendation, UserCreate, 
    UserPreferencesUpdate, UserResponse
)

router = APIRouter()

# Onboarding Endpoints
@router.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = DBUser(username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{user_id}/preferences", response_model=UserResponse)
def update_preferences(user_id: int, preferences: UserPreferencesUpdate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_prefs = db_user.preferences
    
    if preferences.likes is not None:
        current_prefs["likes"] = preferences.likes
    if preferences.dislikes is not None:
        current_prefs["dislikes"] = preferences.dislikes
    if preferences.default_available_minutes is not None:
        current_prefs["default_available_minutes"] = preferences.default_available_minutes
    
    db_user.preferences = current_prefs
    db.commit()
    db.refresh(db_user)
    return db_user

# Recommendation Endpoint
def rank_activities(db_activities, request, user_preferences):
    ranked = []
    for activity in db_activities:
        score = 0

        # Match stress level
        if activity.recommended_stress_level == request.stress_level:
            score += 10

        # Filter by available time
        if request.context and "available_minutes" in request.context:
            available_time = request.context["available_minutes"]
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

@router.post("/recommend", response_model=RecommendationResponse)
def get_recommendations(request: RecommendationRequest, db: Session = Depends(get_db)):
    # Get user preferences
    db_user = db.query(DBUser).filter(DBUser.id == request.user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found. Please complete onboarding.")
    
    user_preferences = db_user.preferences

    # Get all activities
    db_activities = db.query(DBActivity).all()
    if not db_activities:
        raise HTTPException(status_code=404, detail="No activities found in database.")

    # Set default available time if not provided
    if request.context is None:
        request.context = {}
    request.context.setdefault("available_minutes", user_preferences.get("default_available_minutes", 10))

    # Rank activities
    ranked_activities = rank_activities(db_activities, request, user_preferences)

    # Format response
    response_recommendations = [
        ActivityRecommendation(
            id=activity.id,
            name=activity.name,
            description=activity.description,
            duration_minutes=activity.duration_minutes
        )
        for activity in ranked_activities
    ]
    return RecommendationResponse(recommendations=response_recommendations)