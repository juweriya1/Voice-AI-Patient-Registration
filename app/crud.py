import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, and_
from app.models import Patient, Appointment, CallLog, utc_now
from app.schemas import PatientCreate, PatientUpdate, AppointmentCreate, normalize_phone

async def get_patient(db: AsyncSession, patient_id: str, include_deleted: bool = False) -> Optional[Patient]:
    """Retrieve a single patient by ID."""
    stmt = select(Patient).where(Patient.patient_id == patient_id)
    if not include_deleted:
        stmt = stmt.where(Patient.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_patients(
    db: AsyncSession,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
    include_deleted: bool = False
) -> List[Patient]:
    """Retrieve all patients with optional filtering."""
    stmt = select(Patient)
    conditions = []
    
    if not include_deleted:
        conditions.append(Patient.deleted_at.is_(None))
        
    if last_name:
        conditions.append(Patient.last_name.ilike(f"%{last_name.strip()}%"))
        
    if date_of_birth:
        conditions.append(Patient.date_of_birth == date_of_birth.strip())
        
    if phone_number:
        # Search either raw phone or formatted phone
        clean_p = re.sub(r"[^\d]", "", phone_number)
        if len(clean_p) == 11 and clean_p.startswith("1"):
            clean_p = clean_p[1:]
        if len(clean_p) == 10:
            formatted = f"({clean_p[:3]}) {clean_p[3:6]}-{clean_p[6:]}"
            conditions.append(or_(Patient.phone_number == formatted, Patient.phone_number.contains(clean_p)))
        else:
            conditions.append(Patient.phone_number.ilike(f"%{phone_number.strip()}%"))

    if conditions:
        stmt = stmt.where(and_(*conditions))
        
    stmt = stmt.order_by(Patient.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def find_patient_by_phone(db: AsyncSession, phone_number: str) -> Optional[Patient]:
    """Find active patient by phone number."""
    clean_p = re.sub(r"[^\d]", "", phone_number)
    if len(clean_p) == 11 and clean_p.startswith("1"):
        clean_p = clean_p[1:]
    if len(clean_p) == 10:
        formatted = f"({clean_p[:3]}) {clean_p[3:6]}-{clean_p[6:]}"
        stmt = select(Patient).where(
            and_(
                Patient.deleted_at.is_(None),
                or_(Patient.phone_number == formatted, Patient.phone_number.contains(clean_p))
            )
        )
    else:
        stmt = select(Patient).where(
            and_(
                Patient.deleted_at.is_(None),
                Patient.phone_number.contains(phone_number.strip())
            )
        )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_patient(db: AsyncSession, patient_in: PatientCreate) -> Patient:
    """Create a new patient record in the database."""
    patient_data = patient_in.model_dump()
    patient = Patient(**patient_data)
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient

async def update_patient(db: AsyncSession, patient_id: str, patient_in: PatientUpdate) -> Optional[Patient]:
    """Partially update an existing patient record."""
    patient = await get_patient(db, patient_id)
    if not patient:
        return None
        
    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
        
    patient.updated_at = utc_now()
    await db.commit()
    await db.refresh(patient)
    return patient

async def soft_delete_patient(db: AsyncSession, patient_id: str) -> Optional[Patient]:
    """Soft-delete a patient record by setting deleted_at timestamp."""
    patient = await get_patient(db, patient_id)
    if not patient:
        return None
        
    patient.deleted_at = utc_now()
    patient.updated_at = utc_now()
    await db.commit()
    await db.refresh(patient)
    return patient

async def create_appointment(db: AsyncSession, appt_in: AppointmentCreate) -> Appointment:
    """Create an appointment for a patient."""
    appt = Appointment(
        patient_id=appt_in.patient_id,
        appointment_date=appt_in.appointment_date,
        doctor_specialty=appt_in.doctor_specialty or "Primary Care",
        notes=appt_in.notes
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt

async def get_appointments(db: AsyncSession, patient_id: Optional[str] = None) -> List[Appointment]:
    """Retrieve appointments."""
    stmt = select(Appointment)
    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    stmt = stmt.order_by(Appointment.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def create_call_log(
    db: AsyncSession,
    caller_phone: Optional[str] = None,
    patient_id: Optional[str] = None,
    vapi_call_id: Optional[str] = None,
    summary: Optional[str] = None,
    transcript: Optional[str] = None
) -> CallLog:
    """Create a call log record."""
    call_log = CallLog(
        caller_phone=caller_phone,
        patient_id=patient_id,
        vapi_call_id=vapi_call_id,
        summary=summary,
        transcript=transcript
    )
    db.add(call_log)
    await db.commit()
    await db.refresh(call_log)
    return call_log

async def get_call_logs(db: AsyncSession) -> List[CallLog]:
    """Retrieve all call logs."""
    stmt = select(CallLog).order_by(CallLog.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
