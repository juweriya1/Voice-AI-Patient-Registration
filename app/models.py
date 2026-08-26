import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

def generate_uuid():
    return str(uuid.uuid4())

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(String(20), nullable=False, index=True)  # MM/DD/YYYY format
    sex = Column(String(30), nullable=False)  # Male, Female, Other, Decline to Answer
    phone_number = Column(String(30), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10), nullable=False)
    
    # Optional fields
    insurance_provider = Column(String(255), nullable=True)
    insurance_member_id = Column(String(100), nullable=True)
    preferred_language = Column(String(50), default="English", nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    
    # Timestamps & Soft Delete
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)

    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "sex": self.sex,
            "phone_number": self.phone_number,
            "email": self.email,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "insurance_provider": self.insurance_provider,
            "insurance_member_id": self.insurance_member_id,
            "preferred_language": self.preferred_language or "English",
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    patient_id = Column(String(36), ForeignKey("patients.patient_id"), nullable=False)
    appointment_date = Column(String(50), nullable=False)
    doctor_specialty = Column(String(100), default="Primary Care")
    status = Column(String(30), default="SCHEDULED")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    patient = relationship("Patient", back_populates="appointments")

    def to_dict(self):
        return {
            "appointment_id": self.appointment_id,
            "patient_id": self.patient_id,
            "appointment_date": self.appointment_date,
            "doctor_specialty": self.doctor_specialty,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class CallLog(Base):
    __tablename__ = "call_logs"

    call_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    vapi_call_id = Column(String(100), nullable=True)
    caller_phone = Column(String(30), nullable=True)
    patient_id = Column(String(36), nullable=True)
    summary = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    status = Column(String(50), default="COMPLETED")
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "call_id": self.call_id,
            "vapi_call_id": self.vapi_call_id,
            "caller_phone": self.caller_phone,
            "patient_id": self.patient_id,
            "summary": self.summary,
            "transcript": self.transcript,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
