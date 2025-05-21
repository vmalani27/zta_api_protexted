from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Protected Resource Service")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to Protected Resource Service"}

@app.get("/protected-resource")
async def protected_resource():
    """
    Protected resource endpoint
    """
    return {
        "message": "Access granted to protected resource",
        "data": {
            "resource_id": "123",
            "resource_type": "sensitive_data",
            "content": "This is protected content"
        }
    }

@app.get("/public-resource")
async def public_resource():
    """
    Public resource endpoint
    """
    return {
        "message": "Access granted to public resource",
        "data": {
            "resource_id": "456",
            "resource_type": "public_data",
            "content": "This is public content"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001) 