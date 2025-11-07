from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField,
    DateField,
    TextAreaField,
    IntegerField )

from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    ValidationError,
    Length,
    Optional )

from backend.models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    remember = BooleanField('Remember Me')
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
        user = User.query.filter_by(email_address=email_address.data).first() #check whether email 'exists' or not
        if user:
            raise ValidationError('Email id already in use. Try another email address')

    def validate_user_name(self, user_name):
        user = User.query.filter_by(user_name=user_name.data).first() #check if email is in use
        if user:
            raise ValidationError('Username is already taken. Please choose another.')


class AddDoctorForm(FlaskForm):
    # Name fields
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=80)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=80)])

    # Username, email, password
    user_name = StringField('Username', validators=[Optional(), Length(min=2, max=120)])
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Set Initial Password', validators=[DataRequired(), Length(min=6)])
    
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    # Gender and dob
    gender = SelectField(
        'Gender',
        choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        validators=[DataRequired()]
    )
    dob = DateField('Date of Birth (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])

    # Contact with country code
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

    # Address lines
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(min=2, max=200)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=100)])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=3, max=12)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])

    # Department and Qualification
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
            raise ValidationError('Email is already registered')

    def validate_user_name(self, user_name):
        if user_name.data:
            user = User.query.filter_by(user_name=user_name.data).first()
            if user:
                raise ValidationError('Username is already taken')
