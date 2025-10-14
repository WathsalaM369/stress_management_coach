#Vinushas
import requests
import json

def test_stress_estimator():
    """Test the stress estimator endpoint"""
    url = "http://localhost:8001/estimate-stress"
    data = {"text": "I'm feeling very overwhelmed with work deadlines and exams"}
    
    try:
        response = requests.post(url, json=data)
        print("✅ Stress Estimator Response:")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except Exception as e:
        print(f"❌ Error testing stress estimator: {e}")
        return None

def test_motivational_agent():
    """Test the motivational agent endpoint"""
    url = "http://localhost:8002/generate-motivation"
    data = {
        "stress_level": 7.5,
        "recommended_activity": "deep breathing exercises",
        "user_message": "I'm completely overwhelmed with work deadlines"
    }
    
    try:
        response = requests.post(url, json=data)
        print("✅ Motivational Agent Response:")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except Exception as e:
        print(f"❌ Error testing motivational agent: {e}")
        return None

if __name__ == "__main__":
    print("🧠 Testing Stress Management Coach System...")
    print("=" * 50)
    
    stress_result = test_stress_estimator()
    print("=" * 50)
    
    if stress_result and 'stress_level' in stress_result:
        # Use the actual stress level from the first test
        data = {
            "stress_level": stress_result['stress_level'],
            "recommended_activity": "deep breathing exercises",
            "user_message": "I'm completely overwhelmed with work deadlines"
        }
        
        motivation_result = test_motivational_agent()
    else:
        # Fallback test
        motivation_result = test_motivational_agent()
    
    print("=" * 50)
    print("🎉 System test completed!")