import re
from datetime import datetime, date
from typing import Optional, List, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

# Valid 2-letter US State abbreviations
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "MP", "AS"
}

class SexEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE_TO_ANSWER = "Decline to Answer"

def normalize_phone(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    cleaned = re.sub(r"[^\d]", "", str(v))
    # Handle optional leading +1 or 1
    if len(cleaned) == 11 and cleaned.startswith("1"):
        cleaned = cleaned[1:]
    if len(cleaned) != 10:
        raise ValueError("Must be a valid 10-digit U.S. phone number.")
    return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"

def parse_dob(v: Any) -> str:
    if isinstance(v, date):
        parsed = v
    elif isinstance(v, str):
        v = v.strip()
        # Try MM/DD/YYYY, MM-DD-YYYY, YYYY-MM-DD
        formats = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d/%y", "%Y/%m/%d"]
        parsed = None
        for fmt in formats:
            try:
                parsed = datetime.strptime(v, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError("date_of_birth must be a valid date in MM/DD/YYYY format.")
    else:
        raise ValueError("Invalid date format.")

    today = date.today()
    if parsed > today:
        raise ValueError("date_of_birth cannot be in the future.")
    if parsed.year < 1900:
        raise ValueError("date_of_birth year must be 1900 or later.")
    
    return parsed.strftime("%m/%d/%Y")

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="1–50 chars, alphabetic + hyphens/apostrophes")
    last_name: str = Field(..., min_length=1, max_length=50, description="1–50 chars, alphabetic + hyphens/apostrophes")
    date_of_birth: str = Field(..., description="Valid date, not in future, MM/DD/YYYY")
    sex: SexEnum = Field(..., description="Male, Female, Other, Decline to Answer")
    phone_number: str = Field(..., description="Valid U.S. 10-digit phone number")
    email: Optional[EmailStr] = Field(None, description="Valid email format")
    address_line_1: str = Field(..., min_length=1, max_length=255, description="Street address")
    address_line_2: Optional[str] = Field(None, max_length=255, description="Apt/Suite/Unit if applicable")
    city: str = Field(..., min_length=1, max_length=100, description="1–100 characters")
    state: str = Field(..., min_length=2, max_length=2, description="Valid 2-letter U.S. state abbreviation")
    zip_code: str = Field(..., description="5-digit or ZIP+4 U.S. format")
    insurance_provider: Optional[str] = Field(None, max_length=255, description="Name of insurance company")
    insurance_member_id: Optional[str] = Field(None, max_length=100, description="Alphanumeric member/subscriber ID")
    preferred_language: Optional[str] = Field("English", max_length=50, description="Default: English")
    emergency_contact_name: Optional[str] = Field(None, max_length=255, description="Full name")
    emergency_contact_phone: Optional[str] = Field(None, description="Valid U.S. 10-digit phone number")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace only.")
        if not re.match(r"^[a-zA-Z\s'-]+$", v):
            raise ValueError("Name can only contain alphabetic characters, spaces, hyphens, and apostrophes.")
        return v

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, v: Any) -> str:
        return parse_dob(v)

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ["male", "m"]:
                return SexEnum.MALE
            if v_clean in ["female", "f"]:
                return SexEnum.FEMALE
            if v_clean in ["other", "o"]:
                return SexEnum.OTHER
            if v_clean in ["decline", "decline to answer", "declined", "n/a"]:
                return SexEnum.DECLINE_TO_ANSWER
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        res = normalize_phone(v)
        if not res:
            raise ValueError("Phone number is required.")
        return res

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        return normalize_phone(v)

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in US_STATES:
            raise ValueError(f"State '{v}' is not a valid 2-letter U.S. state abbreviation.")
        return v_upper

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        v_clean = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v_clean):
            raise ValueError("zip_code must be a 5-digit number or ZIP+4 (e.g. 12345 or 12345-6789).")
        return v_clean

    @field_validator("insurance_member_id")
    @classmethod
    def validate_insurance_member_id(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v_clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", v_clean):
            raise ValueError("insurance_member_id must be alphanumeric.")
        return v_clean

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        if not re.match(r"^[a-zA-Z\s'-]+$", v):
            raise ValueError("Name can only contain alphabetic characters, spaces, hyphens, and apostrophes.")
        return v

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return parse_dob(v)

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ["male", "m"]:
                return SexEnum.MALE
            if v_clean in ["female", "f"]:
                return SexEnum.FEMALE
            if v_clean in ["other", "o"]:
                return SexEnum.OTHER
            if v_clean in ["decline", "decline to answer", "declined", "n/a"]:
                return SexEnum.DECLINE_TO_ANSWER
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return normalize_phone(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        return normalize_phone(v)

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_upper = v.strip().upper()
        if v_upper not in US_STATES:
            raise ValueError(f"State '{v}' is not a valid 2-letter U.S. state abbreviation.")
        return v_upper

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v_clean):
            raise ValueError("zip_code must be a 5-digit number or ZIP+4 (e.g. 12345 or 12345-6789).")
        return v_clean

    @field_validator("insurance_member_id")
    @classmethod
    def validate_insurance_member_id(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v_clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", v_clean):
            raise ValueError("insurance_member_id must be alphanumeric.")
        return v_clean

class PatientResponse(PatientBase):
    patient_id: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Standard API response envelope as requested in PDF: { "data": ..., "error": ... }
class APIEnvelope(BaseModel):
    data: Optional[Any] = None
    error: Optional[Any] = None

class AppointmentCreate(BaseModel):
    patient_id: str
    appointment_date: str
    doctor_specialty: Optional[str] = "Primary Care"
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: str
    patient_id: str
    appointment_date: str
    doctor_specialty: str
    status: str
    notes: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)
