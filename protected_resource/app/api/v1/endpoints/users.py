from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ....core.security import get_password_hash
from ....db.session import get_db
from ....models.models import User, UserRole
from ....schemas.schemas import User as UserSchema, UserCreate

router = APIRouter()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from request headers"""
    username = request.headers.get("X-User")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user information"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

def get_role_based_fields(role: str) -> List[str]:
    """Get fields that a role can access"""
    if role.lower() == "admin":
        return ["id", "username", "email", "role", "is_active"]
    elif role.lower() == "teacher":
        return ["id", "username", "email", "role"]
    elif role.lower() == "warden":
        return ["id", "username", "email", "role"]
    return []

def filter_user_data(user: User, allowed_fields: List[str]) -> Dict:
    """Filter user data based on allowed fields"""
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }
    return {k: v for k, v in user_dict.items() if k in allowed_fields}

@router.get("/", response_model=List[UserSchema])
def read_users(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve users. Only admin can see all users.
    """
    # Get roles from headers
    roles = request.headers.get("X-Roles", "").split(",")
    if not roles or roles == [""]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No roles specified"
        )

    # Check if user has permission to view users
    has_permission = False
    for role in roles:
        if role.lower() in ["admin", "teacher", "warden"]:
            has_permission = True
            break

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get users from database
    users = db.query(User).offset(skip).limit(limit).all()
    
    # Filter data based on highest role
    if "admin" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("admin")
    elif "teacher" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("teacher")
    else:  # warden
        allowed_fields = get_role_based_fields("warden")

    # Filter each user's data
    filtered_users = [filter_user_data(user, allowed_fields) for user in users]
    
    return filtered_users

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    *,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int
) -> Any:
    """
    Get user by ID. Only admin can see all user details.
    """
    # Get roles from headers
    roles = request.headers.get("X-Roles", "").split(",")
    if not roles or roles == [""]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No roles specified"
        )

    # Check if user has permission to view users
    has_permission = False
    for role in roles:
        if role.lower() in ["admin", "teacher", "warden"]:
            has_permission = True
            break

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Filter data based on highest role
    if "admin" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("admin")
    elif "teacher" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("teacher")
    else:  # warden
        allowed_fields = get_role_based_fields("warden")

    # Filter user data
    filtered_user = filter_user_data(user, allowed_fields)
    
    return filtered_user

@router.post("/", response_model=UserSchema)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    request: Request
) -> Any:
    """
    Create new user. Only admin can create users.
    """
    # Get roles from headers
    roles = request.headers.get("X-Roles", "").split(",")
    if not roles or "admin" not in [r.lower() for r in roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create users"
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user 