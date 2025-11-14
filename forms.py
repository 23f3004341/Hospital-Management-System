from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField,
    DateField,
    TextAreaField,
    IntegerField,
    RadioField
)
from wtforms.validators import (
    DataRequired,
    Length,
    Regexp,
    Email,
    EqualTo,
    ValidationError,
    Optional
)
from models import User


# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    remember_me = BooleanField('Remember Me')
    login_as = SelectField(
        'Login as',
        choices=[('admin', 'Admin'), ('doctor', 'Doctor'), ('patient', 'Patient')],
        validators=[DataRequired()],
        coerce=str
    )
    submit = SubmitField('Login')


# Patient Registeration Form
class PatientRegistrationForm(FlaskForm):
    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=1, max=80),
                    Regexp(r'^[A-Za-z\s]+$', message="First name must contain only letters.")]
    )
    last_name = StringField(
        'Last Name',
        validators=[Optional(), Length(max=80),
                    Regexp(r'^[A-Za-z\s]*$', message="Last name must contain only letters.")]
    )

    user_name = StringField('Username (used to log in)',
                            validators=[DataRequired(), Length(min=2, max=120)])

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

    height = StringField('Height (cm)', validators=[
        Optional(),
        Regexp(r'^\d{1,3}(\.\d{1,2})?$', message="Enter valid height in numbers only.")
    ])
    weight = StringField('Weight (kg)', validators=[
        Optional(),
        Regexp(r'^\d{1,3}(\.\d{1,2})?$', message="Enter valid weight in numbers only.")
    ])

    marital_status = SelectField(
        'Marital Status',
        choices=[('', 'Select'), ('Single', 'Single'), ('Married', 'Married'), ('Other', 'Other')],
        validators=[Optional()]
    )

    contact_number = StringField(
        'Contact Number',
        validators=[DataRequired(), Regexp(r'^\d{10}$', message="Enter a valid 10-digit number.")]
    )

    address = StringField('Address Line 1', validators=[DataRequired(), Length(min=5, max=200)])
    address_line2 = StringField('Address Line 2 (optional)', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    country = StringField('Country', validators=[Optional()])
    pincode = StringField(
        'Pincode',
        validators=[DataRequired(), Regexp(r'^\d{6}$', message="Enter a 6-digit pincode.")]
    )

    nationality = StringField('Nationality', validators=[Optional(), Length(max=100)])

    medications = RadioField(
        'Taking any medications currently?',
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='no',
        validators=[Optional()]
    )

    emergency_contact_name = StringField(
        'Emergency Contact Name',
        validators=[Optional(), Length(max=120),
                    Regexp(r'^[A-Za-z\s]+$', message="Enter letters only.")]
    )
    emergency_contact_relationship = StringField('Relationship', validators=[Optional(), Length(max=60)])
    emergency_contact_number = StringField(
        'Emergency Contact Number',
        validators=[Optional(), Regexp(r'^\d{10}$', message="Enter valid 10-digit number.")]
    )

    submit = SubmitField('Submit & Register')


    def validate_email_address(self, field):
        existing_user = User.query.filter_by(email_address=field.data.strip().lower()).first()
        if existing_user and (not hasattr(self, "obj") or existing_user.user_id != getattr(self.obj, "user_id", None)):
            raise ValidationError("Email ID already in use. Try another email address.")

    def validate_user_name(self, field):
        existing_user = User.query.filter_by(user_name=field.data.strip()).first()
        if existing_user and (not hasattr(self, "obj") or existing_user.user_id != getattr(self.obj, "user_id", None)):
           raise ValidationError("Username is already taken. Please choose another.")



# Add Doctor form
class AddDoctorForm(FlaskForm):
    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=1, max=80), Regexp(r'^[A-Za-z]+$', message="Only letters allowed.")]
    )
    middle_name = StringField(
        'Middle Name',
        validators=[Optional(), Length(max=80), Regexp(r'^[A-Za-z]*$', message="Only letters allowed.")]
    )
    last_name = StringField(
        'Last Name',
        validators=[DataRequired(), Length(min=1, max=80), Regexp(r'^[A-Za-z]+$', message="Only letters allowed.")]
    )

    user_name = StringField('Username', render_kw={'readonly': True})
    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField(
        'Set Initial Password',
        validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )

    gender = SelectField(
        'Gender',
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        validators=[DataRequired()]
    )
    dob = DateField('Date of Birth', validators=[Optional()])
    doctor_experience = IntegerField('Experience (Years)', validators=[DataRequired()])

    country_code = SelectField(
        'Country Code',
        choices=[
            ('+91', '+91 (India)'),
            ('+1', '+1 (USA)'),
            ('+44', '+44 (UK)'),
            ('+61', '+61 (Australia)'),
            ('+81', '+81 (Japan)'),
            ('+49', '+49 (Germany)')
        ],
        validators=[DataRequired()]
    )
    contact_number = StringField(
        'Contact Number',
        validators=[DataRequired(), Regexp(r'^\d{10}$', message="Contact number must be 10 digits.")]
    )

    address_line1 = StringField('Address Line 1', validators=[DataRequired()])
    address_line2 = StringField('Address Line 2 (optional)', validators=[Optional()])
    pincode = StringField(
        'Pincode',
        validators=[DataRequired(), Regexp(r'^\d{6}$', message="Pincode must be 6 digits.")]
    )
    city = StringField('City', render_kw={'readonly': True})
    state = StringField('State', render_kw={'readonly': True})
    country = StringField('Country', render_kw={'readonly': True})

    qualification = SelectField(
        'Qualification',
        choices=[
            ('MBBS', 'MBBS'), ('MD', 'MD'), ('MS', 'MS'),
            ('DM', 'DM'), ('MCh', 'MCh'),
            ('BDS', 'BDS'), ('MDS', 'MDS')
        ],
        validators=[DataRequired()]
    )
    department_ref = SelectField(
        'Department',
        choices=[], 
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField('Add Doctor')


# Update Doctor Form
class DoctorUpdateForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=80)])
    middle_name = StringField("Middle Name", validators=[Optional(), Length(max=80)])
    last_name = StringField("Last Name", validators=[Optional(), Length(max=80)])
    user_name = StringField("Username", render_kw={"readonly": True})
    email_address = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    contact_number = StringField("Contact Number", validators=[DataRequired(), Length(min=6, max=20)])
    doctor_experience = IntegerField("Experience (Years)", validators=[Optional()])
    department_ref = SelectField("Department", coerce=int, validators=[DataRequired()])
    qualification = SelectField("Qualification", choices=[
        ("MBBS", "MBBS"),
        ("MD", "MD"),
        ("MS", "MS"),
        ("BDS", "BDS"),
        ("BHMS", "BHMS"),
        ("BPT", "BPT"),
        ("Other", "Other")
    ], validators=[DataRequired()])
    submit = SubmitField("Update")


class PatientEditForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=80)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=80)])

    email_address = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    contact_number = StringField('Contact Number', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message="Enter a valid 10-digit number.")
    ])

    dob = DateField('Date of Birth (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])

    height = StringField('Height (cm)', validators=[Optional(), Regexp(r'^\d{1,3}(\.\d{1,2})?$')])
    weight = StringField('Weight (kg)', validators=[Optional(), Regexp(r'^\d{1,3}(\.\d{1,2})?$')])

    marital_status = SelectField(
        'Marital Status',
        choices=[('', 'Select'), ('Single', 'Single'), ('Married', 'Married'), ('Other', 'Other')],
        validators=[Optional()]
    )

    medications = RadioField(
        'Taking any medications currently?',
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='no',
        validators=[Optional()]
    )

    emergency_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=120)])
    emergency_relation = StringField('Relationship', validators=[Optional(), Length(max=60)])
    emergency_contact = StringField(
        'Emergency Contact Number',
        validators=[Optional(), Regexp(r'^\d{10}$', message="Enter valid 10-digit number.")]
    )

    address = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])

    pincode = StringField('Pincode', validators=[Optional(), Regexp(r'^\d{6}$')])
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    country = StringField('Country', validators=[Optional()])
    nationality = StringField('Nationality', validators=[Optional(), Length(max=100)])

    submit = SubmitField("Save Changes")
