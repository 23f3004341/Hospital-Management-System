from flask import render_template, redirect, url_for, flash, request, Blueprint, current_app
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
from datetime import datetime

from init import db
from models import User, Department, Appointment, Treatment
from forms import LoginForm, PatientRegistrationForm, AddDoctorForm
from werkzeug.security import check_password_hash

main = Blueprint('main', __name__)


def role_required(role):
    """
    Decorator to require a role. Compares canonical lowercase roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login', next=request.url))
            user_role = (getattr(current_user, 'user_role', '') or '').strip().lower()
            if user_role != (role or '').strip().lower():
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
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_redirect'))

    form = PatientRegistrationForm()
    if form.validate_on_submit():
        new_patient = User(
            user_name=form.user_name.data.strip(),
            email_address=form.email_address.data.strip().lower(),
            gender=form.gender.data,
            dob=form.dob.data,
            contact_number=form.contact_number.data.strip(),
            address=form.address.data.strip(),
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
        email = (form.email.data or "").strip().lower()
        password = form.password.data or ""
        # canonical role value submitted by the SelectField
        selected_role = (form.login_as.data or "").strip().lower()

        # case-insensitive email lookup
        user = User.query.filter(db.func.lower(User.email_address) == email).first()

        # debug (remove/comment out in production if desired)
        current_app.logger.debug("Login attempt email=%s selected_role=%s user=%s", email, selected_role, getattr(user, 'user_name', None))

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', title='Login', form=form)

        user_role = (user.user_role or "").strip().lower()
        if selected_role != user_role:
            # use user's stored display form in message, but compare using canonical values
            flash(f'Incorrect role selected. Please login as {user.user_role.capitalize()}.', 'warning')
            return render_template('login.html', title='Login', form=form)

        # passed checks, login
        remember_flag = bool(getattr(form, 'remember_me', None) and form.remember_me.data)
        login_user(user, remember=remember_flag)
        flash(f'Welcome {user.user_name}! Logged in as {user.user_role.capitalize()}.', 'success')
        return redirect(url_for('main.dashboard_redirect'))

    return render_template('login.html', title='Login', form=form)


# Logout Page
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


# Dashboard Redirect
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


# Admin Add Doctor
@main.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_doctor():
    form = AddDoctorForm()

    # build department choices early so SelectField validates against them
    departments = Department.query.order_by(Department.dept_name).all()
    form.department_ref.choices = [(d.dept_id, d.dept_name) for d in departments]
    # sentinel value for "please select"
    form.department_ref.choices.insert(0, (0, 'Select Department'))

    # Successful submission path
    if form.validate_on_submit():
        # explicit check for sentinel (defensive - DataRequired may mark 0 invalid)
        if int(form.department_ref.data or 0) == 0:
            flash('Please select a valid department.', 'warning')
            return render_template('add_doctor.html', title='Add New Doctor', form=form)

        # create username if not provided
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

        country_code = form.country_code.data or ""
        contact_num = form.contact_number.data.strip() if form.contact_number.data else ""
        contact_combined = f"{country_code}{contact_num}"

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

        new_doctor = User(
            user_name=username,
            email_address=form.email_address.data.strip().lower(),
            gender=form.gender.data,
            dob=form.dob.data,  # form.validate_dob should have normalized this to a date or None
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

        new_doctor.set_password(form.password.data)

        db.session.add(new_doctor)
        db.session.commit()

        flash(f'Doctor account for {new_doctor.user_name} created successfully.', 'success')
        return redirect(url_for('main.admin_dashboard'))

    # If we reached here, either GET or POST-with-errors.
    # If POST and the form failed, surface helpful error messages to the user.
    if request.method == 'POST':
        # ensure department-specific helpful message if sentinel selected
        try:
            posted_dept = request.form.get('department_ref')
            if posted_dept is not None and int(posted_dept) == 0:
                form.errors.setdefault('department_ref', []).append('Please select a valid department.')
        except Exception:
            pass

        # flash each field error so user sees what's wrong
        if form.errors:
            for field, errs in form.errors.items():
                for err in errs:
                    # convert WTForms field names to nicer labels if you prefer
                    flash(f"{field}: {err}", "danger")

    return render_template('add_doctor.html', title='Add New Doctor', form=form)


# Doctor Dashboard
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


# Patient Dashboard
@main.route('/patient/dashboard')
@login_required
@role_required('patient')
def patient_dashboard():
    return render_template('patient_dash.html', title='Patient Dashboard')
