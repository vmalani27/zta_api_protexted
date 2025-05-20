from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....db.session import get_db
from ....models.models import User, UserRole, Warden
from ....schemas.schemas import Warden as WardenSchema, WardenCreate
from .users import get_current_user
from ....core.security import check_permissions

router = APIRouter()

@router.post("/", response_model=WardenSchema)
def create_warden(
    *,
    db: Session = Depends(get_db),
    warden_in: WardenCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new warden. Only admin can create wardens.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    warden = Warden(**warden_in.dict())
    db.add(warden)
    db.commit()
    db.refresh(warden)
    return warden

@router.get("/", response_model=List[WardenSchema])
def read_wardens(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve wardens. Only admin and wardens can see warden list.
    """
    if not check_permissions(current_user.role, UserRole.WARDEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    wardens = db.query(Warden).offset(skip).limit(limit).all()
    return wardens

@router.get("/{warden_id}", response_model=WardenSchema)
def read_warden(
    *,
    db: Session = Depends(get_db),
    warden_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get warden by ID. Only admin and wardens can see warden details.
    """
    if not check_permissions(current_user.role, UserRole.WARDEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    warden = db.query(Warden).filter(Warden.id == warden_id).first()
    if not warden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warden not found"
        )
    return warden

@router.put("/{warden_id}", response_model=WardenSchema)
def update_warden(
    *,
    db: Session = Depends(get_db),
    warden_id: int,
    warden_in: WardenCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update warden. Only admin can update warden information.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    warden = db.query(Warden).filter(Warden.id == warden_id).first()
    if not warden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warden not found"
        )
    
    for field, value in warden_in.dict(exclude_unset=True).items():
        setattr(warden, field, value)
    
    db.add(warden)
    db.commit()
    db.refresh(warden)
    return warden

@router.delete("/{warden_id}", response_model=WardenSchema)
def delete_warden(
    *,
    db: Session = Depends(get_db),
    warden_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete warden. Only admin can delete wardens.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    warden = db.query(Warden).filter(Warden.id == warden_id).first()
    if not warden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warden not found"
        )
    
    db.delete(warden)
    db.commit()
    return warden 