#Vinushas
import requests
import json

# Test Stress Estimator
def test_stress_estimator():
    url = "http://localhost:8001/estimate-stress"
    params = {"text": "I'm feeling very overwhelmed with work deadlines"}
    
    response = requests.post(url, params=params)
    print("Stress Estimator Response:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

# Test Motivational Agent
def test_motivational_agent():
    url = "http://localhost:8002/generate-motivation"
    data = {
        "stress_level": 7.5,
        "recommended_activity": "deep breathing exercises",
        "user_message": "I'm completely overwhelmed with work deadlines"
    }
    
    response = requests.post(url, json=data)
    print("\nMotivational Agent Response:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

if __name__ == "__main__":
    print("Testing APIs...")
    test_stress_estimator()
    test_motivational_agent()