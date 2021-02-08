# app/forms.py

import phonenumbers
from flask_wtf import FlaskForm
from phonenumbers import carrier
from app.models import User
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

"""
This module shall contain the various web forms used in the web app
"""


class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign Up')

    def validate(self):
        # check if all required fields are filled
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        password = self.password.data
        if len(password) < 8 or len(password) > 100:
            self.password.errors.append("Please enter a password of between 8 and 100 characters")
            return False

        confirm_password = self.confirm_password.data
        if confirm_password != password:
            self.confirm_password.errors.append('Should be the same as password')
            return False

        telephone = self.telephone.data
        if not telephone:
            self.telephone.errors.append("Missing phone numbers")
            return False
        if type(telephone) != str:
            self.telephone.errors.append("Unable to determine phone number")
            return False
        region = "KE"
        # Create a `PhoneNumber` object from a string representing a phone number
        # Specify country of origin of phone number.
        # This maybe unnecessary for numbers starting with '+' since they are globally unique.
        phone = phonenumbers.parse(telephone, region)
        # Check whether it's a possible number (e.g. it has the right number of digits)
        if not phonenumbers.is_possible_number(phone):
            self.telephone.errors.append("Possibly not a number. Check if e.g. number of digits is correct")
            return False
        # Check whether it's a valid number (e.g. it's in an assigned exchange)
        if not phonenumbers.is_valid_number_for_region(phone, region):
            self.telephone.errors.append("Invalid phone number")
            return False
        # Format number as per international format code E164
        phone_number = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        # Get the carrier of the phone number
        operator = carrier.name_for_number(phone, "en") if carrier.name_for_number(phone, "en") else ''
        print(phone_number, operator)
        # Ensure phone is Safaricom
        if operator != "Safaricom":
            self.telephone.errors.append("Kindly use a Safaricom line for MPESA prompt")
            return False
        # If telephone is previously, raise error
        if User.query.filter_by(telephone=phone_number).first():
            self.telephone.errors.append('Telephone already registered')
            return False
        return True


class LoginForm(FlaskForm):
    telephone = StringField('Telephone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def validate(self):
        # check if all required fields are filled
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        password = self.password.data
        if len(password) < 8 or len(password) > 100:
            self.password.errors.append("Please enter a password of between 8 and 100 characters")
            return False

        telephone = self.telephone.data
        if not telephone:
            self.telephone.errors.append("Missing phone numbers")
            return False
        if type(telephone) != str:
            self.telephone.errors.append("Unable to determine phone number")
            return False
        region = "KE"
        # Create a `PhoneNumber` object from a string representing a phone number
        # Specify country of origin of phone number.
        # This maybe unnecessary for numbers starting with '+' since they are globally unique.
        phone = phonenumbers.parse(telephone, region)
        # Check whether it's a possible number (e.g. it has the right number of digits)
        if not phonenumbers.is_possible_number(phone):
            self.telephone.errors.append("Possibly not a number. Check if e.g. number of digits is correct")
            return False
        # Check whether it's a valid number (e.g. it's in an assigned exchange)
        if not phonenumbers.is_valid_number_for_region(phone, region):
            self.telephone.errors.append("Invalid phone number")
            return False
        # Format number as per international format code E164
        phone_number = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        # Get the carrier of the phone number
        operator = carrier.name_for_number(phone, "en") if carrier.name_for_number(phone, "en") else ''
        print(phone_number, operator)
        # Ensure phone is Safaricom
        if operator != "Safaricom":
            self.telephone.errors.append("Kindly use a Safaricom line for MPESA prompt")
            return False
        # If telephone is not registered, raise error
        user = User.query.filter_by(telephone=phone_number).first()
        if not user:
            self.telephone.errors.append('User not registered')
            return False

        # confirm user's password
        if not user.verify_password(password):
            self.password.errors.append("Invalid password")
            return False

        return True

    # --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org
