#manual testing script:
import requests
import json
import time

def test_stress_estimator():
    """Test the stress estimator API with various inputs"""
    url = "http://localhost:5001/estimate"
    
    # Test various types of user inputs
    test_inputs = [
        "I'm feeling great today! Everything is going well.",
        "I have a lot of work to do but I'm managing.",
        "I'm so overwhelmed with deadlines and can't cope with the pressure.",
        "Just a normal day, nothing special.",
        "Everything is too much right now, I need a break.",
        "I'm worried about my exam next week.",
        "Feeling good after my workout.",
        "The presentation didn't go well, I'm anxious about the feedback.",
        "Ugh, today sucks.",
        "Can't sleep, too much on my mind.",
        "My boss is being unreasonable with these deadlines.",
        "I feel like I'm drowning in work.",
        "Had a relaxing day off, feeling refreshed.",
        "Not sure how I'll get everything done on time.",
        "Everything is going according to plan, feeling confident."
    ]
    
    print("Testing Stress Estimator Agent API with Various Inputs")
    print("=" * 60)
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: '{user_input}'")
        
        data = {
            "text": user_input,
            "user_id": f"test_user_{i % 3}"  # Cycle through 3 test users
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Stress Level: {result['stress_level']}")
                print(f"   Score: {result['stress_score']}/10")
                print(f"   Keywords: {result['keywords']}")
                print(f"   Explanation: {result['explanation']}")
                if 'trend' in result:
                    print(f"   Trend: {result['trend']}")
                        
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Make sure the server is running on port 5001.")
            break
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Brief pause between requests
        time.sleep(0.5)

def test_health_check():
    """Test the health check endpoint"""
    url = "http://localhost:5001/health"
    
    print("\n" + "=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=5)
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Service: {result['service']}")
        print(f"Description: {result['description']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def test_history():
    """Test the history endpoint"""
    url = "http://localhost:5001/history/test_user_1"
    
    print("\n" + "=" * 60)
    print("Testing History Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=5)
        result = response.json()
        print(f"User ID: {result['user_id']}")
        print(f"History entries: {result['count']}")
        if result['history']:
            print("Recent entries:")
            for entry in result['history'][-3:]:  # Show last 3 entries
                print(f"  {entry['timestamp']}: {entry['score']} ({entry['level']})")
    except Exception as e:
        print(f"❌ History check failed: {e}")

if __name__ == '__main__':
    # Run the tests
    test_stress_estimator()
    test_health_check()
    test_history()