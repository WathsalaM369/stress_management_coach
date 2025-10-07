##Vinushas
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from agents.stress_estimator import stress_estimator
from agents.motivational_agent import motivational_agent, MotivationRequest
from config import Config

app = FastAPI(title="Stress Management Coach API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config()

# Include stress estimator routes
@app.post("/estimate-stress")
async def estimate_stress_endpoint(text: str):
    try:
        result = stress_estimator.estimate_stress_level(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add motivational agent endpoint
@app.post("/generate-motivation")
async def generate_motivation_endpoint(request: MotivationRequest):
    try:
        result = motivational_agent.generate_motivation(request)
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Stress Management Coach API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.STRESS_ESTIMATOR_PORT)