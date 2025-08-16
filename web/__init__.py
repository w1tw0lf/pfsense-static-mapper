import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    app = Flask(__name__)

    # Logging Configuration
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
    csrf = CSRFProtect(app)

    with app.app_context():
        from . import auth
        from . import views

        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(views.views_bp)

    return app