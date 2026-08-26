"""
Vapi & OpenAI Tool Definitions for Patient Intake Voice AI.
"""

VAPI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_existing_patient",
            "description": "Checks if a patient already exists in the CareCloud database using their 10-digit phone number. Use this at the start of intake to identify returning patients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The caller's 10-digit U.S. phone number (e.g., '5551234567' or '555-123-4567')."
                    }
                },
                "required": ["phone_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "register_patient",
            "description": "Registers a new patient into the CareCloud persistent database after reading back all demographic details to the caller and receiving their explicit confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Patient's first name (1-50 chars, alphabetic + hyphens/apostrophes)."
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Patient's last name (1-50 chars, alphabetic + hyphens/apostrophes)."
                    },
                    "date_of_birth": {
                        "type": "string",
                        "description": "Date of birth in MM/DD/YYYY format (must not be in the future)."
                    },
                    "sex": {
                        "type": "string",
                        "enum": ["Male", "Female", "Other", "Decline to Answer"],
                        "description": "Patient's biological sex or gender identity."
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Valid 10-digit U.S. phone number."
                    },
                    "email": {
                        "type": "string",
                        "description": "Optional email address."
                    },
                    "address_line_1": {
                        "type": "string",
                        "description": "Street address (e.g. 123 Main St)."
                    },
                    "address_line_2": {
                        "type": "string",
                        "description": "Optional apartment, suite, or unit number."
                    },
                    "city": {
                        "type": "string",
                        "description": "City name."
                    },
                    "state": {
                        "type": "string",
                        "description": "2-letter U.S. state abbreviation (e.g., 'CA', 'NY', 'TX')."
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "5-digit or ZIP+4 U.S. postal code (e.g. '90210' or '12345-6789')."
                    },
                    "insurance_provider": {
                        "type": "string",
                        "description": "Optional name of health insurance provider (e.g., Aetna, Blue Cross, Medicare)."
                    },
                    "insurance_member_id": {
                        "type": "string",
                        "description": "Optional alphanumeric member/subscriber ID."
                    },
                    "preferred_language": {
                        "type": "string",
                        "description": "Preferred language for care, default 'English'."
                    },
                    "emergency_contact_name": {
                        "type": "string",
                        "description": "Optional full name of emergency contact."
                    },
                    "emergency_contact_phone": {
                        "type": "string",
                        "description": "Optional 10-digit phone number of emergency contact."
                    }
                },
                "required": [
                    "first_name",
                    "last_name",
                    "date_of_birth",
                    "sex",
                    "phone_number",
                    "address_line_1",
                    "city",
                    "state",
                    "zip_code"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_patient",
            "description": "Updates demographic information for an existing patient record in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "The unique patient UUID to update."
                    },
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "date_of_birth": {"type": "string"},
                    "sex": {"type": "string", "enum": ["Male", "Female", "Other", "Decline to Answer"]},
                    "phone_number": {"type": "string"},
                    "email": {"type": "string"},
                    "address_line_1": {"type": "string"},
                    "address_line_2": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "zip_code": {"type": "string"},
                    "insurance_provider": {"type": "string"},
                    "insurance_member_id": {"type": "string"},
                    "preferred_language": {"type": "string"},
                    "emergency_contact_name": {"type": "string"},
                    "emergency_contact_phone": {"type": "string"}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": "Schedules a primary care appointment for a registered patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "The patient's UUID."
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "Requested appointment date and time (e.g., 'Next Monday at 10:00 AM' or '2026-09-01 10:00 AM')."
                    },
                    "doctor_specialty": {
                        "type": "string",
                        "description": "Specialty required (default: 'Primary Care')."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes or reason for visit."
                    }
                },
                "required": ["patient_id", "appointment_date"]
            }
        }
    }
]
