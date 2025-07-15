from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, Length


class LoginForm(FlaskForm):
    name = StringField("Name", [InputRequired()])
    password = PasswordField("Password", [InputRequired()])
    submit = SubmitField("Sign in")


# Add these to your existing forms.py file


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(
                min=3, max=50, message="Username must be between 3 and 50 characters"
            ),
        ],
    )
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address"),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")


class ResendVerificationForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address"),
        ],
    )
    submit = SubmitField("Resend Verification Email")
