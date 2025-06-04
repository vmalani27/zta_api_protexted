from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ....db.session import get_db
from ....models.models import User, UserRole, Student
from ....schemas.schemas import Student as StudentSchema, StudentCreate
from .users import get_current_user
from ....core.security import check_permissions

router = APIRouter()

def get_role_based_fields(role: str) -> List[str]:
    """Get fields that a role can access"""
    if role.lower() == "admin":
        return ["id", "name", "address", "phone_number", "highest_education", 
               "sgpa", "cgpa", "hostel_id", "room_number", "sharing_type"]
    elif role.lower() == "teacher":
        return ["id", "name", "highest_education", "sgpa", "cgpa"]
    elif role.lower() == "warden":
        return ["id", "name", "hostel_id", "room_number", "sharing_type"]
    return []

def filter_student_data(student: Student, allowed_fields: List[str]) -> Dict:
    """Filter student data based on allowed fields"""
    student_dict = {
        "id": student.id,
        "name": student.name,
        "address": student.address,
        "phone_number": student.phone_number,
        "highest_education": student.highest_education,
        "sgpa": student.sgpa,
        "cgpa": student.cgpa,
        "hostel_id": student.hostel_id,
        "room_number": student.room_number,
        "sharing_type": student.sharing_type
    }
    return {k: v for k, v in student_dict.items() if k in allowed_fields}

@router.post("/", response_model=StudentSchema)
def create_student(
    *,
    db: Session = Depends(get_db),
    student_in: StudentCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new student. Only admin can create students.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    student = Student(**student_in.dict())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@router.get("/", response_model=List[StudentSchema])
def read_students(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve students. Teachers can see academic info, wardens can see hostel info.
    """
    # Get roles from headers
    roles = request.headers.get("X-Roles", "").split(",")
    if not roles or roles == [""]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No roles specified"
        )

    # Check if user has permission to view students
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

    # Get students from database
    students = db.query(Student).offset(skip).limit(limit).all()
    
    # Filter data based on highest role
    if "admin" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("admin")
    elif "teacher" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("teacher")
    else:  # warden
        allowed_fields = get_role_based_fields("warden")

    # Filter each student's data
    filtered_students = [filter_student_data(student, allowed_fields) for student in students]
    
    return filtered_students

@router.get("/{student_id}", response_model=StudentSchema)
def read_student(
    *,
    request: Request,
    db: Session = Depends(get_db),
    student_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get student by ID. Teachers can see academic info, wardens can see hostel info.
    """
    # Get roles from headers
    roles = request.headers.get("X-Roles", "").split(",")
    if not roles or roles == [""]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No roles specified"
        )

    # Check if user has permission to view students
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

    # Get student from database
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Filter data based on highest role
    if "admin" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("admin")
    elif "teacher" in [r.lower() for r in roles]:
        allowed_fields = get_role_based_fields("teacher")
    else:  # warden
        allowed_fields = get_role_based_fields("warden")

    # Filter student data
    filtered_student = filter_student_data(student, allowed_fields)
    
    return filtered_student

@router.put("/{student_id}", response_model=StudentSchema)
def update_student(
    *,
    db: Session = Depends(get_db),
    student_id: int,
    student_in: StudentCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update student. Only admin can update all fields, teachers can update academic info,
    wardens can update hostel info.
    """
    if not check_permissions(current_user.role, UserRole.TEACHER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    update_data = student_in.dict(exclude_unset=True)
    
    # Role-based field updates
    if current_user.role == UserRole.ADMIN:
        # Admin can update all fields
        pass
    elif current_user.role == UserRole.TEACHER:
        # Teachers can only update academic info
        update_data = {k: v for k, v in update_data.items() 
                      if k in ['sgpa', 'cgpa']}
    elif current_user.role == UserRole.WARDEN:
        # Wardens can only update hostel info
        update_data = {k: v for k, v in update_data.items() 
                      if k in ['hostel_id', 'room_number', 'sharing_type']}
    
    for field, value in update_data.items():
        setattr(student, field, value)
    
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@router.delete("/{student_id}", response_model=StudentSchema)
def delete_student(
    *,
    db: Session = Depends(get_db),
    student_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete student. Only admin can delete students.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    db.delete(student)
    db.commit()
    return student 