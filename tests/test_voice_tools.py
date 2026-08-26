import pytest
import json

@pytest.mark.asyncio
async def test_voice_tool_check_existing_patient(client):
    # Seed patient
    await client.post("/patients", json={
        "first_name": "Alice",
        "last_name": "Johnson",
        "date_of_birth": "07/19/1991",
        "sex": "Female",
        "phone_number": "555-444-3333",
        "address_line_1": "789 Pine Rd",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101"
    })

    # Test direct voice tool dispatcher for existing
    resp = await client.post("/api/voice/tools/execute", json={
        "tool": "check_existing_patient",
        "arguments": {"phone_number": "555-444-3333"}
    })
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["exists"] is True
    assert res_data["first_name"] == "Alice"

    # Test non-existing
    resp_new = await client.post("/api/voice/tools/execute", json={
        "tool": "check_existing_patient",
        "arguments": {"phone_number": "555-000-1111"}
    })
    assert resp_new.json()["data"]["exists"] is False

@pytest.mark.asyncio
async def test_voice_tool_register_patient(client):
    resp = await client.post("/api/voice/tools/execute", json={
        "tool": "register_patient",
        "arguments": {
            "first_name": "Robert",
            "last_name": "Smith",
            "date_of_birth": "01/10/1980",
            "sex": "Male",
            "phone_number": "(555) 777-8888",
            "address_line_1": "123 Maple St",
            "city": "Denver",
            "state": "CO",
            "zip_code": "80201",
            "insurance_provider": "Cigna",
            "insurance_member_id": "CIG12345"
        }
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "success"
    assert "patient_id" in data

    # Verify persisted in database
    get_p = await client.get(f"/patients/{data['patient_id']}")
    assert get_p.status_code == 200
    assert get_p.json()["data"]["first_name"] == "Robert"

@pytest.mark.asyncio
async def test_vapi_webhook_tool_call(client):
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "call": {
                "id": "vapi-call-test-1",
                "customer": {"number": "+15552223333"}
            },
            "toolCalls": [
                {
                    "id": "tc_123",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": json.dumps({
                            "first_name": "David",
                            "last_name": "Miller",
                            "date_of_birth": "09/15/1987",
                            "sex": "Male",
                            "phone_number": "555-222-3333",
                            "address_line_1": "555 Boulder Ave",
                            "city": "Boulder",
                            "state": "CO",
                            "zip_code": "80301"
                        })
                    }
                }
            ]
        }
    }

    webhook_resp = await client.post("/api/voice/vapi/webhook", json=vapi_payload)
    assert webhook_resp.status_code == 200
    body = webhook_resp.json()
    assert "results" in body
    assert len(body["results"]) == 1
    assert body["results"][0]["toolCallId"] == "tc_123"
    result_content = json.loads(body["results"][0]["result"])
    assert result_content["status"] == "success"
    assert result_content["first_name"] == "David"

@pytest.mark.asyncio
async def test_vapi_end_of_call_report(client):
    report_payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {
                "id": "vapi-call-test-999",
                "customer": {"number": "+15553334444"}
            },
            "summary": "Patient David Miller registered successfully.",
            "transcript": "Maya: Hello! Caller: Hi I want to register..."
        }
    }

    resp = await client.post("/api/voice/vapi/webhook", json=report_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
