import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AppointmentCreate, AppointmentResponse, APIEnvelope
import app.crud as crud

logger = logging.getLogger("carecloud.appointments")

router = APIRouter(prefix="/appointments", tags=["Appointments (Bonus)"])

@router.get("", response_model=APIEnvelope)
async def list_appointments(
    patient_id: Optional[str] = Query(None, description="Filter by patient_id"),
    db: AsyncSession = Depends(get_db)
):
    """List all scheduled appointments or filter by patient_id."""
    appts = await crud.get_appointments(db, patient_id=patient_id)
    return {
        "data": [a.to_dict() for a in appts],
        "error": None
    }

@router.post("", response_model=APIEnvelope, status_code=status.HTTP_201_CREATED)
async def create_new_appointment(
    appt_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Schedule a new appointment for a patient."""
    patient = await crud.get_patient(db, appt_in.patient_id)
    if not patient:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"data": None, "error": f"Patient with ID '{appt_in.patient_id}' not found."}
        )
    appt = await crud.create_appointment(db, appt_in)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"data": appt.to_dict(), "error": None}
    )
