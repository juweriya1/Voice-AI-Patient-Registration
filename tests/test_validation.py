import pytest
from datetime import date, timedelta

VALID_PAYLOAD = {
    "first_name": "Sarah",
    "last_name": "Connor",
    "date_of_birth": "02/28/1984",
    "sex": "Female",
    "phone_number": "(555) 234-5678",
    "address_line_1": "456 Oak Lane",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701"
}

@pytest.mark.asyncio
async def test_invalid_name_numbers(client):
    payload = VALID_PAYLOAD.copy()
    payload["first_name"] = "Sarah123"
    response = await client.post("/patients", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["data"] is None
    assert "alphabetic" in str(body["error"]).lower()

@pytest.mark.asyncio
async def test_future_date_of_birth(client):
    future_date = (date.today() + timedelta(days=10)).strftime("%m/%d/%Y")
    payload = VALID_PAYLOAD.copy()
    payload["date_of_birth"] = future_date
    response = await client.post("/patients", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "cannot be in the future" in str(body["error"]).lower()

@pytest.mark.asyncio
async def test_invalid_phone_digits(client):
    # Short phone (3 digits)
    payload = VALID_PAYLOAD.copy()
    payload["phone_number"] = "123"
    response = await client.post("/patients", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "10-digit" in str(body["error"]).lower()

@pytest.mark.asyncio
async def test_invalid_state_code(client):
    payload = VALID_PAYLOAD.copy()
    payload["state"] = "ZZ"
    response = await client.post("/patients", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "valid 2-letter u.s. state" in str(body["error"]).lower()

@pytest.mark.asyncio
async def test_invalid_zip_code(client):
    payload = VALID_PAYLOAD.copy()
    payload["zip_code"] = "ABCDE"
    response = await client.post("/patients", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "5-digit" in str(body["error"]).lower()

@pytest.mark.asyncio
async def test_invalid_email(client):
    payload = VALID_PAYLOAD.copy()
    payload["email"] = "not-an-email"
    response = await client.post("/patients", json=payload)
    assert response.status_code == 422
