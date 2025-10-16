#Vinushas
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents.motivational_agent import motivational_agent, MotivationRequest
import uvicorn

app = FastAPI(title="Motivational Agent API")

# Add CORS middleware to motivational agent too
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-motivation")
async def generate_motivation(request: MotivationRequest):
    return motivational_agent.generate_motivation(request).dict()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
    