from app import db

from datetime import datetime

class User(db.Model):
    __tablename__= "users_account"
    user_id = db.Column(db.Integer, primary_key=True)
    department_ref = db.Column(db.Integer, db.ForeignKey('department_info.dept_id'), nullable=True)
    user_name = db.Column(db.String(120), unique=True, nullable=False)
    email_address = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100),nullable=False)
    user_role = db.Column(db.String(60),nullable=False) # examples: admins, doctors, patients
    joined_on = db.Column(db.DateTime, default=datetime.utcnow)
    doctor_appointments = db.relationship('Appointment', foreign_keys='Appointment.doctor_id', back_populates='doctor')
    patient_appointments = db.relationship('Appointment', foreign_keys='Appointment.patient_id', back_populates='patient')

    # back reference to the department
    department = db.relationship('Department', back_populates='doctors')

class Department(db.Model):
    __tablename__="department_info"
    dept_id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    description= db.Column(db.Text, nullable=True)
    # reverse relationship to easily fetch the doctors in this department
    doctors = db.relationship('User', back_populates='department', lazy=True)

class Appointment(db.Model):
    __tablename__= "appointment_info"
    appointment_id = db.Column(db.Integer, primary_key=True)
    appointment_date = db.Column(db.String(25))
    appointment_time = db.Column(db.String(25))
    appointment_status = db.Column(db.String(30), default="Confirmed") # examples: Scheduled, Rescheduled, Confirmed, Completed, In-progress, Cancelled
    doctor_id = db.Column(db.Integer, db.ForeignKey('users_account.user_id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('users_account.user_id'))
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatment_info.treatment_id'))
    doctor = db.relationship('User', foreign_keys= [doctor_id], back_populates = 'doctor_appointments')
    patient = db.relationship('User', foreign_keys=[patient_id], back_populates = 'patient_appointments')

class Treatment(db.Model):
    __tablename__ ="treatment_info"
    treatment_id = db.Column(db.Integer, primary_key=True)
    treatment_name = db.Column(db.String(100))
    treatment_description = db.Column(db.Text)
    treatment_cost =  db.Column(db.Float, nullable=False)  # Cost in INR
    appointments = db.relationship('Appointment', backref='treatment', lazy=True)

