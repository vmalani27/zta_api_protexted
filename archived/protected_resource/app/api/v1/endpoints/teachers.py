from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....db.session import get_db
from ....models.models import User, UserRole, Teacher
from ....schemas.schemas import Teacher as TeacherSchema, TeacherCreate
from .users import get_current_user
from ....core.security import check_permissions

router = APIRouter()

@router.post("/", response_model=TeacherSchema)
def create_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_in: TeacherCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new teacher. Only admin can create teachers.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    teacher = Teacher(**teacher_in.dict())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher

@router.get("/", response_model=List[TeacherSchema])
def read_teachers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve teachers. Only admin and teachers can see teacher list.
    """
    if not check_permissions(current_user.role, UserRole.TEACHER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    teachers = db.query(Teacher).offset(skip).limit(limit).all()
    return teachers

@router.get("/{teacher_id}", response_model=TeacherSchema)
def read_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get teacher by ID. Only admin and teachers can see teacher details.
    """
    if not check_permissions(current_user.role, UserRole.TEACHER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    return teacher

@router.put("/{teacher_id}", response_model=TeacherSchema)
def update_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: int,
    teacher_in: TeacherCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update teacher. Only admin can update teacher information.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    for field, value in teacher_in.dict(exclude_unset=True).items():
        setattr(teacher, field, value)
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher

@router.delete("/{teacher_id}", response_model=TeacherSchema)
def delete_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete teacher. Only admin can delete teachers.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    db.delete(teacher)
    db.commit()
    return teacher 