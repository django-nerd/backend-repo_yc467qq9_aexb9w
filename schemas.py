"""
Database Schemas for Hospital Management System

Each Pydantic model maps to a MongoDB collection using the class name in lowercase.
Examples:
- User -> "user"
- Doctor -> "doctor"
- Patient -> "patient"
- Appointment -> "appointment"

These schemas are used for validation at the API layer.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    role: Literal["admin", "doctor", "patient"] = Field(..., description="User role")
    is_active: bool = Field(True, description="Whether user is active")


class Doctor(BaseModel):
    user_id: str = Field(..., description="Reference to user _id (string)")
    specialty: str = Field(..., description="Medical specialty")
    experience_years: int = Field(0, ge=0, description="Years of experience")
    availability: List[str] = Field(default_factory=list, description="Available time slots or notes")


class Patient(BaseModel):
    user_id: str = Field(..., description="Reference to user _id (string)")
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[Literal["male", "female", "other"]] = None
    conditions: List[str] = Field(default_factory=list, description="Known conditions")


class Appointment(BaseModel):
    patient_id: str = Field(..., description="Patient document id (string)")
    doctor_id: str = Field(..., description="Doctor document id (string)")
    reason: str = Field(..., description="Reason for visit")
    scheduled_at: datetime = Field(..., description="Scheduled datetime (ISO 8601)")
    status: Literal["pending", "confirmed", "completed", "cancelled"] = Field("pending")


class Prescription(BaseModel):
    appointment_id: str = Field(..., description="Appointment id")
    medications: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
