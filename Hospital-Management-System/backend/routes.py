from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
from datetime import datetime
from backend import db
from backend.models import User, Department, Appointment, Treatment 
from backend.forms import LoginForm, PatientRegistrationForm, AddDoctorForm

main = Blueprint('main', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
            if current_user.user_role != role:
                flash(f'Access denied. You are not registered as {role}', 'danger')
                return redirect(url_for('main.dashboard_redirect'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@main.route('/')
@main.route('/home')
def home():
    return render_template('home.html')

# Registration Page
@main.route('/register', methods=['GET', 'POST'])
def register():
    # Only patients can register
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))

    form = PatientRegistrationForm()
    if form.validate_on_submit():
        new_patient = User(
            user_name=form.user_name.data,
            email_address=form.email_address.data,
            gender=form.gender.data,
            dob=form.dob.data,
            contact_number=form.contact_number.data,
            address=form.address.data,
            user_role='patient'
        )
        new_patient.set_password(form.password.data)
        db.session.add(new_patient)
        db.session.commit()

        flash('Patient account successfully created. Login now.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', title='Patient Registration', form=form)

# Login Page
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data
        selected_role = request.form.get('role') or request.args.get('role') or 'patient'

        user = User.query.filter_by(email_address=email).first()
        if user and user.check_password(password):
            if user.user_role == selected_role:
                login_user(user, remember=form.remember.data)
                flash(f'Welcome {user.user_name}! Logged in as {selected_role.capitalize()}.', 'success')
                return redirect(url_for('main.dashboard_redirect'))
            else:
                flash(f'Incorrect role selected. Please login as {user.user_role.capitalize()}.', 'warning')
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', title='Login', form=form)

#Logout Page
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

# Home Page
@main.route('/dashboard')
@login_required
def dashboard_redirect():
    role = current_user.user_role
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

# Admin Dashboard
@main.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    total_doctors = db.session.query(User).filter_by(user_role='doctor').count()
    total_patients = db.session.query(User).filter_by(user_role='patient').count()
    total_appointments = db.session.query(Appointment).count()

    doctors = User.query.filter_by(user_role='doctor').all()
    patients = User.query.filter_by(user_role='patient').all()
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc()).all()

    return render_template(
        'admin_dashboard.html',
        title='Admin Dashboard',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        doctors=doctors,
        patients=patients,
        appointments=appointments
    )

# Admin_Add_Doctor dashboard
@main.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_doctor():
    """Admin-only route to add doctor (reads extended AddDoctorForm)."""
    form = AddDoctorForm()

    departments = Department.query.order_by(Department.dept_name).all()
    form.department_ref.choices = [(d.dept_id, d.dept_name) for d in departments]
    form.department_ref.choices.insert(0, (0, 'Select Department'))

    if form.validate_on_submit():
        if form.department_ref.data == 0:
            flash('Please select a valid department.', 'warning')
            return render_template('add_doctor.html', title='Add New Doctor', form=form)

        username = None
        if form.user_name.data and form.user_name.data.strip():
            username = form.user_name.data.strip()
        else:
            first = (form.first_name.data or "").strip().lower()
            last = (form.last_name.data or "").strip().lower()
            if first and last:
                base = f"{first}.{last}"
            elif first:
                base = first
            else:
                base = (form.email_address.data.split('@')[0]).lower()
            username = base
            i = 1
            while User.query.filter_by(user_name=username).first():
                username = f"{base}{i}"
                i += 1

        # combine contact
        country_code = form.country_code.data or ""
        contact_num = form.contact_number.data.strip() if form.contact_number.data else ""
        contact_combined = f"{country_code}{contact_num}"

        # build full address
        address_parts = []
        if form.address_line1.data:
            address_parts.append(form.address_line1.data.strip())
        if form.address_line2.data:
            address_parts.append(form.address_line2.data.strip())
        if form.city.data:
            address_parts.append(form.city.data.strip())
        if form.state.data:
            address_parts.append(form.state.data.strip())
        if form.pincode.data:
            address_parts.append(form.pincode.data.strip())
        if form.country.data:
            address_parts.append(form.country.data.strip())
        full_address = "\n".join([p for p in address_parts if p])

        # Create user instance
        new_doctor = User(
            user_name=username,
            email_address=form.email_address.data.strip(),
            gender=form.gender.data,
            dob=form.dob.data,               
            contact_number=contact_combined,
            address=full_address,
            nationality=form.country.data or None,
            department_ref=form.department_ref.data,
            doctor_qualification=form.qualification.data,
            doctor_experience=form.doctor_experience.data,
            user_role='doctor'
        )

        try:
            if hasattr(new_doctor, 'first_name'):
                setattr(new_doctor, 'first_name', form.first_name.data.strip() if form.first_name.data else None)
            if hasattr(new_doctor, 'middle_name'):
                setattr(new_doctor, 'middle_name', form.middle_name.data.strip() if form.middle_name.data else None)
            if hasattr(new_doctor, 'last_name'):
                setattr(new_doctor, 'last_name', form.last_name.data.strip() if form.last_name.data else None)
        except Exception:
            pass

        # set password
        new_doctor.set_password(form.password.data)

        db.session.add(new_doctor)
        db.session.commit()

        flash(f'Doctor account for {new_doctor.user_name} created successfully.', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('add_doctor.html', title='Add New Doctor', form=form)


# Doctor dashboard
@main.route('/doctor/dashboard')
@login_required
@role_required('doctor')
def doctor_dashboard():
    today = datetime.today().strftime("%Y-%m-%d")

    upcoming_appointments = (
        Appointment.query
        .filter(Appointment.doctor_id == current_user.user_id)
        .filter(Appointment.appointment_date >= today)
        .order_by(Appointment.appointment_date)
        .all()
    )

    # unique assigned patients
    assigned_patients = (
        User.query.join(Appointment, Appointment.patient_id == User.user_id)
        .filter(Appointment.doctor_id == current_user.user_id)
        .distinct()
        .all()
    )

    return render_template(
        'doctor_dashboard.html',
        title='Doctor Dashboard',
        upcoming_appointments=upcoming_appointments,
        assigned_patients=assigned_patients
    )

# Patient dashboard
@main.route('/patient/dashboard')
@login_required
@role_required('patient')
def patient_dashboard():
    return render_template('patient_dash.html', title='Patient Dashboard')
