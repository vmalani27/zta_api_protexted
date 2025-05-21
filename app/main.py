from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1.api import api_router
from .db.session import engine
from .models import models
from .core.pep import pep

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to ZTA API"}

@app.get("/protected-resource")
async def protected_resource(token_data: dict = Depends(pep)):
    """
    Protected resource endpoint that requires valid JWT token and enforces policies
    """
    return {
        "message": "Access granted to protected resource",
        "user_info": {
            "sub": token_data.get("sub"),
            "roles": token_data.get("realm_access", {}).get("roles", [])
        }
    }

@app.get("/public-resource")
async def public_resource(token_data: dict = Depends(pep)):
    """
    Public resource endpoint that still validates token but has more permissive policies
    """
    return {
        "message": "Access granted to public resource",
        "user_info": {
            "sub": token_data.get("sub"),
            "roles": token_data.get("realm_access", {}).get("roles", [])
        }
    } 