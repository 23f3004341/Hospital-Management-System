import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import date
from sqlalchemy.exc import OperationalError
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "info"

basedir = os.path.abspath(os.path.dirname(__file__))

@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# Default Admin
def create_default_admin():
    try:
        from models import User

        existing_admin = User.query.filter_by(user_role="admin").first()
        if existing_admin:
            print("ℹ️ Admin already exists.")
            return

        admin = User(
            user_name="Admin",
            email_address="admin@medilife.com",
            gender="Male",
            dob=date(1996, 4, 20),
            contact_number="+917000501987",
            address="MG Road, Gurgaon, India",
            user_role="admin",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        print("✅ Default admin created: Email: admin@medilife.com | Password: admin123")

    except OperationalError:
        print("⚠️ Tables not ready — default admin creation skipped.")
    except Exception as e:
        print("⚠️ Skipping default admin creation due to:", e)


# Default Departments
def seed_departments():
    try:
        from models import Department

        default_departments = [
            "Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Dermatology",
            "ENT", "Ophthalmology", "General Medicine", "Psychiatry", "Urology"
        ]

        for name in default_departments:
            if not Department.query.filter_by(dept_name=name).first():
                db.session.add(Department(dept_name=name))

        db.session.commit()
        print("✅ Departments seeded.")

    except OperationalError:
        print("⚠️ Tables not ready — seeding skipped.")
    except Exception as e:
        print("⚠️ Skipping department seeding due to:", e)



def create_app():
    app = Flask(__name__, template_folder="templates")

    # App Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "arya_2320")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "hospital_data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register Blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Initialise Database
    with app.app_context():
        from models import User, Department, Appointment, Treatment
        db.create_all()

        create_default_admin()
        seed_departments()

    return app
