from flask import render_template, redirect, url_for, flash, request, Blueprint,  session
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
from datetime import datetime, timedelta, date, time as dtime
import re
from sqlalchemy import func
from sqlalchemy import and_
from init import db
from models import User, Department, Appointment, Treatment, DoctorAvailability
from forms import LoginForm, PatientRegistrationForm, AddDoctorForm
from werkzeug.security import check_password_hash
from wtforms.validators import Optional



main = Blueprint('main', __name__)

# Role requirement
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
            user_role = (getattr(current_user, 'user_role', '') or '').strip().lower()
            if user_role != (role or '').strip().lower():
                return redirect(url_for('main.dashboard_redirect'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Public routes
@main.route('/')
@main.route('/home')
def home():
    return render_template('home.html')


# Patient registeration
@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))

    form = PatientRegistrationForm()  

    if request.method == 'POST' and form.validate():
        full_address = ", ".join(filter(None, [
            (form.address.data or "").strip(),
            (f"PIN {form.pincode.data.strip()}" if form.pincode.data else None),
            (form.city.data or "").strip(),
            (form.state.data or "").strip(),
            (form.country.data or "").strip(),
        ]))

        new_patient = User(
            first_name=(form.first_name.data or "").strip(),
            last_name=(form.last_name.data or "").strip() if form.last_name.data else None,
            user_name=(form.user_name.data or "").strip(),
            email_address=(form.email_address.data or "").strip().lower(),
            gender=form.gender.data or "Not specified",
            dob=form.dob.data if form.dob.data else None,
            contact_number=(form.contact_number.data or "").strip(),
            address=full_address if full_address else (form.address.data or "").strip(),
            user_role='patient',
            nationality=None,
            availability=None,
        )

        try:
            new_patient.set_password(form.password.data)
            db.session.add(new_patient)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('main.login', role='patient', registered=1))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while registering: {str(e)}", "danger")

    return render_template('register.html', title='Patient Registration', form=form)


# Login route
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))

    form = LoginForm()
    preselected_role = (request.args.get('role') or '').strip().lower()

    if preselected_role in ['admin', 'doctor', 'patient']:
        form.login_as.data = preselected_role

    if request.args.get('registered') == '1':
        flash('Successfully registered. You may now login as a patient.', 'success')

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password', '')
        selected_role = (request.form.get('login_as', preselected_role) or '').strip().lower()

        user = User.query.filter(db.func.lower(User.email_address) == email).first()

        if not user or not user.check_password(password):
            return render_template('login.html', form=form, wrong_credentials=True, preselected_role=preselected_role)

        if selected_role != (user.user_role or '').lower():
            flash(f'⚠️ Please login as {user.user_role.capitalize()}.', 'warning')
            return render_template('login.html', form=form, preselected_role=preselected_role)

        session.pop('_flashes', None)
        login_user(user, remember='remember_me' in request.form)
        flash(f'Welcome {user.user_name}! Logged in as {user.user_role.capitalize()}.', 'success')

        if user.user_role == 'patient':
            return redirect(url_for('main.patient_dashboard'))
        elif user.user_role == 'doctor':
            return redirect(url_for('main.doctor_dashboard'))
        elif user.user_role == 'admin':
            return redirect(url_for('main.admin_dashboard'))

        logout_user()
        flash('Unknown role. Logging out for safety.', 'danger')
        return redirect(url_for('main.home'))

    return render_template('login.html', form=form, preselected_role=preselected_role)


# Logout route
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


# Dashboard redirect
@main.route('/dashboard')
@login_required
def dashboard_redirect():
    role = (current_user.user_role or '').strip().lower()
    if role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif role == 'doctor':
        return redirect(url_for('main.doctor_dashboard'))
    elif role == 'patient':
        return redirect(url_for('main.patient_dashboard'))
    else:
        flash('Unknown user role. Logging out.', 'danger')
        logout_user()
        return redirect(url_for('main.home'))


# Admin Section (Main dashboard)
@main.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    total_doctors = User.query.filter_by(user_role='doctor').count()
    total_patients = User.query.filter_by(user_role='patient').count()
    total_appointments = Appointment.query.filter(Appointment.patient_id.isnot(None)).count()
    total_treatments = Treatment.query.count()

    return render_template(
        'admin_dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_treatments=total_treatments,
        active='dashboard'
    )

# Admin Section (Doctor page)
@main.route('/admin/doctors')
@login_required
@role_required('admin')
def admin_doctors():
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'name')
    query = User.query.filter_by(user_role='doctor')

    if search:
        if filter_type == 'specialization':
            query = query.join(Department).filter(Department.dept_name.ilike(f"%{search}%"))
        else:
            query = query.filter(
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.user_name.ilike(f"%{search}%"))
            )

    doctors = query.all()
    return render_template('admin_doctors.html', doctors=doctors, search=search, filter_type=filter_type, active='doctors')

# Admin Section (Patient page)
@main.route('/admin/patients')
@login_required
@role_required('admin')
def admin_patients():
    search = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'name')
    query = User.query.filter_by(user_role='patient')

    if search:
        if filter_type == 'id':
            query = query.filter(User.user_id == search)
        elif filter_type == 'contact':
            query = query.filter(User.contact_number.ilike(f"%{search}%"))
        else:
            query = query.filter(User.user_name.ilike(f"%{search}%"))

    patients = query.all()
    return render_template('admin_patients.html', patients=patients, search=search, filter_type=filter_type, active='patients')

# Admin Section (Appointment page)
@main.route("/admin/appointments", methods=["GET"])
@login_required
@role_required("admin")
def admin_appointments():
    from datetime import datetime

    filter_type = request.args.get("filter", "upcoming")
    status_filter = request.args.get("status", "all")
    today = datetime.now().date()

    query = Appointment.query

    if filter_type == "past":
        query = query.filter(Appointment.appointment_date < today)
    elif filter_type == "today":
        query = query.filter(Appointment.appointment_date == today)
    else:
        query = query.filter(Appointment.appointment_date >= today)

    if status_filter != "all":
        query = query.filter(Appointment.appointment_status == status_filter)

    appointments = query.filter(Appointment.patient_id.isnot(None)).order_by(
        Appointment.appointment_date.desc()
    ).all()

    return render_template(
        "admin_appointments.html",
        appointments=appointments,
        selected_filter=filter_type,
        selected_status=status_filter
    )

# Admin Section (Treatments Page)
@main.route("/admin/treatments")
@login_required
@role_required("admin")
def admin_treatments():
    treatments = Treatment.query.filter(
        Treatment.patient_id.isnot(None),
        Treatment.doctor_id.isnot(None)
    ).order_by(Treatment.created_on.desc()).all()
    print("✅ Admin Treatments route reached")
    print("Found", len(treatments), "treatments")
    return render_template("admin_treatments.html", treatments=treatments)

# Admin Section (Profile Page)
@main.route('/admin/profile')
@login_required
@role_required('admin')
def admin_profile():
    return render_template('admin_profile.html', admin=current_user, active='profile')

# Admin Section (Add new Doctor)
@main.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_doctor():
    form = AddDoctorForm()
    departments = Department.query.order_by(Department.dept_name).all()
    form.department_ref.choices = [(int(d.dept_id), d.dept_name) for d in departments]

    if request.method == 'POST' and form.validate():
        pwd = (form.password.data or "")
        if len(pwd) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('add_doctor.html', form=form, active='add_doctor')

        if (form.password.data or "") != (form.confirm_password.data or ""):
            flash("Passwords do not match. Please re-enter.", "danger")
            return render_template('add_doctor.html', form=form, active='add_doctor')

        raw_contact = (form.contact_number.data or "").strip()
        contact_digits = re.sub(r'\D', '', raw_contact)

        entered_username = (form.user_name.data or "").strip().lower()
        if entered_username:
            username_to_use = entered_username
        else:
            first = (form.first_name.data or "").strip().lower()
            suffix = (contact_digits[-2:] if len(contact_digits) >= 2 else '01')
            base_username = f"{first}_{suffix}" if first else f"doc_{suffix}"
            username_to_use = base_username
            
        counter = 0
        while User.query.filter(db.func.lower(User.user_name) == username_to_use.lower()).first():
            counter += 1
            username_to_use = f"{username_to_use}_{counter}"


        email_norm = (form.email_address.data or "").strip().lower()
        by_email = User.query.filter(db.func.lower(User.email_address) == email_norm).first()
        if by_email:
            flash("That email is already registered.", "danger")
            return render_template('add_doctor.html', form=form, active='add_doctor')

        country_code = (form.country_code.data or "").strip()
        combined_contact = f"{country_code}{contact_digits}" if country_code else contact_digits

        dob_value = form.dob.data if form.dob.data else None
        full_address = ", ".join(filter(None, [
            (form.address_line1.data or "").strip(),
            (form.address_line2.data or "").strip(),
            (form.city.data or "").strip(),
            (form.state.data or "").strip(),
            (form.country.data or "").strip(),
            (f"PIN {form.pincode.data.strip()}" if form.pincode.data else None)
        ]))

        new_doctor = User(
            first_name=form.first_name.data,
            middle_name=form.middle_name.data if form.middle_name.data else None,
            last_name=form.last_name.data,
            user_name=username_to_use,
            email_address=email_norm,
            gender=form.gender.data,
            dob=dob_value,
            contact_number=combined_contact,
            address=full_address,
            department_ref=int(form.department_ref.data) if form.department_ref.data else None,
            doctor_qualification=form.qualification.data,
            doctor_experience=form.doctor_experience.data or 0,
            user_role='doctor'
        )
        new_doctor.set_password(form.password.data)
        db.session.add(new_doctor)
        db.session.commit()

        flash(f"Doctor '{new_doctor.first_name or new_doctor.user_name}' added successfully!", "success")
        return redirect(url_for('main.admin_doctors'))

    return render_template('add_doctor.html', form=form, active='add_doctor')

# Admin Section (Edit Doctor's details)
@main.route('/admin/manage_doctor/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_doctor(id):
    doctor = User.query.get_or_404(id)
    if doctor.user_role != 'doctor':
        flash('This user is not a doctor.', 'danger')
        return redirect(url_for('main.admin_doctors'))

    from forms import DoctorUpdateForm
    form = DoctorUpdateForm(obj=doctor)
    departments = Department.query.order_by(Department.dept_name).all()
    form.department_ref.choices = [(d.dept_id, d.dept_name) for d in departments]

    if request.method == "GET":
        form.department_ref.data = doctor.department_ref
        form.qualification.data = doctor.doctor_qualification

    if request.method == "POST" and form.validate():
        doctor.first_name = form.first_name.data
        doctor.middle_name = form.middle_name.data
        doctor.last_name = form.last_name.data
        doctor.email_address = form.email_address.data.strip().lower()
        doctor.contact_number = form.contact_number.data
        doctor.doctor_experience = form.doctor_experience.data
        doctor.department_ref = int(form.department_ref.data) if form.department_ref.data else None
        doctor.doctor_qualification = form.qualification.data

        db.session.commit()
        flash(f"Doctor '{doctor.first_name or doctor.user_name}' updated successfully!", "success")
        return redirect(url_for('main.admin_doctors'))

    return render_template('manage_doctor.html', form=form, doctor=doctor, active='doctors')

# Admin Section (View doctor profile page)
@main.route('/admin/doctor_profile/<int:doctor_id>')
@login_required
@role_required('admin')
def view_doctor_profile(doctor_id):
    doctor = User.query.get_or_404(doctor_id)

    if doctor.user_role != 'doctor':
        flash('This user is not a doctor.', 'danger')
        return redirect(url_for('main.admin_doctors'))

    return render_template(
        'admin_doctor_profile.html', 
        doctor=doctor,
        active='doctors'
    )

# Admin Section (Blacklist doctor route)
@main.route('/admin/toggle_blacklist/<int:user_id>', methods = ['GET', 'POST'])
@login_required
@role_required('admin')
def toggle_blacklist(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_role == 'admin':
        flash('You cannot blacklist another admin.', 'danger')
        return redirect(request.referrer or url_for('main.admin_doctors'))
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    flash(f"{user.user_name} has been {'blacklisted' if user.is_blacklisted else 'unblocked'}.", 'info')
    return redirect(request.referrer or url_for('main.admin_doctors'))

# Admin Section (Remove patient route)
@main.route('/admin/remove_patient/<int:user_id>', methods=['POST', 'GET'])
@login_required
@role_required('admin')
def remove_patient(user_id):

    user = User.query.get_or_404(user_id)

    if user.user_role != 'patient':
        flash('Only patient accounts can be removed.', 'danger')
        return redirect(url_for('main.admin_patients'))

    treatments = Treatment.query.filter_by(patient_id=user_id).all()
    for t in treatments:
        db.session.delete(t)

    appointments = Appointment.query.filter_by(patient_id=user_id).all()
    for a in appointments:
        db.session.delete(a)

    db.session.delete(user)
    db.session.commit()

    flash(f"Patient '{user.first_name} {user.last_name or ''}' removed successfully.", "success")
    return redirect(url_for('main.admin_patients'))

# Admin Section (View patient profile)
@main.route('/admin/patient_profile/<int:patient_id>')
@login_required
@role_required('admin')
def view_patient_profile(patient_id):
    patient = User.query.get_or_404(patient_id)
    if patient.user_role != 'patient':
        flash('This user is not a patient.', 'danger')
        return redirect(url_for('main.admin_patients'))
    return render_template('patient_profile.html', patient=patient, active='patients')

# Admin Section (Edit patient details)
@main.route('/admin/manage_patient/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_patient(id):
    patient = User.query.get_or_404(id)
    if patient.user_role != 'patient':
        flash('This user is not a patient.', 'danger')
        return redirect(url_for('main.admin_patients'))

    from forms import PatientRegistrationForm
    form = PatientRegistrationForm(obj=patient)
    form.obj = patient
    form.password.validators = [Optional()]
    form.confirm_password.validators = [Optional()]

    if request.method == "GET":
        form.emergency_contact_name.data = patient.emergency_name
        form.emergency_contact_relationship.data = patient.emergency_relation
        form.emergency_contact_number.data = patient.emergency_contact

    if request.method == "POST" and form.validate():
        patient.first_name = form.first_name.data
        patient.last_name = form.last_name.data
        patient.user_name = form.user_name.data
        patient.email_address = form.email_address.data
        patient.gender = form.gender.data
        patient.dob = form.dob.data
        patient.height = float(form.height.data) if form.height.data else None
        patient.weight = float(form.weight.data) if form.weight.data else None
        patient.marital_status = form.marital_status.data
        patient.medications = form.medications.data
        patient.emergency_name = form.emergency_contact_name.data
        patient.emergency_relation = form.emergency_contact_relationship.data
        patient.emergency_contact = form.emergency_contact_number.data
        patient.contact_number = form.contact_number.data
        patient.address = form.address.data
        patient.address_line2 = form.address_line2.data
        patient.pincode = form.pincode.data
        patient.city = form.city.data
        patient.state = form.state.data
        patient.country = form.country.data
        patient.nationality = form.nationality.data

        db.session.commit()
        flash(f"Patient '{patient.first_name}' details updated successfully!", "success")
        return redirect(url_for('main.view_patient_profile', patient_id=patient.user_id))

    return render_template('manage_patient.html', form=form, patient=patient, active='patients')


# Doctor Section (Main Dashboard)
@main.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.user_role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    doctor_id = current_user.user_id
    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    todays_count = (
        db.session.query(func.count(Appointment.appointment_id))
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.appointment_status.in_(["Booked", "Confirmed"]),
            Appointment.patient_id.isnot(None)
        )
        .scalar()
    )

    week_count = (
        db.session.query(func.count(Appointment.appointment_id))
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= week_later,
            Appointment.appointment_status.in_(["Booked", "Confirmed"]),
            Appointment.patient_id.isnot(None)
        )
        .scalar()
    )

    assigned_patient_ids = (
        db.session.query(Appointment.patient_id)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id.isnot(None),
            Appointment.appointment_status != "Cancelled"
        )
        .distinct()
        .all()
    )

    patient_ids = [p[0] for p in assigned_patient_ids if p[0] is not None]

    assigned_patients = (
        User.query.filter(User.user_id.in_(patient_ids)).all()
        if patient_ids else []
    )

    upcoming_appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= week_later,
            Appointment.patient_id.isnot(None),
            Appointment.appointment_status.in_(["Booked", "Confirmed"])
        )
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
        .all()
    )

    return render_template(
        'doctor_dashboard.html',
        todays_count=todays_count,
        week_count=week_count,
        assigned_patients=assigned_patients,
        upcoming_appointments=upcoming_appointments,
    )

# Doctor Section (Appointment Page)
@main.route("/doctor/appointment/<int:appointment_id>/action", methods=["POST"])
@login_required
@role_required("doctor")
def doctor_manage_appointment(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    action = request.form.get("action")

    if appt.doctor_id != current_user.user_id:
        flash("Access denied.", "danger")
        return redirect(url_for("main.doctor_dashboard"))

    if action == "complete":

        if not appt.treatment_id:
            flash("⚠️ You haven't added any treatment yet! Please add treatment before marking this appointment as completed.", "warning")
            
            return redirect(url_for(
                "main.doctor_patient_profile",
                patient_id=appt.patient_id
            ))

        appt.appointment_status = "Completed"
        db.session.commit()
        flash("✅ Appointment marked as completed.", "success")

    elif action == "cancel":
        appt.appointment_status = "Cancelled"
        db.session.commit()
        flash("❌ Appointment cancelled.", "danger")

    else:
        flash("Invalid action.", "warning")

    return redirect(url_for("main.doctor_dashboard"))


# Doctor Section (Appointments page with filters)
@main.route('/doctor/appointments')
@login_required
@role_required("doctor")
def doctor_appointments():
    doctor_id = current_user.user_id
    filter_option = request.args.get("filter", "upcoming")
    today = date.today()

    base_query = (
        db.session.query(Appointment)
        .join(User, Appointment.patient_id == User.user_id)  
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id.isnot(None)
        )
    )

    if filter_option == "today":
        appointments = (
            base_query
            .filter(Appointment.appointment_date == today)
            .order_by(Appointment.appointment_date.asc(),
                      Appointment.appointment_time.asc())
            .all()
        )

    elif filter_option == "upcoming":
        appointments = (
            base_query
            .filter(Appointment.appointment_date >= today)
            .order_by(Appointment.appointment_date.asc(),
                      Appointment.appointment_time.asc())
            .all()
        )

    elif filter_option == "past":
        appointments = (
            base_query
            .filter(Appointment.appointment_date < today)
            .order_by(Appointment.appointment_date.desc(),
                      Appointment.appointment_time.desc())
            .all()
        )

    elif filter_option == "all":
        appointments = (
            base_query
            .order_by(Appointment.appointment_date.desc(),
                      Appointment.appointment_time.desc())
            .all()
        )

    else:
        appointments = (
            base_query
            .order_by(Appointment.appointment_date.asc(),
                      Appointment.appointment_time.asc())
            .all()
        )

    return render_template(
        "doctor_appointments.html",
        appointments=appointments,
        current_filter=filter_option
    )


@main.route('/doctor/patients')
@login_required
@role_required('doctor')
def doctor_patients():
    doctor_id = current_user.user_id
    search_query = request.args.get("search", "").strip().lower()

    # Fetch distinct patient IDs assigned to this doctor
    assigned_patient_ids = (
        db.session.query(Appointment.patient_id)
        .filter(Appointment.doctor_id == doctor_id)
        .filter(Appointment.patient_id.isnot(None))
        .distinct()
        .all()
    )

    patient_ids = [pid[0] for pid in assigned_patient_ids if pid[0] is not None]

    patients = []
    if patient_ids:
        patients = (
            User.query
            .filter(User.user_id.in_(patient_ids))
            .filter(User.user_role == 'patient')
        )

        if search_query:
            patients = patients.filter(
                db.or_(
                    db.func.lower(User.first_name).like(search_query + '%'),
                    db.func.lower(User.last_name).like(search_query + '%'),
                    db.func.lower(User.email_address).like(search_query + '%')
                )
            )

        patients = patients.order_by(User.first_name).all()

    return render_template('doctor_patients.html', patients=patients)



# Doctor Section (Patient Profile Page)
@main.route("/doctor/patient/<int:patient_id>")
@login_required
@role_required("doctor")
def doctor_patient_profile(patient_id):
    doctor_id = current_user.user_id

    patient = User.query.get_or_404(patient_id)

    appointment_id = request.args.get("appointment_id")
    focused_appointment = None

    if appointment_id:
        focused_appointment = Appointment.query.get(int(appointment_id))

        if (
            not focused_appointment or
            focused_appointment.doctor_id != doctor_id or
            focused_appointment.patient_id != patient_id
        ):
            flash("⚠️ Invalid appointment reference.", "danger")
            return redirect(url_for("main.doctor_patient_profile", patient_id=patient_id))

    appointments = (
        Appointment.query
        .filter_by(doctor_id=doctor_id, patient_id=patient_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )

    treatments = (
        Treatment.query
        .filter_by(doctor_id=doctor_id, patient_id=patient_id)
        .order_by(Treatment.created_on.desc())
        .all()
    )

    today = datetime.now().date()

    next_active_appointment = (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient_id,
            Appointment.appointment_status.in_(["Booked", "Confirmed"]),
            Appointment.appointment_date >= today,      
            Appointment.patient_id.isnot(None)          
        )
        .order_by(
            Appointment.appointment_date.asc(),
            Appointment.appointment_time.asc()
        )
        .first()
    )

    return render_template(
        "doctor_patient_profile.html",
        patient=patient,
        appointments=appointments,
        treatments=treatments,
        focused_appointment=focused_appointment,
        next_active_appointment=next_active_appointment, 
    )

# Doctor Section (Add treatment for patient)
@main.route('/doctor/patient/<int:patient_id>/add_treatment', methods=['POST'])
@login_required
@role_required('doctor')
def add_treatment_for_patient(patient_id):
    patient = User.query.get_or_404(patient_id)

    appointment_id = request.form.get("appointment_id")
    if not appointment_id:
        flash("No appointment selected for this treatment.", "danger")
        return redirect(url_for("main.doctor_patient_profile", patient_id=patient_id))

    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("main.doctor_patient_profile", patient_id=patient_id))

    if appointment.doctor_id != current_user.user_id:
        flash("Access denied.", "danger")
        return redirect(url_for("main.doctor_patient_profile", patient_id=patient_id))

    t_name = request.form.get('treatment_name', '').strip()
    t_diag = request.form.get('diagnosis', '').strip()
    t_pres = request.form.get('prescription', '').strip()
    t_notes = request.form.get('notes', '').strip()

    new_treatment = Treatment(
        patient_id=patient_id,
        doctor_id=current_user.user_id,
        treatment_name=t_name,
        diagnosis=t_diag,
        prescription=t_pres,
        doctor_notes=t_notes            
    )

    db.session.add(new_treatment)
    db.session.flush()           

    appointment.treatment_id = new_treatment.treatment_id
    appointment.appointment_status = "Completed"

    db.session.commit()

    flash("Treatment added and appointment marked as completed.", "success")
    return redirect(url_for('main.doctor_patient_profile', patient_id=patient_id))


# Doctor Section (Availability page)
@main.route("/doctor/availability")
@login_required
@role_required("doctor")
def doctor_availability():
    today = date.today()
    next_7_days = []
    for i in range(7):
        d = today + timedelta(days=i)
        next_7_days.append({"date": d.strftime("%Y-%m-%d"), "weekday": d.strftime("%A")})

    availabilities = DoctorAvailability.query.filter_by(doctor_id=current_user.user_id).all()
    availability_data = {}
    for a in availabilities:
        availability_data[a.date] = {
            "start": a.start_time or "",
            "end": a.end_time or "",
            "available": bool(a.available)
        }

    return render_template(
        "doctor_availability.html",
        next_7_days=next_7_days,
        availability=availability_data
    )


# Doctor Section (Update Availability route)
@main.route("/doctor/availability/update", methods=["POST"])
@login_required
@role_required("doctor")
def update_doctor_availability():
    today = date.today()

    for i in range(7):
        target_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        start_time = request.form.get(f"start_time_{i+1}") or None
        end_time = request.form.get(f"end_time_{i+1}") or None
        available_value = request.form.get(f"available_{i+1}")  # yes or no
        available = True if available_value == "yes" else False

        existing = DoctorAvailability.query.filter_by(
            doctor_id=current_user.user_id, date=target_date
        ).first()

        if existing:
            existing.start_time = start_time
            existing.end_time = end_time
            existing.available = available
        else:
            new_entry = DoctorAvailability(
                doctor_id=current_user.user_id,
                date=target_date,
                start_time=start_time,
                end_time=end_time,
                available=available
            )
            db.session.add(new_entry)

    db.session.commit()
    flash("✅ Availability updated successfully!", "success")
    return redirect(url_for("main.doctor_availability"))

def generate_time_slots(start_str, end_str, slot_minutes=30):
    """Generate 30-min slots between start and end time."""
    try:
        start = datetime.strptime(start_str, "%H:%M")
        end = datetime.strptime(end_str, "%H:%M")
    except:
        return []

    slots = []
    while start < end:
        slot_start = start.strftime("%H:%M")
        slot_end = (start + timedelta(minutes=slot_minutes)).strftime("%H:%M")
        slots.append({"start": slot_start, "end": slot_end})
        start += timedelta(minutes=slot_minutes)

    return slots


# Doctor Section (Self Profile Page)
@main.route('/doctor/profile')
@login_required
@role_required('doctor')
def doctor_profile():
    doctor = current_user
    return render_template('doctor_profile.html', doctor=doctor, active='profile')


# Patient Section (Main Dashboard)
@main.route("/patient/dashboard")
@login_required
@role_required("patient")
def patient_dashboard():
    from datetime import datetime, date

    patient_id = current_user.user_id
    today = date.today()

    appointments = (
        Appointment.query
        .filter(Appointment.patient_id == patient_id, Appointment.appointment_date >= today)
        .order_by(Appointment.appointment_date.asc())
        .all()
    )

    upcoming_appointments = []
    for appt in appointments:
        doctor = User.query.get(appt.doctor_id)
        dept = doctor.department if doctor and hasattr(doctor, "department") else None

        appt_date = appt.appointment_date
        if isinstance(appt_date, str):
            try:
                appt_date = datetime.strptime(appt_date, "%Y-%m-%d").date()
            except:
                appt_date = None

        appt_time = appt.appointment_time
        if isinstance(appt_time, str):
            try:
                appt_time = datetime.strptime(appt_time, "%H:%M").time()
            except:
                appt_time = None

        upcoming_appointments.append({
            "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else "Unknown Doctor",
            "department": dept.dept_name if dept else "General",
            "appointment_date": appt_date,
            "appointment_time": appt_time,
            "status": appt.appointment_status
        })

    departments = Department.query.order_by(Department.dept_name).all()

    return render_template(
        "patient_dashboard.html",
        upcoming_appointments=upcoming_appointments,
        departments=departments
    )


# Patient Section (Booking page)
@main.route('/patient/book', methods=['GET'])
@login_required
@role_required('patient')
def patient_book_page():
    doctors = User.query.filter_by(user_role='doctor').all()
    return render_template('patient_book.html', doctors=doctors, active='book')

# Patient Section (View doctor's availability)
@main.route('/patient/book/doctor/<int:doctor_id>', methods=['GET'])
@login_required
@role_required('patient')
def view_doctor_availability(doctor_id):
    from datetime import date, timedelta

    doctor = User.query.get_or_404(doctor_id)

    next_7_days = []
    for i in range(7):
        d = date.today() + timedelta(days=i)
        next_7_days.append({
            "date": d.strftime("%Y-%m-%d"),
            "weekday": d.strftime("%A")
        })

    # See doctor availability
    availability = {
        a.date: {
            "start": a.start_time,
            "end": a.end_time,
            "available": a.available
        }
        for a in DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    }

    # 30 minute slots for each date
    final_schedule = {}
    for day in next_7_days:
        date_key = day["date"]
        info = availability.get(date_key)

        if not info or not info["available"]:
            final_schedule[date_key] = []
            continue

        slots = generate_time_slots(info["start"], info["end"], slot_minutes=30)

        # Filter out already booked slots
        booked_times = [
            a.appointment_time
            for a in Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=date.fromisoformat(date_key)
            ).all()
        ]

        for s in slots:
            s["is_booked"] = s["start"] in booked_times

        final_schedule[date_key] = slots

    return render_template(
        "patient_doctor_availability.html",
        doctor=doctor,
        next_7_days=next_7_days,
        final_schedule=final_schedule,
        availability=availability,
        active='book'
    )

# Patient Section: Book Appointment
@main.route('/patient/book/<int:doctor_id>', methods=['POST'], endpoint='patient_book')
@login_required
@role_required('patient')
def patient_book(doctor_id):
    from datetime import datetime

    doctor = User.query.get_or_404(doctor_id)

    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')

    if not appointment_date or not appointment_time:
        flash("Please select both date and time.", "warning")
        return redirect(url_for('main.view_doctor_availability', doctor_id=doctor_id))

    try:
        appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(url_for('main.view_doctor_availability', doctor_id=doctor_id))

    existing = Appointment.query.filter_by(
        doctor_id=doctor_id,
        patient_id=current_user.user_id,
        appointment_date=appointment_date_obj,
        appointment_time=appointment_time
    ).first()

    if existing:
        flash("⚠️ This time slot is already booked. Choose another.", "warning")
        return redirect(url_for('main.view_doctor_availability', doctor_id=doctor_id))

    new_appt = Appointment(
        doctor_id=doctor_id,
        patient_id=current_user.user_id,
        appointment_date=appointment_date_obj,
        appointment_time=appointment_time,
        appointment_status='Booked',
        created_on=datetime.utcnow() 
    )
    
    db.session.add(new_appt)
    db.session.commit()

    flash("✅ Appointment booked successfully!", "success")
    return redirect(url_for('main.patient_appointments'))

# Patient Section (My appointments page)
@main.route('/patient/appointments')
@login_required
@role_required('patient')
def patient_appointments():
    appointments = Appointment.query.filter_by(patient_id=current_user.user_id).order_by(Appointment.appointment_date.asc()).all()
    return render_template('patient_appointments.html', appointments=appointments, active='appointments')

# Patient Section (Cancel appointment route)
@main.route('/patient/appointments/cancel/<int:appointment_id>', methods=['POST'])
@login_required
@role_required('patient')
def cancel_appointment(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.patient_id != current_user.user_id:
        flash("Access denied — you can only cancel your own appointments.", "danger")
        return redirect(url_for('main.patient_appointments'))

    appt.appointment_status = 'Cancelled'
    db.session.commit()
    flash("🗓️ Your appointment has been cancelled.", "success")
    return redirect(url_for('main.patient_appointments'))

# Patient Section (Treatment History)
@main.route('/patient/history')
@login_required
@role_required('patient')
def patient_history():
    appointments = (
        Appointment.query
        .filter_by(patient_id=current_user.user_id)
        .filter(Appointment.treatment_id.isnot(None))
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    history_data = []
    for appt in appointments:
        treatment = appt.treatment
        if treatment:
            history_data.append({
                'doctor': appt.doctor,
                'date': appt.appointment_date,
                'time': appt.appointment_time,
                'status': appt.appointment_status,
                'treatment': treatment.treatment_name,
                'diagnosis': treatment.diagnosis,
                'prescription': treatment.prescription,
                'doctor_notes': treatment.doctor_notes,
                'created_on': treatment.created_on
            })

    return render_template('patient_history.html', history=history_data)

# Patient Section (View Self Profile)
@main.route('/patient/profile')
@login_required
@role_required('patient')
def patient_self_profile():
    patient = current_user
    return render_template('patient_self_profile.html', patient=patient, active='profile')

# Patient Section (Edit Self Profile)
@main.route('/patient/edit_profile', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def patient_edit_profile():
    patient = current_user
    from forms import PatientRegistrationForm

    form = PatientRegistrationForm(obj=patient)
    form.obj = patient 

    form.password.validators = [Optional()]
    form.confirm_password.validators = [Optional()]

    if request.method == "GET":
        form.emergency_contact_name.data = patient.emergency_name
        form.emergency_contact_relationship.data = patient.emergency_relation
        form.emergency_contact_number.data = patient.emergency_contact

    if form.validate_on_submit():
        patient.first_name = form.first_name.data
        patient.last_name = form.last_name.data
        patient.user_name = form.user_name.data
        patient.email_address = form.email_address.data
        patient.gender = form.gender.data
        patient.dob = form.dob.data
        
        patient.height = float(form.height.data) if form.height.data else None
        patient.weight = float(form.weight.data) if form.weight.data else None

        patient.marital_status = form.marital_status.data
        patient.medications = form.medications.data

        patient.emergency_name = form.emergency_contact_name.data
        patient.emergency_relation = form.emergency_contact_relationship.data
        patient.emergency_contact = form.emergency_contact_number.data
        
        patient.contact_number = form.contact_number.data
        patient.address = form.address.data
        patient.address_line2 = form.address_line2.data
        patient.pincode = form.pincode.data
        patient.city = form.city.data
        patient.state = form.state.data
        patient.country = form.country.data
        patient.nationality = form.nationality.data
        
        db.session.commit()
        flash("Your profile has been updated successfully!", "success")
        return redirect(url_for('main.patient_self_profile'))

    return render_template('patient_edit_profile.html', form=form, active='profile')
