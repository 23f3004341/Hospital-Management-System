from init import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users_account"

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80))
    middle_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    department_ref = db.Column(db.Integer, db.ForeignKey('department_info.dept_id'), nullable=True)
    user_name = db.Column(db.String(120), unique=True, nullable=False)
    email_address = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.DateTime, default=datetime.utcnow)
    contact_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    nationality = db.Column(db.String(100))
    availability = db.Column(db.String(10))  # Yes/No
    doctor_qualification = db.Column(db.String(150))  # MBBS, MD, MS, BDS, BHMS, BPT
    doctor_experience = db.Column(db.Integer, nullable=True)
    user_role = db.Column(db.String(60), nullable=False)  # admin, doctor, patient
    joined_on = db.Column(db.DateTime, default=datetime.utcnow)

    doctor_appointments = db.relationship(
        'Appointment', foreign_keys='Appointment.doctor_id', back_populates='doctor'
    )
    patient_appointments = db.relationship(
        'Appointment', foreign_keys='Appointment.patient_id', back_populates='patient'
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


class Department(db.Model):
    __tablename__ = "department_info"
    dept_id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    doctors = db.relationship('User', back_populates='department', lazy=True)

    def __repr__(self):
        return f"<Department {self.dept_name}>"


class Appointment(db.Model):
    __tablename__ = "appointment_info"
    appointment_id = db.Column(db.Integer, primary_key=True)
    appointment_date = db.Column(db.String(25))
    appointment_time = db.Column(db.String(25))
    appointment_status = db.Column(db.String(30), default="Confirmed")
    doctor_id = db.Column(db.Integer, db.ForeignKey('users_account.user_id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('users_account.user_id'))
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatment_info.treatment_id'))

    doctor = db.relationship('User', foreign_keys=[doctor_id], back_populates='doctor_appointments')
    patient = db.relationship('User', foreign_keys=[patient_id], back_populates='patient_appointments')

    def __repr__(self):
        return f"<Appointment ID={self.appointment_id}, Status={self.appointment_status}>"


class Treatment(db.Model):
    __tablename__ = "treatment_info"
    treatment_id = db.Column(db.Integer, primary_key=True)
    treatment_name = db.Column(db.String(100))
    treatment_diagnosis = db.Column(db.Text)
    treatment_prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    treatment_cost = db.Column(db.Float, nullable=False)
    appointments = db.relationship('Appointment', backref='treatment', lazy=True)

    def __repr__(self):
        return f"<Treatment {self.treatment_name}>"
