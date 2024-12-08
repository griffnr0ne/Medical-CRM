from flask import Flask, render_template, request
import sqlite3
import datetime
import calendar

app = Flask(__name__)

DATABASE = 'patients.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT,
                    last_name TEXT,
                    dob TEXT,
                    email TEXT,
                    address TEXT,
                    gender TEXT
                  )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    drug_name TEXT,
                    dosage TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    notes TEXT
                  )''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    edit_patient_data = None
    view_patient_data = None
    current_action = None  # can be 'add', 'edit', 'view', or None

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'show_add':
            # Show add patient form
            current_action = 'add'

        elif action == 'add':
            # Add a new patient
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            dob = request.form.get('dob')
            email = request.form.get('email')
            address = request.form.get('address')
            gender = request.form.get('gender')

            conn.execute('INSERT INTO patients (first_name, last_name, dob, email, address, gender) VALUES (?, ?, ?, ?, ?, ?)',
                         (first_name, last_name, dob, email, address, gender))
            conn.commit()
            current_action = None

        elif action == 'cancel_add':
            current_action = None

        elif action == 'load_edit':
            patient_id = request.form.get('patient_id')
            edit_patient_data = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
            current_action = 'edit'

        elif action == 'edit':
            patient_id = request.form.get('patient_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            dob = request.form.get('dob')
            email = request.form.get('email')
            address = request.form.get('address')
            gender = request.form.get('gender')

            conn.execute('UPDATE patients SET first_name=?, last_name=?, dob=?, email=?, address=?, gender=? WHERE id=?',
                         (first_name, last_name, dob, email, address, gender, patient_id))
            conn.commit()

            current_action = None
            edit_patient_data = None

        elif action == 'cancel_edit':
            current_action = None
            edit_patient_data = None

        elif action == 'load_view':
            patient_id = request.form.get('patient_id')
            view_patient_data = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
            current_action = 'view'

        elif action == 'cancel_view':
            current_action = None
            view_patient_data = None

        elif action == 'remove':
            # Remove the selected patient
            patient_id = request.form.get('patient_id')
            conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
            conn.commit()
            # remain in no action mode after removal
            current_action = None

    # Fetch all patients after handling actions
    all_patients = conn.execute("SELECT * FROM patients ORDER BY id ASC").fetchall()
    conn.close()

    return render_template('patients.html',
                           all_patients=all_patients,
                           current_action=current_action,
                           edit_patient=edit_patient_data,
                           view_patient=view_patient_data)


@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    current_action = None  # 'add', 'edit', 'view', 'view_day'
    edit_appointment_data = None
    view_appointment_data = None

    today = datetime.date.today()
    year = today.year
    month = today.month
    selected_day_appointments = []
    selected_day = None

    conn = get_db_connection()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'show_add':
            current_action = 'add'

        elif action == 'add_appointment':
            patient_id = request.form.get('patient_id')
            doctor_name = request.form.get('doctor_name')
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            notes = request.form.get('notes')

            conn.execute('INSERT INTO appointments (patient_id, doctor_name, appointment_date, appointment_time, notes) VALUES (?, ?, ?, ?, ?)',
                         (patient_id, doctor_name, appointment_date, appointment_time, notes))
            conn.commit()
            current_action = None

        elif action == 'cancel_add':
            current_action = None

        elif action == 'load_edit':
            appointment_id = request.form.get('appointment_id')
            edit_appointment_data = conn.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
            current_action = 'edit'

        elif action == 'edit_appointment':
            appointment_id = request.form.get('appointment_id')
            patient_id = request.form.get('patient_id')
            doctor_name = request.form.get('doctor_name')
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            notes = request.form.get('notes')

            conn.execute('UPDATE appointments SET patient_id=?, doctor_name=?, appointment_date=?, appointment_time=?, notes=? WHERE id=?',
                         (patient_id, doctor_name, appointment_date, appointment_time, notes, appointment_id))
            conn.commit()
            current_action = None
            edit_appointment_data = None

        elif action == 'cancel_edit':
            current_action = None
            edit_appointment_data = None

        elif action == 'load_view':
            appointment_id = request.form.get('appointment_id')
            view_appointment_data = conn.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
            current_action = 'view'

        elif action == 'cancel_view':
            current_action = None
            view_appointment_data = None

        elif action == 'prev_month':
            year = int(request.form.get('year'))
            month = int(request.form.get('month'))
            month -= 1
            if month < 1:
                month = 12
                year -= 1

        elif action == 'next_month':
            year = int(request.form.get('year'))
            month = int(request.form.get('month'))
            month += 1
            if month > 12:
                month = 1
                year += 1

        elif action == 'view_day_appointments':
            year = int(request.form.get('year'))
            month = int(request.form.get('month'))
            day = int(request.form.get('day'))
            selected_day = datetime.date(year, month, day)
            selected_day_str = selected_day.isoformat()
            selected_day_appointments = conn.execute('SELECT * FROM appointments WHERE appointment_date = ? ORDER BY appointment_time',
                                                     (selected_day_str,)).fetchall()
            current_action = 'view_day'

        elif action == 'remove':
            # Remove the selected appointment
            appointment_id = request.form.get('appointment_id')
            conn.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
            conn.commit()

            # Check if we removed from daily view or from main list
            remove_year = request.form.get('year')
            remove_month = request.form.get('month')
            remove_day = request.form.get('day')

            if remove_year and remove_month and remove_day:
                # We were in view_day mode
                year = int(remove_year)
                month = int(remove_month)
                day = int(remove_day)
                selected_day = datetime.date(year, month, day)
                selected_day_str = selected_day.isoformat()
                selected_day_appointments = conn.execute('SELECT * FROM appointments WHERE appointment_date = ? ORDER BY appointment_time',
                                                         (selected_day_str,)).fetchall()
                current_action = 'view_day'
            else:
                # Removed from main two-week listing or another mode
                current_action = None

    if request.method == 'GET':
        if current_action not in ['add', 'edit', 'view', 'view_day']:
            # default to showing the calendar if no action
            year = year
            month = month

    start_of_month = datetime.date(year, month, 1)
    _, days_in_month = calendar.monthrange(year, month)
    end_of_month = datetime.date(year, month, days_in_month)

    month_appointments = conn.execute(
        'SELECT appointment_date FROM appointments WHERE appointment_date BETWEEN ? AND ?',
        (start_of_month.isoformat(), end_of_month.isoformat())
    ).fetchall()

    days_with_appointments = set([a['appointment_date'] for a in month_appointments])

    weekday_of_first = start_of_month.weekday()

    two_weeks_later = today + datetime.timedelta(days=14)
    appointments_in_range = conn.execute(
        'SELECT * FROM appointments WHERE appointment_date BETWEEN ? AND ? ORDER BY appointment_date, appointment_time',
        (today.isoformat(), two_weeks_later.isoformat())
    ).fetchall()

    conn.close()

    return render_template('appointments_calendar.html',
                           current_action=current_action,
                           edit_appointment=edit_appointment_data,
                           view_appointment=view_appointment_data,
                           year=year,
                           month=month,
                           days_in_month=days_in_month,
                           days_with_appointments=days_with_appointments,
                           selected_day=selected_day,
                           selected_day_appointments=selected_day_appointments,
                           weekday_of_first=weekday_of_first,
                           appointments_in_range=appointments_in_range)



@app.route('/prescriptions', methods=['GET', 'POST'])
def prescriptions():
    conn = get_db_connection()

    current_action = None # 'view_prescriptions', 'add_prescription', 'edit'
    current_patient_id = None
    current_patient_prescriptions = []
    edit_prescription_data = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'load_prescriptions':
            current_patient_id = request.form.get('patient_id')
            current_action = 'view_prescriptions'

        elif action == 'add_prescription':
            current_action = 'add_prescription'
            current_patient_id = request.form.get('patient_id')

        elif action == 'insert_prescription':
            patient_id = request.form.get('patient_id')
            drug_name = request.form.get('drug_name')
            dosage = request.form.get('dosage')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            notes = request.form.get('notes')

            conn.execute('INSERT INTO prescriptions (patient_id, drug_name, dosage, start_date, end_date, notes) VALUES (?, ?, ?, ?, ?, ?)',
                         (patient_id, drug_name, dosage, start_date, end_date, notes))
            conn.commit()

            current_action = 'view_prescriptions'
            current_patient_id = patient_id

        elif action == 'cancel_add_prescription':
            current_patient_id = request.form.get('patient_id')
            current_action = 'view_prescriptions'

        elif action == 'remove':
            prescription_id = request.form.get('prescription_id')
            current_patient_id = request.form.get('patient_id')

            conn.execute('DELETE FROM prescriptions WHERE id = ?', (prescription_id,))
            conn.commit()

            current_action = 'view_prescriptions'

        elif action == 'load_edit':
            # Load edit form for a prescription
            prescription_id = request.form.get('prescription_id')
            current_patient_id = request.form.get('patient_id')
            edit_prescription_data = conn.execute('SELECT * FROM prescriptions WHERE id = ?', (prescription_id,)).fetchone()
            current_action = 'edit'

        elif action == 'edit_prescription':
            # Update existing prescription
            prescription_id = request.form.get('prescription_id')
            current_patient_id = request.form.get('patient_id')
            drug_name = request.form.get('drug_name')
            dosage = request.form.get('dosage')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            notes = request.form.get('notes')

            conn.execute('UPDATE prescriptions SET drug_name=?, dosage=?, start_date=?, end_date=?, notes=? WHERE id=?',
                         (drug_name, dosage, start_date, end_date, notes, prescription_id))
            conn.commit()

            current_action = 'view_prescriptions'
            edit_prescription_data = None

        elif action == 'cancel_edit':
            # Cancel editing
            current_patient_id = request.form.get('patient_id')
            current_action = 'view_prescriptions'
            edit_prescription_data = None

    all_patients = conn.execute("SELECT * FROM patients ORDER BY id ASC").fetchall()

    if current_action == 'view_prescriptions' and current_patient_id:
        current_patient_prescriptions = conn.execute("SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY id ASC", 
                                                     (current_patient_id,)).fetchall()

    if current_action == 'edit':
        # If we are editing a prescription, pass it to the template as edit_prescription
        return render_template('prescriptions.html',
                               all_patients=all_patients,
                               current_action=current_action,
                               current_patient_id=current_patient_id,
                               current_patient_prescriptions=current_patient_prescriptions,
                               edit_prescription=edit_prescription_data)
    else:
        return render_template('prescriptions.html',
                               all_patients=all_patients,
                               current_action=current_action,
                               current_patient_id=current_patient_id,
                               current_patient_prescriptions=current_patient_prescriptions)




if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
