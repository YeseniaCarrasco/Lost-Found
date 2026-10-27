"""WTForms definitions. Flask-WTF adds a CSRF token to every one of these."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import EqualTo, InputRequired, Length, Regexp


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        InputRequired(), Length(3, 30),
        Regexp(r"^[A-Za-z0-9_.]+$", message="Letters, numbers, dots and underscores only."),
    ])
    password = PasswordField("Password", validators=[InputRequired(), Length(8, 128)])
    confirm = PasswordField("Confirm password", validators=[
        InputRequired(), EqualTo("password", message="Passwords must match."),
    ])


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=30)])
    password = PasswordField("Password", validators=[InputRequired(), Length(max=128)])
    remember = BooleanField("Keep me signed in")
