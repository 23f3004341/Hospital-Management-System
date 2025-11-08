import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from datetime import date
from flask_migrate import Migrate
from sqlalchemy.exc import OperationalError

basedir = os.path.abspath(os.path.dirname(__file__))

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'


def create_default_admin():
    try:
        from models import User
        existing_admin = User.query.filter_by(user_role='admin').first()
        if not existing_admin:
            admin = User(
                user_name='admin',
                email_address='admin@medilife.com',
                gender='Male',
                dob=date(1996, 4, 20),
                contact_number='7000501987',
                address='MG Road Gurgaon',
                user_role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: Email: admin@medilife.com | Password: admin123")
        else:
            print("Admin already exists.")
    except OperationalError:
        print("Database error (likely no DB yet)")
    except Exception as e:
        print("Skipping default admin creation due to:", str(e))


def seed_departments():
    try:
        from models import Department
        default_departments = [
            'Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'Dermatology',
            'ENT', 'Ophthalmology', 'General Medicine', 'Psychiatry', 'Urology'
        ]
        for name in default_departments:
            if not Department.query.filter_by(dept_name=name).first():
                db.session.add(Department(dept_name=name))
        db.session.commit()
        print("Departments included")
    except OperationalError:
        print("Database error (likely no DB yet)")
    except Exception as e:
        print("Skipping department seeding due to:", str(e))


def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'arya_2320')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hospital_data.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        from models import User, Department, Appointment, Treatment
        db.create_all()

        create_default_admin()
        seed_departments()

    return app
