import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import PatientCreate, PatientUpdate, APIEnvelope
import app.crud as crud

logger = logging.getLogger("carecloud.patients")

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=APIEnvelope, status_code=status.HTTP_200_OK)
async def list_patients(
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    date_of_birth: Optional[str] = Query(None, description="Filter by date of birth (MM/DD/YYYY)"),
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    include_deleted: bool = Query(False, description="Include soft-deleted patients"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all registered patients.
    Supports filtering by last_name, date_of_birth, and phone_number.
    Excludes soft-deleted patients by default.
    """
    try:
        patients = await crud.get_patients(
            db,
            last_name=last_name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            include_deleted=include_deleted
        )
        return {
            "data": [p.to_dict() for p in patients],
            "error": None
        }
    except Exception as e:
        logger.error(f"Error listing patients: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"data": None, "error": f"Failed to retrieve patients: {str(e)}"}
        )

@router.get("/check-duplicate", response_model=APIEnvelope, status_code=status.HTTP_200_OK)
async def check_duplicate_patient(
    phone_number: str = Query(..., description="Phone number to check for existing record"),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a patient already exists with the given phone number.
    Returns existing patient info if found, or exists=False.
    """
    patient = await crud.find_patient_by_phone(db, phone_number)
    if patient:
        return {
            "data": {
                "exists": True,
                "patient": patient.to_dict()
            },
            "error": None
        }
    return {
        "data": {
            "exists": False,
            "patient": None
        },
        "error": None
    }

@router.get("/{patient_id}", response_model=APIEnvelope, status_code=status.HTTP_200_OK)
async def get_patient_by_id(
    patient_id: str,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a single patient by their unique patient_id UUID.
    """
    patient = await crud.get_patient(db, patient_id, include_deleted=include_deleted)
    if not patient:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"data": None, "error": f"Patient with ID '{patient_id}' not found."}
        )
    return {
        "data": patient.to_dict(),
        "error": None
    }

@router.post("", response_model=APIEnvelope, status_code=status.HTTP_201_CREATED)
async def create_new_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new patient record with full server-side validation.
    Returns the created patient record including auto-generated patient_id.
    """
    try:
        new_patient = await crud.create_patient(db, patient_in)
        logger.info(f"Successfully registered patient: {new_patient.first_name} {new_patient.last_name} ({new_patient.patient_id})")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"data": new_patient.to_dict(), "error": None}
        )
    except Exception as e:
        logger.error(f"Error creating patient: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"data": None, "error": f"Failed to create patient: {str(e)}"}
        )

@router.put("/{patient_id}", response_model=APIEnvelope, status_code=status.HTTP_200_OK)
async def update_existing_patient(
    patient_id: str,
    patient_in: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing patient record. Partial updates are supported.
    """
    try:
        updated = await crud.update_patient(db, patient_id, patient_in)
        if not updated:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"data": None, "error": f"Patient with ID '{patient_id}' not found."}
            )
        logger.info(f"Updated patient {patient_id}")
        return {
            "data": updated.to_dict(),
            "error": None
        }
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"data": None, "error": f"Failed to update patient: {str(e)}"}
        )

@router.delete("/{patient_id}", response_model=APIEnvelope, status_code=status.HTTP_200_OK)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Soft-delete a patient record (sets deleted_at timestamp, does not hard-delete).
    """
    deleted = await crud.soft_delete_patient(db, patient_id)
    if not deleted:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"data": None, "error": f"Patient with ID '{patient_id}' not found."}
        )
    logger.info(f"Soft-deleted patient {patient_id} at {deleted.deleted_at}")
    return {
        "data": {
            "patient_id": deleted.patient_id,
            "deleted_at": deleted.deleted_at.isoformat() if deleted.deleted_at else None,
            "message": "Patient record soft-deleted successfully."
        },
        "error": None
    }
