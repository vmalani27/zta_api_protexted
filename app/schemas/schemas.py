from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.models import UserRole

# Base schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole

class StudentBase(BaseModel):
    name: str
    address: str
    phone_number: str
    highest_education: str
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    hostel_id: Optional[int] = None
    room_number: Optional[str] = None
    sharing_type: Optional[str] = None

class TeacherBase(BaseModel):
    name: str
    department: str
    specialization: str

class HostelBase(BaseModel):
    name: str
    address: str
    total_rooms: int

class WardenBase(BaseModel):
    name: str
    contact_number: str

# Create schemas
class UserCreate(UserBase):
    password: str

class StudentCreate(StudentBase):
    pass

class TeacherCreate(TeacherBase):
    pass

class HostelCreate(HostelBase):
    pass

class WardenCreate(WardenBase):
    pass

# Response schemas
class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Student(StudentBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class Teacher(TeacherBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class Hostel(HostelBase):
    id: int
    warden_id: Optional[int]

    class Config:
        from_attributes = True

class Warden(WardenBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None 