from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash
from web.forms import LoginForm
from static_mapping.config import load_config

config = load_config()
auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['GET', 'POST'])
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
            current_app.logger.info(f"User '{username}' logged in successfully.")
            return redirect(url_for('views.index'))
        else:
            flash('Invalid credentials', 'error')
            current_app.logger.warning(f"Failed login attempt for user '{username}'.")
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    current_app.logger.info(f"User '{session.get('username')}' logged out.")
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You were logged out', 'success')
    return redirect(url_for('auth.login'))