# init_db.py
from agents.utils.database import engine, SessionLocal, Base, DBActivity

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Sample activities with PROPER stress level assignments
sample_activities = [
    # HIGH STRESS ACTIVITIES (Quick, calming)
    DBActivity(
        name="5-Minute Breathing Exercise",
        description="A short guided box breathing exercise to calm your nervous system quickly.",
        recommended_stress_level="High",
        duration_minutes=5,
        category="mindfulness",
        keywords="quick, calm, breathing, anxiety, emergency"
    ),
    DBActivity(
        name="Quick Grounding Technique",
        description="5-4-3-2-1 sensory grounding exercise to reduce anxiety.",
        recommended_stress_level="High",
        duration_minutes=3,
        category="mindfulness",
        keywords="quick, anxiety, grounding, emergency"
    ),
    
    # MEDIUM STRESS ACTIVITIES (Balanced)
    DBActivity(
        name="10-Minute Guided Meditation",
        description="A beginner-friendly meditation session to focus the mind.",
        recommended_stress_level="Medium",
        duration_minutes=10,
        category="mindfulness",
        keywords="focus, mindfulness, indoor, balanced"
    ),
    DBActivity(
        name="Quick Journaling",
        description="Write down your thoughts and feelings for 5-10 minutes.",
        recommended_stress_level="Medium",
        duration_minutes=8,
        category="creative",
        keywords="writing, reflection, processing"
    ),
    
    # LOW STRESS ACTIVITIES (Longer, preventive)
    DBActivity(
        name="15-Minute Evening Walk",
        description="A brisk walk outdoors to get fresh air and change your environment.",
        recommended_stress_level="Low",
        duration_minutes=15,
        category="physical",
        keywords="outdoor, exercise, nature, preventive"
    ),
    DBActivity(
        name="Stretch Break",
        description="Full body stretching exercises to release physical tension.",
        recommended_stress_level="Low",
        duration_minutes=12,
        category="physical",
        keywords="exercise, indoor, relaxation"
    ),
    DBActivity(
        name="Mindful Tea Break",
        description="Prepare and enjoy a warm drink mindfully.",
        recommended_stress_level="Low",
        duration_minutes=15,
        category="mindfulness",
        keywords="relaxing, slow, enjoyment"
    )
]

# Clear existing activities and add new ones
db.query(DBActivity).delete()
for activity in sample_activities:
    db.add(activity)

db.commit()
db.close()
print("Database populated with PROPERLY categorized activities!")