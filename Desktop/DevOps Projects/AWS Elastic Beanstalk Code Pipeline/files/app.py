from flask import Flask, jsonify, request, render_template_string
from datetime import datetime
import uuid

app = Flask(__name__)

# ── In-memory store (replace with RDS in production) ─────────────────────────
appointments = {}

DOCTORS = [
    {"id": "D001", "name": "Dr. Sarah Tremblay", "specialty": "General Practice"},
    {"id": "D002", "name": "Dr. James Okafor",   "specialty": "Cardiology"},
    {"id": "D003", "name": "Dr. Mei-Lin Zhao",   "specialty": "Pediatrics"},
]

# ── HTML UI ──────────────────────────────────────────────────────────────────
UI = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>NovaMed — Appointment Booking</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a1a2e; }
    header {
      background: #0a3d62; color: white;
      padding: 18px 32px; display: flex; align-items: center; gap: 12px;
    }
    header h1 { font-size: 1.4rem; font-weight: 700; }
    header span { font-size: 0.85rem; opacity: 0.7; }
    .badge {
      margin-left: auto; background: #1e88e5;
      padding: 4px 12px; border-radius: 20px; font-size: 0.75rem;
    }
    .container { max-width: 960px; margin: 32px auto; padding: 0 16px; }
    .card {
      background: white; border-radius: 10px; padding: 24px;
      margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .card h2 {
      font-size: 1rem; color: #0a3d62; margin-bottom: 16px;
      border-bottom: 2px solid #e3f2fd; padding-bottom: 8px;
    }
    .form-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
    .form-group { display: flex; flex-direction: column; flex: 1; min-width: 180px; }
    label { font-size: 0.8rem; color: #555; margin-bottom: 4px; font-weight: 600; }
    input, select {
      border: 1px solid #cfd8dc; border-radius: 6px;
      padding: 8px 10px; font-size: 0.9rem; outline: none; transition: border 0.2s;
    }
    input:focus, select:focus { border-color: #1e88e5; }
    button {
      background: #0a3d62; color: white; border: none;
      padding: 10px 24px; border-radius: 6px; cursor: pointer;
      font-size: 0.9rem; font-weight: 600; transition: background 0.2s;
    }
    button:hover { background: #1e88e5; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th { background: #e3f2fd; color: #0a3d62; padding: 10px; text-align: left; font-size: 0.8rem; }
    td { padding: 10px; border-bottom: 1px solid #f0f0f0; }
    tr:hover td { background: #fafafa; }
    .status-confirmed { color: #2e7d32; font-weight: 600; }
    .status-cancelled { color: #c62828; font-weight: 600; }
    #msg { margin-top: 10px; font-size: 0.85rem; color: #2e7d32; min-height: 18px; }
    .env-banner {
      background: #fff3cd; border-left: 4px solid #f59e0b;
      padding: 8px 16px; font-size: 0.82rem; color: #7c5700;
      margin-bottom: 20px; border-radius: 4px;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>NovaMed Clinic Network</h1>
      <span>Patient Appointment Booking System</span>
    </div>
    <div class="badge">ca-central-1</div>
  </header>

  <div class="container">
    <div class="env-banner">
      Environment: <strong id="env-label">Loading...</strong>
      &nbsp;|&nbsp; Version: <strong id="ver-label">-</strong>
    </div>

    <div class="card">
      <h2>Book an Appointment</h2>
      <div class="form-row">
        <div class="form-group">
          <label>Patient Name</label>
          <input id="patient" type="text" placeholder="Full name" />
        </div>
        <div class="form-group">
          <label>Doctor</label>
          <select id="doctor">
            <option value="">Select doctor...</option>
            <option value="D001">Dr. Sarah Tremblay - General Practice</option>
            <option value="D002">Dr. James Okafor - Cardiology</option>
            <option value="D003">Dr. Mei-Lin Zhao - Pediatrics</option>
          </select>
        </div>
        <div class="form-group">
          <label>Date and Time</label>
          <input id="appt-date" type="datetime-local" />
        </div>
        <div class="form-group">
          <label>Reason</label>
          <input id="reason" type="text" placeholder="e.g. Annual checkup" />
        </div>
      </div>
      <button onclick="bookAppointment()">Book Appointment</button>
      <div id="msg"></div>
    </div>

    <div class="card">
      <h2>All Appointments</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Patient</th><th>Doctor</th>
            <th>Date and Time</th><th>Reason</th><th>Status</th>
          </tr>
        </thead>
        <tbody id="appt-table">
          <tr><td colspan="6" style="color:#aaa">Loading...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    async function loadAppointments() {
      const res = await fetch('/api/appointments');
      const data = await res.json();
      const tbody = document.getElementById('appt-table');
      if (!data.appointments.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="color:#aaa">No appointments yet.</td></tr>';
        return;
      }
      tbody.innerHTML = data.appointments.map(a => `
        <tr>
          <td style="font-family:monospace;font-size:0.78rem">${a.id.slice(0,8)}</td>
          <td>${a.patient_name}</td>
          <td>${a.doctor_name}</td>
          <td>${a.appointment_date}</td>
          <td>${a.reason}</td>
          <td class="status-${a.status}">${a.status}</td>
        </tr>`).join('');
    }

    async function loadMeta() {
      const res = await fetch('/api/health');
      const data = await res.json();
      document.getElementById('env-label').textContent = data.environment;
      document.getElementById('ver-label').textContent = data.version;
    }

    async function bookAppointment() {
      const msg = document.getElementById('msg');
      const body = {
        patient_name:     document.getElementById('patient').value,
        doctor_id:        document.getElementById('doctor').value,
        appointment_date: document.getElementById('appt-date').value,
        reason:           document.getElementById('reason').value,
      };
      if (!body.patient_name || !body.doctor_id || !body.appointment_date) {
        msg.style.color = '#c62828';
        msg.textContent = 'Please fill in all required fields.';
        return;
      }
      const res = await fetch('/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (res.ok) {
        msg.style.color = '#2e7d32';
        msg.textContent = 'Appointment booked! ID: ' + data.appointment.id.slice(0,8);
        document.getElementById('patient').value = '';
        document.getElementById('reason').value = '';
        loadAppointments();
      } else {
        msg.style.color = '#c62828';
        msg.textContent = data.error || 'Booking failed.';
      }
    }

    loadMeta();
    loadAppointments();
  </script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(UI)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status":      "healthy",
        "service":     "NovaMed Appointment API",
        "environment": "production",
        "version":     "1.0.0",
        "timestamp":   datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    return jsonify({"doctors": DOCTORS}), 200


@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    return jsonify({"appointments": list(appointments.values())}), 200


@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.get_json()

    patient_name     = data.get('patient_name', '').strip()
    doctor_id        = data.get('doctor_id', '').strip()
    appointment_date = data.get('appointment_date', '').strip()
    reason           = data.get('reason', 'General consultation').strip()

    if not patient_name:
        return jsonify({"error": "patient_name is required"}), 400
    if not doctor_id:
        return jsonify({"error": "doctor_id is required"}), 400
    if not appointment_date:
        return jsonify({"error": "appointment_date is required"}), 400

    doctor = next((d for d in DOCTORS if d['id'] == doctor_id), None)
    if not doctor:
        return jsonify({"error": f"Doctor {doctor_id} not found"}), 404

    appt_id = str(uuid.uuid4())
    appointment = {
        "id":               appt_id,
        "patient_name":     patient_name,
        "doctor_id":        doctor_id,
        "doctor_name":      doctor['name'],
        "specialty":        doctor['specialty'],
        "appointment_date": appointment_date,
        "reason":           reason,
        "status":           "confirmed",
        "created_at":       datetime.utcnow().isoformat() + "Z"
    }
    appointments[appt_id] = appointment
    return jsonify({"message": "Appointment booked", "appointment": appointment}), 201


@app.route('/api/appointments/<appt_id>', methods=['GET'])
def get_appointment(appt_id):
    appt = appointments.get(appt_id)
    if not appt:
        return jsonify({"error": "Appointment not found"}), 404
    return jsonify({"appointment": appt}), 200


@app.route('/api/appointments/<appt_id>', methods=['DELETE'])
def cancel_appointment(appt_id):
    appt = appointments.get(appt_id)
    if not appt:
        return jsonify({"error": "Appointment not found"}), 404
    appointments[appt_id]['status'] = 'cancelled'
    return jsonify({"message": "Appointment cancelled", "appointment": appointments[appt_id]}), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
