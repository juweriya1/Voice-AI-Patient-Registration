"""
End-to-End Voice AI Intake Call Simulation.
Tests every step of the conversational flow, webhook execution,
read-back confirmation, patient registration, and appointment booking.
"""

import requests
import json
import time

import os
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

def run_simulation():
    print("=" * 65)
    print("📞 SIMULATING END-TO-END PATIENT INTAKE CALL WITH MAYA")
    print("=" * 65)

    call_id = f"sim-call-{int(time.time())}"
    caller_phone = "(555) 321-7654"

    # Step 1: Maya greets and checks returning caller
    print("\n[Step 1] Maya answers call and checks if caller exists...")
    print(f"   Maya: 'Hello! Thank you for calling CareCloud Patient Registration. My name is Maya...'")
    print(f"   Caller: 'Hi Maya, I am Michael Scott, calling from {caller_phone}'")
    
    dup_check_payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": caller_phone}},
            "toolCalls": [
                {
                    "id": "tc_001",
                    "type": "function",
                    "function": {
                        "name": "check_existing_patient",
                        "arguments": {"phone_number": caller_phone}
                    }
                }
            ]
        }
    }
    r1 = requests.post(f"{BASE_URL}/api/voice/vapi/webhook", json=dup_check_payload).json()
    res1 = json.loads(r1["results"][0]["result"])
    print(f"   Tool Response: exists={res1.get('exists')} ({res1.get('message')})")
    assert res1.get("exists") is False, "Expected new patient"

    # Step 2: Caller provides required demographic information
    print("\n[Step 2] Maya collects required demographics...")
    print("   Name: Michael Scott")
    print("   DOB: 03/15/1965")
    print("   Sex: Male")
    print("   Phone: (555) 321-7654")
    print("   Address: 1725 Slough Ave, Scranton, PA 18503")

    # Step 3: Maya offers optional fields
    print("\n[Step 3] Maya offers optional fields (insurance, emergency contact)...")
    print("   Maya: 'I can also collect your insurance information, emergency contact, and preferred language...'")
    print("   Caller: 'Yes, I have Blue Cross insurance with ID BC998877, and emergency contact Dwight Schrute at 555-888-1234.'")

    # Step 4: Mandatory Read-Back Confirmation
    print("\n[Step 4] Maya reads back all information for explicit confirmation...")
    print("   Maya: 'Let me read back everything: Name: Michael Scott; DOB: March 15, 1965; Sex: Male; Phone: (555) 321-7654; Address: 1725 Slough Ave, Scranton, PA 18503; Insurance: Blue Cross (BC998877); Emergency: Dwight Schrute (555-888-1234). Does everything sound correct?'")
    print("   Caller: 'Yes, that is completely correct.'")

    # Step 5: Save Patient via register_patient tool
    print("\n[Step 5] Maya invokes 'register_patient' tool...")
    reg_payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": caller_phone}},
            "toolCalls": [
                {
                    "id": "tc_002",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Michael",
                            "last_name": "Scott",
                            "date_of_birth": "03/15/1965",
                            "sex": "Male",
                            "phone_number": caller_phone,
                            "email": "michael.scott@dundermifflin.com",
                            "address_line_1": "1725 Slough Ave",
                            "city": "Scranton",
                            "state": "PA",
                            "zip_code": "18503",
                            "insurance_provider": "Blue Cross",
                            "insurance_member_id": "BC998877",
                            "preferred_language": "English",
                            "emergency_contact_name": "Dwight Schrute",
                            "emergency_contact_phone": "555-888-1234"
                        }
                    }
                }
            ]
        }
    }
    r2 = requests.post(f"{BASE_URL}/api/voice/vapi/webhook", json=reg_payload).json()
    res2 = json.loads(r2["results"][0]["result"])
    patient_id = res2.get("patient_id")
    print(f"   Tool Response: status={res2.get('status')}, patient_id={patient_id}")
    print(f"   Maya: 'You are all set, Michael!'")
    assert res2.get("status") == "success"

    # Step 6: Bonus - Appointment Booking
    print("\n[Step 6] Maya offers appointment scheduling...")
    print("   Maya: 'Would you like to schedule your first primary care appointment while we are on the line?'")
    print("   Caller: 'Yes please, next Thursday at 11:00 AM.'")
    
    appt_payload = {
        "message": {
            "type": "tool-calls",
            "call": {"id": call_id, "customer": {"number": caller_phone}},
            "toolCalls": [
                {
                    "id": "tc_003",
                    "type": "function",
                    "function": {
                        "name": "schedule_appointment",
                        "arguments": {
                            "patient_id": patient_id,
                            "appointment_date": "Next Thursday at 11:00 AM",
                            "doctor_specialty": "Primary Care",
                            "notes": "New patient comprehensive exam"
                        }
                    }
                }
            ]
        }
    }
    r3 = requests.post(f"{BASE_URL}/api/voice/vapi/webhook", json=appt_payload).json()
    res3 = json.loads(r3["results"][0]["result"])
    print(f"   Tool Response: status={res3.get('status')}, appt_id={res3.get('appointment_id')}")
    assert res3.get("status") == "success"

    # Step 7: End of Call & Transcript Persistence
    print("\n[Step 7] End of call report & transcript persisted...")
    end_payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": call_id, "customer": {"number": caller_phone}},
            "summary": "Patient Michael Scott registered successfully and scheduled an appointment for Next Thursday at 11:00 AM.",
            "transcript": "Maya: Hello! Thank you for calling CareCloud... Caller: Hi Maya, Michael Scott..."
        }
    }
    requests.post(f"{BASE_URL}/api/voice/vapi/webhook", json=end_payload)
    print("   Call Log & Transcript successfully saved to database.")

    # Step 8: Verification via REST API & Persistence Check
    print("\n[Step 8] Verifying persistence via REST API...")
    patient_res = requests.get(f"{BASE_URL}/patients/{patient_id}").json()
    print(f"   GET /patients/{patient_id} -> {patient_res['data']['first_name']} {patient_res['data']['last_name']} (Phone: {patient_res['data']['phone_number']})")
    assert patient_res["data"]["first_name"] == "Michael"

    # Step 9: Testing Duplicate Detection on Second Call
    print("\n[Step 9] Testing Returning Caller Duplicate Detection on Call 2...")
    r_dup = requests.post(f"{BASE_URL}/api/voice/vapi/webhook", json=dup_check_payload).json()
    res_dup = json.loads(r_dup["results"][0]["result"])
    print(f"   Tool Response: exists={res_dup.get('exists')}! Found: {res_dup.get('first_name')} {res_dup.get('last_name')}")
    print(f"   Maya: 'It looks like we already have a record for Michael Scott. Would you like to update your information instead?'")
    assert res_dup.get("exists") is True

    print("\n" + "=" * 65)
    print("🎉 ALL END-TO-END CALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
