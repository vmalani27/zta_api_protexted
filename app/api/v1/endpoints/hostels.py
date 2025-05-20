from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....db.session import get_db
from ....models.models import User, UserRole, Hostel
from ....schemas.schemas import Hostel as HostelSchema, HostelCreate
from .users import get_current_user
from ....core.security import check_permissions

router = APIRouter()

@router.post("/", response_model=HostelSchema)
def create_hostel(
    *,
    db: Session = Depends(get_db),
    hostel_in: HostelCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new hostel. Only admin can create hostels.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hostel = Hostel(**hostel_in.dict())
    db.add(hostel)
    db.commit()
    db.refresh(hostel)
    return hostel

@router.get("/", response_model=List[HostelSchema])
def read_hostels(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve hostels. Only admin and wardens can see hostel list.
    """
    if not check_permissions(current_user.role, UserRole.WARDEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hostels = db.query(Hostel).offset(skip).limit(limit).all()
    return hostels

@router.get("/{hostel_id}", response_model=HostelSchema)
def read_hostel(
    *,
    db: Session = Depends(get_db),
    hostel_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get hostel by ID. Only admin and wardens can see hostel details.
    """
    if not check_permissions(current_user.role, UserRole.WARDEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hostel not found"
        )
    return hostel

@router.put("/{hostel_id}", response_model=HostelSchema)
def update_hostel(
    *,
    db: Session = Depends(get_db),
    hostel_id: int,
    hostel_in: HostelCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update hostel. Only admin can update hostel information.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hostel not found"
        )
    
    for field, value in hostel_in.dict(exclude_unset=True).items():
        setattr(hostel, field, value)
    
    db.add(hostel)
    db.commit()
    db.refresh(hostel)
    return hostel

@router.delete("/{hostel_id}", response_model=HostelSchema)
def delete_hostel(
    *,
    db: Session = Depends(get_db),
    hostel_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete hostel. Only admin can delete hostels.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hostel not found"
        )
    
    db.delete(hostel)
    db.commit()
    return hostel 