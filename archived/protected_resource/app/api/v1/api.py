from fastapi import APIRouter
from .endpoints import auth, users, students, teachers, hostels, wardens

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(hostels.router, prefix="/hostels", tags=["hostels"])
api_router.include_router(wardens.router, prefix="/wardens", tags=["wardens"]) 