import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, appointments

@pytest.fixture
def client():
    app.config['TESTING'] = True
    appointments.clear()
    with app.test_client() as client:
        yield client


# ── Health check ──────────────────────────────────────────────────────────────
def test_health_check(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'NovaMed Appointment API'


# ── Doctors ───────────────────────────────────────────────────────────────────
def test_get_doctors(client):
    res = client.get('/api/doctors')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data['doctors']) == 3


# ── Appointments: create ──────────────────────────────────────────────────────
def test_create_appointment(client):
    payload = {
        "patient_name":     "John Smith",
        "doctor_id":        "D001",
        "appointment_date": "2025-09-15T10:00",
        "reason":           "Annual checkup"
    }
    res = client.post('/api/appointments',
                      data=json.dumps(payload),
                      content_type='application/json')
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data['appointment']['patient_name'] == 'John Smith'
    assert data['appointment']['status'] == 'confirmed'


def test_create_appointment_missing_patient(client):
    payload = {"doctor_id": "D001", "appointment_date": "2025-09-15T10:00"}
    res = client.post('/api/appointments',
                      data=json.dumps(payload),
                      content_type='application/json')
    assert res.status_code == 400


def test_create_appointment_invalid_doctor(client):
    payload = {
        "patient_name":     "Jane Doe",
        "doctor_id":        "D999",
        "appointment_date": "2025-09-15T10:00"
    }
    res = client.post('/api/appointments',
                      data=json.dumps(payload),
                      content_type='application/json')
    assert res.status_code == 404


# ── Appointments: list ────────────────────────────────────────────────────────
def test_get_appointments_empty(client):
    res = client.get('/api/appointments')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['appointments'] == []


def test_get_appointments_after_create(client):
    payload = {
        "patient_name":     "Alice Brown",
        "doctor_id":        "D002",
        "appointment_date": "2025-10-01T14:00",
        "reason":           "Cardiology follow-up"
    }
    client.post('/api/appointments',
                data=json.dumps(payload),
                content_type='application/json')
    res = client.get('/api/appointments')
    data = json.loads(res.data)
    assert len(data['appointments']) == 1


# ── Appointments: cancel ──────────────────────────────────────────────────────
def test_cancel_appointment(client):
    payload = {
        "patient_name":     "Bob Martin",
        "doctor_id":        "D003",
        "appointment_date": "2025-11-05T09:00",
        "reason":           "Pediatric checkup"
    }
    create_res = client.post('/api/appointments',
                             data=json.dumps(payload),
                             content_type='application/json')
    appt_id = json.loads(create_res.data)['appointment']['id']

    cancel_res = client.delete(f'/api/appointments/{appt_id}')
    assert cancel_res.status_code == 200
    data = json.loads(cancel_res.data)
    assert data['appointment']['status'] == 'cancelled'


def test_cancel_nonexistent_appointment(client):
    res = client.delete('/api/appointments/nonexistent-id')
    assert res.status_code == 404


# ── UI ────────────────────────────────────────────────────────────────────────
def test_ui_loads(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'NovaMed' in res.data
