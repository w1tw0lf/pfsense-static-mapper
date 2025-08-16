import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Regexp
from flask_wtf.csrf import CSRFProtect
from static_mapping.core import create_static_mapping_entry
from static_mapping.utils import count_available_ips
from static_mapping.config import load_config
from static_mapping.api import PfSenseAPI
from werkzeug.security import check_password_hash
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler
import configparser

app = Flask(__name__)

# Logging Configuration
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
csrf = CSRFProtect(app)

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=2)
    session.modified = True

config = load_config()

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

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        stored_username = config.get('auth', 'username')
        stored_password_hash = config.get('auth', 'password_hash')
        if username == stored_username and check_password_hash(stored_password_hash, password):
            session['logged_in'] = True
            session['username'] = username
            flash('You were successfully logged in', 'info')
            app.logger.info(f"User '{username}' logged in successfully.")
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
            app.logger.warning(f"Failed login attempt for user '{username}'.")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    app.logger.info(f"User '{session.get('username')}' logged out.")
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You were logged out', 'success')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = MappingForm()

    # Load config for PfSenseAPI initialization
    pfsense_config = configparser.ConfigParser()
    pfsense_config.read('config.ini')

    # Initialize PfSenseAPI
    pfsense_api = PfSenseAPI(pfsense_config, app.logger)

    # Get existing mappings and DHCP range for available IP count
    existing_maps = pfsense_api.get_existing_static_mappings()
    interface_ip, interface_subnet = pfsense_api.get_interface_details()
    dhcp_range_from, dhcp_range_to = pfsense_api.get_dhcp_range()

    available_ips_count = 0
    if interface_ip and interface_subnet and dhcp_range_from and dhcp_range_to:
        available_ips_count = count_available_ips(existing_maps, interface_ip, interface_subnet, dhcp_range_from, dhcp_range_to)

    if form.validate_on_submit():
        hostname = form.hostname.data
        description = form.description.data
        mac_address = form.mac_address.data

        success, message, _ = create_static_mapping_entry(mac_address, hostname, description, app.logger)

        if success:
            flash(message, 'success')
            app.logger.info(f"User '{session.get('username')}' created a new static mapping for MAC address '{mac_address}'.")
        else:
            flash(message, 'error')
            app.logger.error(f"Failed to create static mapping for MAC address '{mac_address}'. Reason: {message}")
        return redirect(url_for('index'))

    messages = get_flashed_messages(with_categories=True)
    success_flag = False
    for category, message in messages:
        if category == 'success':
            success_flag = True
            break
            
    return render_template('index.html', form=form, messages=messages, success_flag=success_flag, available_ips_count=available_ips_count)

if __name__ == '__main__':
    app.run()