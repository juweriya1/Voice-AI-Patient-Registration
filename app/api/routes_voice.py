import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.database import get_db
from app.schemas import PatientCreate, PatientUpdate, AppointmentCreate
import app.crud as crud

logger = logging.getLogger("carecloud.voice")

router = APIRouter(prefix="/voice", tags=["Voice AI & Telephony Webhook"])

async def execute_voice_tool(name: str, args: Dict[str, Any], db: AsyncSession, caller_phone: Optional[str] = None) -> Dict[str, Any]:
    """
    Central dispatcher for voice agent tool calls.
    Invokes the service / CRUD layer and validates inputs server-side.
    """
    logger.info(f"Executing voice tool '{name}' with args: {args}")
    
    if name == "check_existing_patient":
        phone = args.get("phone_number") or caller_phone
        if not phone:
            return {"exists": False, "message": "No phone number provided to check."}
        
        patient = await crud.find_patient_by_phone(db, phone)
        if patient:
            return {
                "exists": True,
                "patient_id": patient.patient_id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone_number": patient.phone_number,
                "date_of_birth": patient.date_of_birth,
                "message": f"Found existing patient record for {patient.first_name} {patient.last_name}."
            }
        else:
            return {
                "exists": False,
                "message": "No existing record found for this phone number."
            }

    elif name == "register_patient":
        try:
            # Validate input through Pydantic schema
            patient_in = PatientCreate(**args)
            new_patient = await crud.create_patient(db, patient_in)
            logger.info(f"Voice Agent registered new patient: {new_patient.patient_id}")
            return {
                "status": "success",
                "patient_id": new_patient.patient_id,
                "first_name": new_patient.first_name,
                "last_name": new_patient.last_name,
                "message": f"Patient {new_patient.first_name} {new_patient.last_name} successfully registered with ID {new_patient.patient_id}."
            }
        except ValidationError as ve:
            errors = [f"{err['loc'][-1]}: {err['msg']}" for err in ve.errors()]
            error_msg = "; ".join(errors)
            logger.warning(f"Voice Agent registration validation error: {error_msg}")
            return {
                "status": "validation_error",
                "error": error_msg,
                "message": f"Validation failed: {error_msg}. Please ask the caller to clarify."
            }
        except Exception as e:
            logger.error(f"Error registering patient from voice tool: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": "A database error occurred while saving patient information."
            }

    elif name == "update_patient":
        patient_id = args.get("patient_id")
        if not patient_id:
            return {"status": "error", "message": "patient_id is required for updates."}
        try:
            update_data = {k: v for k, v in args.items() if k != "patient_id" and v is not None}
            patient_update = PatientUpdate(**update_data)
            updated = await crud.update_patient(db, patient_id, patient_update)
            if not updated:
                return {"status": "error", "message": f"Patient with ID {patient_id} not found."}
            return {
                "status": "success",
                "patient_id": updated.patient_id,
                "message": f"Patient record for {updated.first_name} {updated.last_name} updated successfully."
            }
        except ValidationError as ve:
            errors = [f"{err['loc'][-1]}: {err['msg']}" for err in ve.errors()]
            return {"status": "validation_error", "error": "; ".join(errors)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif name == "schedule_appointment":
        patient_id = args.get("patient_id")
        appointment_date = args.get("appointment_date")
        if not patient_id or not appointment_date:
            return {"status": "error", "message": "patient_id and appointment_date are required."}
        try:
            appt_in = AppointmentCreate(
                patient_id=patient_id,
                appointment_date=appointment_date,
                doctor_specialty=args.get("doctor_specialty", "Primary Care"),
                notes=args.get("notes", "Scheduled via Voice AI")
            )
            appt = await crud.create_appointment(db, appt_in)
            return {
                "status": "success",
                "appointment_id": appt.appointment_id,
                "appointment_date": appt.appointment_date,
                "message": f"Appointment successfully scheduled for {appt.appointment_date}."
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    else:
        return {"status": "error", "message": f"Unknown tool name: {name}"}

@router.post("/vapi/webhook")
async def vapi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Main webhook endpoint for Vapi Telephony & Voice AI.
    Handles tool-calls, assistant responses, and end-of-call transcripts.
    """
    body = await request.json()
    message = body.get("message", {})
    message_type = message.get("type")
    
    logger.info(f"Received Vapi webhook event: {message_type}")

    # Handle Tool Calling (Function Calls)
    if message_type == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        call_info = message.get("call", {})
        customer_phone = call_info.get("customer", {}).get("number")
        
        results = []
        for tc in tool_calls:
            tool_id = tc.get("id")
            func = tc.get("function", {})
            func_name = func.get("name")
            func_args = func.get("arguments", {})
            
            if isinstance(func_args, str):
                try:
                    func_args = json.loads(func_args)
                except Exception:
                    func_args = {}

            tool_result = await execute_voice_tool(func_name, func_args, db, caller_phone=customer_phone)
            results.append({
                "toolCallId": tool_id,
                "result": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
            })

        return {"results": results}

    # Handle End of Call Report (Observability & Transcript Persistence)
    elif message_type in ("end-of-call-report", "status-update"):
        call_info = message.get("call", {})
        call_id = call_info.get("id")
        customer_phone = call_info.get("customer", {}).get("number")
        transcript = message.get("transcript") or message.get("artifact", {}).get("transcript")
        summary = message.get("summary") or message.get("artifact", {}).get("summary")
        
        if transcript or summary:
            await crud.create_call_log(
                db,
                caller_phone=customer_phone,
                vapi_call_id=call_id,
                summary=summary,
                transcript=transcript
            )
            logger.info(f"Persisted call transcript for Vapi call {call_id}")
            
        return {"status": "ok"}

    return {"status": "ok"}

@router.post("/tools/execute")
async def execute_tool_direct(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Direct tool execution endpoint for testing and Web Voice Simulator.
    Payload: { "tool": "register_patient", "arguments": { ... } }
    """
    payload = await request.json()
    tool_name = payload.get("tool")
    args = payload.get("arguments", {})
    caller_phone = payload.get("caller_phone")
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="Missing 'tool' in request body.")

    result = await execute_voice_tool(tool_name, args, db, caller_phone=caller_phone)
    return {"data": result, "error": None}
