import pytest

SAMPLE_PATIENT = {
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "05/14/1988",
    "sex": "Female",
    "phone_number": "555-123-4567",
    "email": "jane.doe@example.com",
    "address_line_1": "100 Market St",
    "address_line_2": "Apt 4B",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94105",
    "insurance_provider": "Blue Shield of California",
    "insurance_member_id": "BSC987654321",
    "preferred_language": "English",
    "emergency_contact_name": "John Doe",
    "emergency_contact_phone": "555-987-6543"
}

@pytest.mark.asyncio
async def test_create_patient_success(client):
    response = await client.post("/patients", json=SAMPLE_PATIENT)
    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["date_of_birth"] == "05/14/1988"
    assert data["patient_id"] is not None
    assert data["created_at"] is not None

@pytest.mark.asyncio
async def test_list_patients(client):
    # Seed 1 patient
    await client.post("/patients", json=SAMPLE_PATIENT)
    
    response = await client.get("/patients")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1
    assert body["data"][0]["first_name"] == "Jane"

@pytest.mark.asyncio
async def test_get_patient_by_id(client):
    create_resp = await client.post("/patients", json=SAMPLE_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    # Retrieve valid
    response = await client.get(f"/patients/{patient_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["patient_id"] == patient_id

    # Retrieve non-existent
    non_existent = await client.get("/patients/non-existent-uuid")
    assert non_existent.status_code == 404
    assert non_existent.json()["data"] is None
    assert "not found" in non_existent.json()["error"].lower()

@pytest.mark.asyncio
async def test_update_patient_partial(client):
    create_resp = await client.post("/patients", json=SAMPLE_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    # Partial update: change city and zip
    update_resp = await client.put(f"/patients/{patient_id}", json={
        "city": "Oakland",
        "zip_code": "94601"
    })
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["data"]["city"] == "Oakland"
    assert body["data"]["zip_code"] == "94601"
    # Unchanged fields persist
    assert body["data"]["first_name"] == "Jane"

@pytest.mark.asyncio
async def test_soft_delete_patient(client):
    create_resp = await client.post("/patients", json=SAMPLE_PATIENT)
    patient_id = create_resp.json()["data"]["patient_id"]

    # Soft delete
    del_resp = await client.delete(f"/patients/{patient_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["error"] is None
    assert del_resp.json()["data"]["patient_id"] == patient_id

    # Should not appear in standard list
    list_resp = await client.get("/patients")
    assert len(list_resp.json()["data"]) == 0

    # Should return 404 on direct get
    get_resp = await client.get(f"/patients/{patient_id}")
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_query_filters(client):
    await client.post("/patients", json=SAMPLE_PATIENT)
    
    # Filter by matching last_name
    r1 = await client.get("/patients?last_name=Doe")
    assert len(r1.json()["data"]) == 1

    # Filter by non-matching last_name
    r2 = await client.get("/patients?last_name=Smith")
    assert len(r2.json()["data"]) == 0

    # Filter by phone
    r3 = await client.get("/patients?phone_number=5551234567")
    assert len(r3.json()["data"]) == 1

@pytest.mark.asyncio
async def test_duplicate_check_endpoint(client):
    await client.post("/patients", json=SAMPLE_PATIENT)

    # Check existing phone
    dup_resp = await client.get("/patients/check-duplicate?phone_number=555-123-4567")
    assert dup_resp.status_code == 200
    assert dup_resp.json()["data"]["exists"] is True
    assert dup_resp.json()["data"]["patient"]["first_name"] == "Jane"

    # Check new phone
    new_resp = await client.get("/patients/check-duplicate?phone_number=555-999-0000")
    assert new_resp.status_code == 200
    assert new_resp.json()["data"]["exists"] is False
