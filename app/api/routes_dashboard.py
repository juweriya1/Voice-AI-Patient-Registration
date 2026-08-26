from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database import get_db
from app.config import settings
import app.crud as crud

router = APIRouter(tags=["Dashboard UI"])

# Setup template directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the CareCloud Patient Intake Dashboard."""
    patients = await crud.get_patients(db, include_deleted=True)
    active_patients = [p for p in patients if p.deleted_at is None]
    deleted_patients = [p for p in patients if p.deleted_at is not None]
    appointments = await crud.get_appointments(db)
    call_logs = await crud.get_call_logs(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "patients": [p.to_dict() for p in active_patients],
            "deleted_count": len(deleted_patients),
            "appointments": [a.to_dict() for a in appointments],
            "call_logs": [c.to_dict() for c in call_logs],
            "phone_number": settings.PHONE_NUMBER or "+1 (732) 782-5431",
            "vapi_assistant_id": settings.VAPI_ASSISTANT_ID or "2e7d665f-c6b5-416f-a839-b9c07269977e",
            "environment": settings.ENVIRONMENT,
        }
    )
