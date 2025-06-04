from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from .config import settings
from ..models.models import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def check_permissions(user_role: str, required_role: str) -> bool:
    """Check if user has required role or higher"""
    role_hierarchy = {
        UserRole.ADMIN: 3,
        UserRole.TEACHER: 2,
        UserRole.WARDEN: 2,
        UserRole.STUDENT: 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level 