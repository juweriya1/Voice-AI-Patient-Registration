"""
Database Seeding Script for CareCloud Patient Registration.
Seeds 2 realistic patient records for demonstration and testing.
"""

import asyncio
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, AsyncSessionLocal
from app.schemas import PatientCreate
import app.crud as crud

DEMO_PATIENTS = [
    PatientCreate(
        first_name="Jane",
        last_name="Doe",
        date_of_birth="05/14/1988",
        sex="Female",
        phone_number="555-123-4567",
        email="jane.doe@example.com",
        address_line_1="100 Market St",
        address_line_2="Apt 4B",
        city="San Francisco",
        state="CA",
        zip_code="94105",
        insurance_provider="Blue Shield of California",
        insurance_member_id="BSC987654321",
        preferred_language="English",
        emergency_contact_name="John Doe",
        emergency_contact_phone="555-987-6543"
    ),
    PatientCreate(
        first_name="Carlos",
        last_name="Rodriguez",
        date_of_birth="11/22/1975",
        sex="Male",
        phone_number="555-987-6543",
        email="carlos.rodriguez@example.com",
        address_line_1="450 Biscayne Blvd",
        city="Miami",
        state="FL",
        zip_code="33132",
        insurance_provider="Aetna Health",
        insurance_member_id="AET11223344",
        preferred_language="Spanish",
        emergency_contact_name="Maria Rodriguez",
        emergency_contact_phone="555-888-9999"
    )
]

async def seed():
    print("Initializing database...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        print("Checking existing records...")
        existing = await crud.get_patients(db, include_deleted=True)
        if existing:
            print(f"Database already contains {len(existing)} patient(s). Skipping seed.")
            return

        for patient_in in DEMO_PATIENTS:
            patient = await crud.create_patient(db, patient_in)
            print(f"✅ Seeded Patient: {patient.first_name} {patient.last_name} (ID: {patient.patient_id})")

    print("🎉 Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
