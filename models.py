from init import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Model
class User(db.Model, UserMixin):
    __tablename__ = "users_account"

    user_id = db.Column(db.Integer, primary_key=True)
    user_role = db.Column(db.String(60), nullable=False)
    user_name = db.Column(db.String(120), unique=True, nullable=False)
    email_address = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    first_name = db.Column(db.String(80))
    middle_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    gender = db.Column(db.String(10), nullable=False)
    image = db.Column(db.String(255))
    joined_on = db.Column(db.DateTime, default=datetime.utcnow)
    is_blacklisted = db.Column(db.Boolean, default=False)

    contact_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    country = db.Column(db.String(80))
    pincode = db.Column(db.String(10))
    nationality = db.Column(db.String(100))

    dob = db.Column(db.DateTime, default=datetime.utcnow)

    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    medications = db.Column(db.String(5))
    marital_status = db.Column(db.String(50))
    emergency_name = db.Column(db.String(120))
    emergency_relation = db.Column(db.String(80))
    emergency_contact = db.Column(db.String(20))

    department_ref = db.Column(db.Integer, db.ForeignKey('department_info.dept_id'))
    availability = db.Column(db.String(10))
    doctor_qualification = db.Column(db.String(150))
    doctor_experience = db.Column(db.Integer)

    doctor_appointments = db.relationship(
        'Appointment',
        foreign_keys='Appointment.doctor_id',
        back_populates='doctor',
        cascade="all, delete",
        passive_deletes=True
    )

    patient_appointments = db.relationship(
        'Appointment',
        foreign_keys='Appointment.patient_id',
        back_populates='patient',
        cascade="all, delete",
        passive_deletes=True
    )

    doctor_treatments = db.relationship(
        'Treatment',
        foreign_keys='Treatment.doctor_id',
        backref='doctor',
        cascade="all, delete",
        passive_deletes=True
    )

    patient_treatments = db.relationship(
        'Treatment',
        foreign_keys='Treatment.patient_id',
        backref='patient',
        cascade="all, delete",
        passive_deletes=True
    )

    availabilities = db.relationship(
        'DoctorAvailability',
        backref='doctor',
        cascade='all, delete',
        passive_deletes=True
    )

    department = db.relationship('Department', back_populates='doctors')

    def set_password(self, password_text):
        self.password = generate_password_hash(password_text)

    def check_password(self, password_text):
        return check_password_hash(self.password, password_text)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f"<User {self.user_name} ({self.user_role})>"


# Department Model
class Department(db.Model):
    __tablename__ = "department_info"

    dept_id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    doctors = db.relationship('User', back_populates='department')

    def __repr__(self):
        return f"<Department {self.dept_name}>"


# Appointment Model
class Appointment(db.Model):
    __tablename__ = "appointment_info"

    appointment_id = db.Column(db.Integer, primary_key=True)
    appointment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    appointment_time = db.Column(db.String(25))
    appointment_status = db.Column(db.String(30), default="Confirmed")
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('users_account.user_id', ondelete='CASCADE'),
        nullable=False
    )
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('users_account.user_id', ondelete='CASCADE'),
        nullable=False
    )

    treatment_id = db.Column(
        db.Integer,
        db.ForeignKey('treatment_info.treatment_id', ondelete='SET NULL'),
        nullable=True
    )

    doctor = db.relationship('User', foreign_keys=[doctor_id], back_populates='doctor_appointments')
    patient = db.relationship('User', foreign_keys=[patient_id], back_populates='patient_appointments')
    treatment = db.relationship('Treatment', backref='appointment', lazy=True)

    def __repr__(self):
        return f"<Appointment {self.appointment_id} - {self.appointment_status}>"


# Treatment Model
class Treatment(db.Model):
    __tablename__ = "treatment_info"

    treatment_id = db.Column(db.Integer, primary_key=True)
    treatment_name = db.Column(db.String(150), nullable=False)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    doctor_notes = db.Column(db.Text)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('users_account.user_id', ondelete='CASCADE'),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('users_account.user_id', ondelete='CASCADE'),
        nullable=False
    )

    def __repr__(self):
        return f"<Treatment {self.treatment_name}>"


# Docotor Availability Model
class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('users_account.user_id', ondelete='CASCADE'),
        nullable=False
    )

    date = db.Column(db.String(25), nullable=False)
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    available = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Availability {self.date} ({'Yes' if self.available else 'No'})>"
