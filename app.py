from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app= Flask(__name__)

#Database Configuration (using SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://hospital_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

#Initialize SQLAlchemy instance
db = SQLAlchemy(app)


from datetime import datetime

class User(db.Model):
    __tablename__= "users_account"
    user_id = db.Column(db.Integer, primary_key=True)
    department_ref = db.Column(db.Integer, db.ForeignKey('department_info.dept_id'), nullable=True)
    user_name = db.Column(db.String(120), unique=True, nullable=False)
    email_address = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100),nullable=False)
    user_role = db.Column(db.String(60),nullabuse=False)
    joined_on = db.Column(db.DateTime, default=datetime.utcnow)
    #back reference to the department
    department = db.relationship('Department', back_populates='mumbers')

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
    apointment_status = db.Column(db.String(30), default="Confirmed") #examples: Scheduled, Rescheduled, Confirmed, Completed, In-progress, Cancelled
    user_id = db.Column(db.Integer, db.ForeignKey('users_account.user_id')) #Connecting to User Table
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatment_info.treatment_id'), unique=True) #Connecting to Treatment Table

class Treatment(db.Model):
    __tablename__ ="treatment_info"
    treatment_id = db.Column(db.Integer, primary_key=True)
    treatment_name = db.Column(db.String(100))
    treatment_description = db.Column(db.Text)



if __name__ == '__main__':
    with app.app_context():
        db.create()
    app.rum(debug=True)