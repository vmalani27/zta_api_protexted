from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    WARDEN = "warden"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String,unique=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)

    # Relationships
    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)
    warden = relationship("Warden", back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    address = Column(String)
    phone_number = Column(String)
    highest_education = Column(String)
    sgpa = Column(Float)
    cgpa = Column(Float)
    hostel_id = Column(Integer, ForeignKey("hostels.id"))
    room_number = Column(String)
    sharing_type = Column(String)  # e.g., "Single", "Double", "Triple"

    # Relationships
    user = relationship("User", back_populates="student")
    hostel = relationship("Hostel", back_populates="students")

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    department = Column(String)
    specialization = Column(String)

    # Relationships
    user = relationship("User", back_populates="teacher")

class Hostel(Base):
    __tablename__ = "hostels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    total_rooms = Column(Integer)
    warden_id = Column(Integer, ForeignKey("wardens.id"))

    # Relationships
    students = relationship("Student", back_populates="hostel")
    warden = relationship("Warden", back_populates="hostel")

class Warden(Base):
    __tablename__ = "wardens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    contact_number = Column(String)

    # Relationships
    user = relationship("User", back_populates="warden")
    hostel = relationship("Hostel", back_populates="warden") 