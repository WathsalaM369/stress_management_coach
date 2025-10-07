#Vinushas
#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import threading
from config import Config

def run_stress_estimator():
    """Run the stress estimator agent"""
    print("Starting Stress Estimator Agent...")
    os.system(f"python -m uvicorn app:app --host 0.0.0.0 --port {config.STRESS_ESTIMATOR_PORT} --reload")

def run_motivational_agent():
    """Run the motivational agent"""
    print("Starting Motivational Agent...")
    
    # Create a simple FastAPI app for the motivational agent
    motivational_app_code = """
from fastapi import FastAPI
from agents.motivational_agent import motivational_agent, MotivationRequest
from pydantic import BaseModel
import uvicorn
from config import Config

app = FastAPI(title="Motivational Agent API")
config = Config()

@app.post("/generate-motivation")
async def generate_motivation(request: MotivationRequest):
    return motivational_agent.generate_motivation(request).dict()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "motivational_agent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.MOTIVATIONAL_AGENT_PORT)
"""
    
    # Write the temporary app file
    with open("motivational_app.py", "w") as f:
        f.write(motivational_app_code)
    
    # Run the motivational agent
    os.system(f"python -m uvicorn motivational_app:app --host 0.0.0.0 --port {config.MOTIVATIONAL_AGENT_PORT} --reload")

def test_system():
    """Test the system components"""
    print("Testing system components...")
    
    # Test LLM client
    try:
        from utils.llm_client import llm_client
        test_response = llm_client.generate_text("Say 'Hello, World!'")
        if test_response:
            print("✓ LLM Client working")
        else:
            print("✗ LLM Client failed")
    except Exception as e:
        print(f"✗ LLM Client error: {e}")
    
    # Test motivational agent
    try:
        from agents.motivational_agent import MotivationalAgent, MotivationRequest
        agent = MotivationalAgent()
        request = MotivationRequest(
            stress_level=7.5,
            recommended_activity="deep breathing",
            user_message="I'm feeling overwhelmed"
        )
        response = agent.generate_motivation(request)
        if response.success:
            print("✓ Motivational Agent working")
            print(f"Sample message: {response.motivational_message[:100]}...")
        else:
            print("✗ Motivational Agent failed")
    except Exception as e:
        print(f"✗ Motivational Agent error: {e}")

if __name__ == "__main__":
    config = Config()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_system()
    else:
        print("Starting Stress Management Coach System...")
        print("Press Ctrl+C to stop all services")
        
        # Start services in separate threads
        try:
            # For simplicity, we'll run them sequentially for now
            # In production, you'd use a process manager like PM2 or Docker Compose
            
            print("1. Starting Stress Estimator Agent on port 8001...")
            stress_thread = threading.Thread(target=run_stress_estimator)
            stress_thread.daemon = True
            stress_thread.start()
            
            time.sleep(3)  # Wait a bit for the first service to start
            
            print("2. Starting Motivational Agent on port 8002...")
            motivation_thread = threading.Thread(target=run_motivational_agent)
            motivation_thread.daemon = True
            motivation_thread.start()
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down services...")
            sys.exit(0)