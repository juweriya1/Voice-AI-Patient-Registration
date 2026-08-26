# Voice AI Patient Intake & Registration System

A full-stack, voice-based patient intake system accessible via real telephony. Callers can dial a real U.S. phone number to converse naturally with an AI intake coordinator (**Maya**), who collects patient demographic information, handles edge cases and corrections, performs full read-back confirmation, persists validated records into a persistent database, and exposes them through a REST API and web dashboard.

---

## Live Demo & Endpoints

- **Live Phone Number:** `+1 (732) 782-5431`
- **Web Dashboard:** [https://warned-angeles-plot-mode.trycloudflare.com/](https://warned-angeles-plot-mode.trycloudflare.com/)
- **REST API Base URL:** `https://warned-angeles-plot-mode.trycloudflare.com`
- **Swagger Documentation:** [https://warned-angeles-plot-mode.trycloudflare.com/docs](https://warned-angeles-plot-mode.trycloudflare.com/docs)
- **Health Endpoint:** `https://warned-angeles-plot-mode.trycloudflare.com/health`

---

## Architecture Overview

```
                      +-----------------------------+
                      |     Caller (Mobile Phone)   |
                      +--------------+--------------+
                                     |
                                     | Real Phone Line (SIP/PSTN)
                                     v
                      +-----------------------------+
                      |   Telephony & Voice Pipeline|
                      |  (Deepgram STT + ElevenLabs)|
                      +--------------+--------------+
                                     |
                                     | GPT-4o Agent / Tool Calling
                                     v
+-------------------------------------------------------------------------+
| FastAPI Application Server                                               |
|                                                                         |
|  +---------------------------+       +-------------------------------+  |
|  | Voice Webhook Router      |       | Patient REST API Router       |  |
|  | /api/voice/vapi/webhook   |       | /patients, /appointments      |  |
|  +-------------+-------------+       +---------------+---------------+  |
|                |                                     |                  |
|                v                                     v                  |
|  +-------------------------------------------------------------------+  |
|  | Pydantic Validation Layer (schemas.py)                            |  |
|  | - Name regex, past DOB validation, 10-digit phone normalization   |  |
|  +-----------------------------------+-------------------------------+  |
|                                      |                                  |
|                                      v                                  |
|  +-------------------------------------------------------------------+  |
|  | Async Service & CRUD Layer (crud.py)                              |  |
|  +-----------------------------------+-------------------------------+  |
+--------------------------------------|----------------------------------+
                                       | SQLAlchemy (aiosqlite)
                                       v
                      +-----------------------------+
                      | Persistent Database         |
                      | (carecloud_patients.db)     |
                      | - patients                  |
                      | - appointments              |
                      | - call_logs                 |
                      +-----------------------------+
```

---

## Key Features

### Conversational Voice Agent
- **Natural Voice Intake:** Powered by GPT-4o, Deepgram Speech-to-Text, and ElevenLabs voice synthesis (`Rachel`).
- **Conversational Pacing:** Avoids rigid IVR menus. Gathers required demographic fields naturally and adapts to interruptions.
- **Smart Field Batching:** Instead of asking for each optional field individually, it batches them into a conversational opt-in:
  > *"I can also collect your insurance information, emergency contact, and preferred language. Would you like to provide any of those?"*
- **Mandatory Read-Back Confirmation:** Before committing any data to the database, Maya reads back all gathered information (name, DOB, phone, address, insurance, emergency contact) and explicitly asks for caller confirmation.
- **Real-Time Corrections:** Gracefully handles letter-by-letter spelling corrections (*"Actually, my last name is spelled D-A-V-I-S"*), field updates, and mid-call restart requests.
- **Duplicate Caller Recognition:** Checks caller phone numbers on intake. If an existing record matches, the agent prompts:
  > *"It looks like we already have a record for [First Name] [Last Name]. Would you like to update your information instead?"*
- **Multi-Language Support:** Seamlessly transitions into Spanish if the caller says *"Hablo español"*.
- **Post-Registration Appointment Booking:** Offers to schedule a follow-up primary care appointment upon registration.

### Backend & API
- **Strict Server-Side Validation:** Validates all data via Pydantic v2 schemas before database write (never relying solely on the LLM).
- **Persistent Storage:** Uses async SQLite via SQLAlchemy, ensuring data survives application restarts.
- **RESTful Endpoints:** Standard HTTP status codes (200, 201, 400, 404, 422, 500) and consistent response envelopes `{ "data": {...}, "error": null }`.
- **Soft-Deletes:** Patient deletion marks a `deleted_at` timestamp rather than hard-deleting records.
- **Observability:** End-of-call webhooks record caller numbers, call duration, summaries, and transcripts into the database.

---

## Patient Demographic Data Model

| Field | Type | Required | Validation Rules |
| :--- | :--- | :---: | :--- |
| `patient_id` | UUID | Auto | Unique identifier |
| `first_name` | String | Yes | 1–50 characters, alphabetic, hyphens, and apostrophes |
| `last_name` | String | Yes | 1–50 characters, alphabetic, hyphens, and apostrophes |
| `date_of_birth` | String | Yes | Valid date, not in the future, normalized to `MM/DD/YYYY` |
| `sex` | Enum | Yes | `Male`, `Female`, `Other`, `Decline to Answer` |
| `phone_number` | String | Yes | Valid U.S. 10-digit number, normalized to `(XXX) XXX-XXXX` |
| `email` | String | No | Valid email format |
| `address_line_1` | String | Yes | Street address |
| `address_line_2` | String | No | Apartment, suite, or unit number |
| `city` | String | Yes | 1–100 characters |
| `state` | String | Yes | Valid 2-letter U.S. state abbreviation (e.g., `CA`, `NY`, `TX`) |
| `zip_code` | String | Yes | 5-digit ZIP code or ZIP+4 (`12345` or `12345-6789`) |
| `insurance_provider` | String | No | Insurance company name |
| `insurance_member_id` | String | No | Alphanumeric member/subscriber ID |
| `preferred_language` | String | No | Defaults to `English` |
| `emergency_contact_name` | String | No | Full name |
| `emergency_contact_phone`| String | No | Valid U.S. 10-digit phone number |
| `created_at` / `updated_at`| Timestamp | Auto | UTC timestamp |
| `deleted_at` | Timestamp | Auto | Timestamp for soft-deleted records |

---

## REST API Reference

All responses use a standardized envelope:
```json
{
  "data": { ... },
  "error": null
}
```

### Endpoints

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/patients` | List active patients. Query params: `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| `GET` | `/patients/:id` | Retrieve a single patient by UUID |
| `POST` | `/patients` | Register a new patient with server-side validation |
| `PUT` | `/patients/:id` | Update an existing patient record (supports partial updates) |
| `DELETE` | `/patients/:id` | Soft-delete a patient record (sets `deleted_at`) |
| `GET` | `/patients/check-duplicate` | Check if a phone number already exists |
| `POST` | `/appointments` | Book a clinic visit for a registered patient |
| `GET` | `/appointments` | List scheduled appointments |
| `POST` | `/api/voice/vapi/webhook` | Webhook receiver for voice tool calls and call transcripts |
| `GET` | `/health` | Service health check |

---

## Local Development & Setup

### 1. Requirements
- Python 3.10+
- Virtual environment (`venv`)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/juweriya1/Voice-AI-Patient-Registration.git
cd Voice-AI-Patient-Registration

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure the following variables in `.env`:
```env
PORT=8000
HOST=0.0.0.0
DATABASE_URL=sqlite+aiosqlite:///./carecloud_patients.db
VAPI_API_KEY=your_vapi_private_api_key_here
```

### 4. Database Seeding
To populate the database with demonstration patient records:
```bash
python scripts/seed_db.py
```

### 5. Running the Application
```bash
uvicorn app.main:app --reload --port 8000
```
- Dashboard UI: `http://localhost:8000/`
- Interactive API Docs: `http://localhost:8000/docs`

---

## Testing

The project includes an automated test suite using `pytest` and `httpx.AsyncClient` against an in-memory SQLite instance:

```bash
pytest -v
```

### Test Coverage Highlights:
- **API Endpoints:** Create, list, retrieve, partial update, soft-delete, and query filtering.
- **Data Validation:** Checks for future DOB rejection, non-alphabetic name rejection, invalid phone formats, invalid US state abbreviations, and malformed ZIP codes.
- **Voice Tools:** Tests tool dispatchers, duplicate caller detection, appointment scheduling, and Vapi webhook payload parsing.

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── routes_patients.py       # REST API endpoints for patient records
│   │   ├── routes_voice.py          # Webhook & tool dispatcher for voice agent
│   │   ├── routes_appointments.py   # Appointment booking routes
│   │   └── routes_dashboard.py      # Web dashboard routes
│   ├── voice/
│   │   ├── prompts.py               # Maya system prompt and conversational instructions
│   │   ├── tools.py                 # JSON tool schemas for LLM function calling
│   │   └── vapi_client.py           # Vapi API client
│   ├── config.py                    # App configuration via pydantic-settings
│   ├── crud.py                      # Database queries and mutations
│   ├── database.py                  # SQLAlchemy async engine and session factory
│   ├── main.py                      # FastAPI application entry point and middleware
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── schemas.py                   # Pydantic validation schemas
│   ├── static/                      # CSS and JavaScript for dashboard
│   └── templates/                   # HTML templates (Jinja2)
├── scripts/
│   ├── seed_db.py                   # Database seeder for demo records
│   ├── setup_vapi_agent.py          # Assistant configuration script
│   └── simulate_full_call.py        # End-to-end call simulator
├── tests/
│   ├── conftest.py                  # Test fixtures and async test client
│   ├── test_api_patients.py         # Integration tests for REST API
│   ├── test_validation.py           # Unit tests for data validation rules
│   └── test_voice_tools.py          # Tests for voice tool execution
├── .env.example
├── .gitignore
├── pytest.ini
└── requirements.txt
```
