"""WTForms definitions. Flask-WTF adds a CSRF token to every one of these."""
from datetime import date
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, PasswordField, SelectField,
                     StringField, TextAreaField)
from wtforms.validators import (EqualTo, InputRequired, Length, Optional,
                                Regexp, ValidationError)

CATEGORIES = ["Electronics", "Keys", "ID / Cards", "Bags", "Clothing",
              "Water bottles", "Books & notes", "Jewelry", "Other"]


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


class ItemForm(FlaskForm):
    title = StringField("What was found?", validators=[InputRequired(), Length(2, 100)])
    category = SelectField("Category", choices=CATEGORIES, default="Other")
    location = StringField("Where?", validators=[InputRequired(), Length(2, 120)])
    found_date = DateField("When?", default=date.today, validators=[InputRequired()])
    photo_url = StringField("Photo URL", validators=[Optional(), Length(max=500)])
    description = TextAreaField("Details", validators=[Optional(), Length(max=1000)])

    def validate_found_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("The date can't be in the future.")

    def validate_photo_url(self, field):
        parsed = urlparse(field.data or "")
        if field.data and (parsed.scheme not in ("http", "https") or not parsed.netloc):
            raise ValidationError("Enter a full http:// or https:// image link.")
