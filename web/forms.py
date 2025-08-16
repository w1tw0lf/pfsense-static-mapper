from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Regexp

class MappingForm(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    mac_address = StringField('MAC Address', validators=[
        DataRequired(),
        Regexp(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
               message="Invalid MAC address format.")
    ])
    submit = SubmitField('Add Mapping')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')