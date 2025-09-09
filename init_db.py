# init_db.py
from agents.utils.database import engine, SessionLocal, Base, DBActivity

# Create all tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Sample activities data
sample_activities = [
    DBActivity(
        name="5-Minute Breathing Exercise",
        description="A short guided box breathing exercise to calm your nervous system.",
        recommended_stress_level="High",
        duration_minutes=5,
        category="mindfulness",
        keywords="quick, calm, breathing, anxiety"
    ),
    DBActivity(
        name="10-Minute Guided Meditation",
        description="A beginner-friendly meditation session to focus the mind.",
        recommended_stress_level="Medium",
        duration_minutes=10,
        category="mindfulness",
        keywords="focus, mindfulness, indoor"
    ),
    DBActivity(
        name="15-Minute Evening Walk",
        description="A brisk walk outdoors to get fresh air and change your environment.",
        recommended_stress_level="Low",
        duration_minutes=15,
        category="physical",
        keywords="outdoor, exercise, nature"
    ),
    DBActivity(
        name="Quick Journaling",
        description="Write down your thoughts and feelings for 5 minutes.",
        recommended_stress_level="Medium",
        duration_minutes=5,
        category="creative",
        keywords="writing, reflection, indoor"
    ),
    DBActivity(
        name="Stretch Break",
        description="Simple stretching exercises to release physical tension.",
        recommended_stress_level="Low",
        duration_minutes=7,
        category="physical",
        keywords="quick, exercise, indoor"
    )
]

# Add activities to database
for activity in sample_activities:
    db.add(activity)

db.commit()
db.close()
print("✅ Database populated with sample activities!")