// CareCloud Dashboard & Voice Simulator Interaction

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('block'));
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active', 'border-indigo-600', 'text-indigo-600');
        btn.classList.add('border-transparent', 'text-slate-500');
    });

    const activeContent = document.getElementById(tabId);
    if (activeContent) {
        activeContent.classList.remove('hidden');
        activeContent.classList.add('block');
    }

    const activeBtn = document.getElementById(`tab-btn-${tabId.replace('-tab', '')}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'border-indigo-600', 'text-indigo-600');
        activeBtn.classList.remove('border-transparent', 'text-slate-500');
    }
}

function filterPatientsTable() {
    const nameQuery = document.getElementById('searchLastName').value.toLowerCase();
    const phoneQuery = document.getElementById('searchPhone').value.toLowerCase();
    const rows = document.querySelectorAll('.patient-row');

    rows.forEach(row => {
        const name = row.getAttribute('data-name').toLowerCase();
        const phone = row.getAttribute('data-phone').toLowerCase();
        const matchName = !nameQuery || name.includes(nameQuery);
        const matchPhone = !phoneQuery || phone.includes(phoneQuery);

        if (matchName && matchPhone) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function openVoiceSimulatorModal() {
    document.getElementById('voiceModal').classList.remove('hidden');
}

function closeVoiceSimulatorModal() {
    document.getElementById('voiceModal').classList.add('hidden');
}

function openAddPatientModal() {
    openVoiceSimulatorModal();
}

function viewPatientDetails(patient) {
    document.getElementById('detailPatientName').innerText = `${patient.first_name} ${patient.last_name}`;
    document.getElementById('detailPatientId').innerText = `UUID: ${patient.patient_id}`;

    const content = `
        <div class="grid grid-cols-2 gap-2 text-xs">
            <div><strong class="text-slate-500">Date of Birth:</strong> <span class="font-medium text-slate-800">${patient.date_of_birth}</span></div>
            <div><strong class="text-slate-500">Sex:</strong> <span class="font-medium text-slate-800">${patient.sex}</span></div>
            <div><strong class="text-slate-500">Phone:</strong> <span class="font-mono text-slate-800">${patient.phone_number}</span></div>
            <div><strong class="text-slate-500">Email:</strong> <span class="text-slate-800">${patient.email || '—'}</span></div>
            <div class="col-span-2"><strong class="text-slate-500">Address:</strong> <span class="text-slate-800">${patient.address_line_1} ${patient.address_line_2 || ''}, ${patient.city}, ${patient.state} ${patient.zip_code}</span></div>
            <div><strong class="text-slate-500">Insurance:</strong> <span class="text-slate-800">${patient.insurance_provider || '—'} (${patient.insurance_member_id || '—'})</span></div>
            <div><strong class="text-slate-500">Language:</strong> <span class="text-slate-800">${patient.preferred_language || 'English'}</span></div>
            <div class="col-span-2"><strong class="text-slate-500">Emergency Contact:</strong> <span class="text-slate-800">${patient.emergency_contact_name || '—'} ${patient.emergency_contact_phone ? '(' + patient.emergency_contact_phone + ')' : ''}</span></div>
            <div class="col-span-2 border-t pt-2 mt-2 text-slate-400 text-[11px]">
                Created: ${patient.created_at} | Updated: ${patient.updated_at}
            </div>
        </div>
    `;
    document.getElementById('detailContent').innerHTML = content;
    document.getElementById('patientDetailsModal').classList.remove('hidden');
}

function closeDetailsModal() {
    document.getElementById('patientDetailsModal').classList.add('hidden');
}

function quickBookAppointment(patientId, patientName) {
    document.getElementById('apptPatientId').value = patientId;
    document.getElementById('apptPatientName').innerText = `Patient: ${patientName} (${patientId.substring(0, 8)}...)`;
    document.getElementById('bookApptModal').classList.remove('hidden');
}

function closeBookApptModal() {
    document.getElementById('bookApptModal').classList.add('hidden');
}

async function submitAppointmentForm(e) {
    e.preventDefault();
    const patientId = document.getElementById('apptPatientId').value;
    const apptDate = document.getElementById('apptDateTime').value;
    const specialty = document.getElementById('apptSpecialty').value;
    const notes = document.getElementById('apptNotes').value;

    try {
        const resp = await fetch('/appointments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                appointment_date: apptDate,
                doctor_specialty: specialty,
                notes: notes
            })
        });
        const res = await resp.json();
        if (resp.ok) {
            alert('Appointment successfully booked!');
            closeBookApptModal();
            window.location.reload();
        } else {
            alert('Error booking appointment: ' + JSON.stringify(res.error));
        }
    } catch (err) {
        alert('Request failed: ' + err.message);
    }
}

async function softDeletePatient(patientId, name) {
    if (!confirm(`Are you sure you want to soft-delete patient record for ${name}?`)) {
        return;
    }
    try {
        const resp = await fetch(`/patients/${patientId}`, { method: 'DELETE' });
        const res = await resp.json();
        if (resp.ok) {
            alert(`Record for ${name} soft-deleted.`);
            window.location.reload();
        } else {
            alert('Failed to delete: ' + JSON.stringify(res.error));
        }
    } catch (err) {
        alert('Request failed: ' + err.message);
    }
}

async function simulateCheckCaller() {
    const phone = document.getElementById('simPhone').value;
    const out = document.getElementById('simCheckResult');
    if (!phone) {
        alert('Please enter a phone number');
        return;
    }
    out.classList.remove('hidden');
    out.className = 'mt-2 text-xs font-mono p-2 rounded bg-slate-100 text-slate-700';
    out.innerText = 'Checking database...';

    try {
        const resp = await fetch('/api/voice/tools/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tool: 'check_existing_patient',
                arguments: { phone_number: phone }
            })
        });
        const res = await resp.json();
        const data = res.data;
        if (data.exists) {
            out.className = 'mt-2 text-xs font-mono p-2 rounded bg-emerald-50 text-emerald-800 border border-emerald-200';
            out.innerHTML = `✅ <strong>Duplicate Caller Detected!</strong><br>Found: ${data.first_name} ${data.last_name} (DOB: ${data.date_of_birth})<br><em>Maya Prompt: "It looks like we already have a record for ${data.first_name} ${data.last_name}. Would you like to update your information instead?"</em>`;
        } else {
            out.className = 'mt-2 text-xs font-mono p-2 rounded bg-amber-50 text-amber-800 border border-amber-200';
            out.innerHTML = `ℹ️ <strong>New Caller</strong><br>No previous record found for ${phone}. Maya will proceed with new registration.`;
        }
    } catch (e) {
        out.className = 'mt-2 text-xs font-mono p-2 rounded bg-rose-50 text-rose-800';
        out.innerText = 'Error: ' + e.message;
    }
}

function fillSampleData() {
    document.getElementById('sim_first_name').value = 'Emily';
    document.getElementById('sim_last_name').value = 'O\'Connor';
    document.getElementById('sim_dob').value = '04/18/1992';
    document.getElementById('sim_sex').value = 'Female';
    document.getElementById('sim_phone_num').value = '555-432-1098';
    document.getElementById('sim_email').value = 'emily.oc@example.com';
    document.getElementById('sim_addr1').value = '742 Evergreen Terrace';
    document.getElementById('sim_city').value = 'Springfield';
    document.getElementById('sim_state').value = 'IL';
    document.getElementById('sim_zip').value = '62704';
    document.getElementById('sim_ins').value = 'UnitedHealthcare';
}

async function simulateRegisterPatient(e) {
    e.preventDefault();
    const out = document.getElementById('simToolOutput');
    out.classList.remove('hidden');
    out.className = 'mt-3 text-xs font-mono p-2 rounded bg-slate-100 text-slate-700';
    out.innerText = 'Executing voice tool register_patient...';

    const payload = {
        first_name: document.getElementById('sim_first_name').value,
        last_name: document.getElementById('sim_last_name').value,
        date_of_birth: document.getElementById('sim_dob').value,
        sex: document.getElementById('sim_sex').value,
        phone_number: document.getElementById('sim_phone_num').value,
        email: document.getElementById('sim_email').value || null,
        address_line_1: document.getElementById('sim_addr1').value,
        city: document.getElementById('sim_city').value,
        state: document.getElementById('sim_state').value,
        zip_code: document.getElementById('sim_zip').value,
        insurance_provider: document.getElementById('sim_ins').value || null
    };

    try {
        const resp = await fetch('/api/voice/tools/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tool: 'register_patient',
                arguments: payload
            })
        });
        const res = await resp.json();
        const data = res.data;
        if (data.status === 'success') {
            out.className = 'mt-3 text-xs font-mono p-3 rounded bg-emerald-50 text-emerald-800 border border-emerald-200';
            out.innerHTML = `🎉 <strong>Voice Registration Succeeded!</strong><br>Patient ID: ${data.patient_id}<br>Message: ${data.message}<br><em>Maya says: "You're all set, ${data.first_name}!"</em>`;
            setTimeout(() => window.location.reload(), 1500);
        } else {
            out.className = 'mt-3 text-xs font-mono p-3 rounded bg-rose-50 text-rose-800 border border-rose-200';
            out.innerHTML = `⚠️ <strong>Tool Validation Error</strong><br>${data.message || data.error}`;
        }
    } catch (err) {
        out.className = 'mt-3 text-xs font-mono p-3 rounded bg-rose-50 text-rose-800';
        out.innerText = 'Execution error: ' + err.message;
    }
}
