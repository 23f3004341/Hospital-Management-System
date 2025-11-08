from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField,
    DateField,   # kept for other forms if any, but we'll use StringField for dob here
    TextAreaField,
    IntegerField
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    ValidationError,
    Length,
    Optional
)

from models import User  # keep your project import

import datetime as _dt


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    # template expects form.remember_me
    remember_me = BooleanField('Remember Me')
    login_as = SelectField(
        'Login as',
        choices=[
            ('admin', 'Admin'),
            ('doctor', 'Doctor'),
            ('patient', 'Patient')
        ],
        validators=[DataRequired()],
        coerce=str
    )
    submit = SubmitField('Login')


class PatientRegistrationForm(FlaskForm):
    user_name = StringField('Username', validators=[DataRequired(), Length(min=2, max=120)])
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )
    gender = SelectField(
        'Gender',
        choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        validators=[DataRequired()]
    )
    dob = DateField('Date of Birth (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=6, max=20)])
    address = TextAreaField('Address', validators=[DataRequired(), Length(min=5, max=300)])
    submit = SubmitField('Register')

    def validate_email_address(self, email_address):
        user = User.query.filter_by(email_address=email_address.data).first()
        if user:
            raise ValidationError('Email ID already in use. Try another email address.')

    def validate_user_name(self, user_name):
        user = User.query.filter_by(user_name=user_name.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose another.')


class AddDoctorForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=80)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=80)])

    user_name = StringField('Username', validators=[Optional(), Length(min=2, max=120)])
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Set Initial Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])

    gender = SelectField(
        'Gender',
        choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        validators=[DataRequired()]
    )
    # Accept flexible date formats in doctor form (we'll parse it in validate_dob)
    dob = StringField('Date of Birth (YYYY-MM-DD or DD/MM/YYYY)', validators=[Optional()])

    country_code = SelectField(
        'Country Code',
        coerce=str,
        choices=[
            ('+91', '+91 (India)'),
            ('+1', '+1 (USA)'),
            ('+44', '+44 (UK)'),
            ('+61', '+61 (Australia)'),
            ('+971', '+971 (UAE)'),
            ('+49', '+49 (Germany)')
        ],
        validators=[DataRequired()]
    )
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=6, max=20)])

    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(min=2, max=200)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=3, max=12)])
    country = StringField('Country', validators=[DataRequired(), Length(max=100)])

    department_ref = SelectField('Department', coerce=int, validators=[DataRequired()])
    qualification = SelectField(
        'Qualification',
        choices=[
            ('MBBS', 'MBBS'),
            ('MD', 'MD'),
            ('MS', 'MS'),
            ('BAMS', 'BAMS'),
            ('BHMS', 'BHMS'),
            ('BDS', 'BDS'),
            ('DO', 'DO'),
            ('OTHER', 'Other')
        ],
        validators=[DataRequired()]
    )
    doctor_experience = IntegerField('Experience (Years)', validators=[DataRequired()])

    submit = SubmitField('Add Doctor')

    def validate_email_address(self, email_address):
        user = User.query.filter_by(email_address=email_address.data).first()
        if user:
            raise ValidationError('Email is already registered.')

    def validate_user_name(self, user_name):
        if user_name.data:
            user = User.query.filter_by(user_name=user_name.data).first()
            if user:
                raise ValidationError('Username is already taken.')

    def validate_dob(self, field):
        """
        Accept several common date formats and convert field.data to a date object.
        Valid formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
        """
        s = (field.data or "").strip()
        if not s:
            field.data = None
            return

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                parsed = _dt.datetime.strptime(s, fmt).date()
                field.data = parsed  # normalized to date object for route code
                return
            except ValueError:
                continue
        raise ValidationError("Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY.")
