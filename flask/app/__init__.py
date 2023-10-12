from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from . import config
import logging


app = Flask(__name__)
app.config.from_object(config)

logging.basicConfig(filename= config.APP_LOG_FILE, level=logging.DEBUG)

db = SQLAlchemy(app)

login_manager = LoginManager(app)

login_manager.login_view = "login"
login_manager.login_message = config.LOGIN_MESSAGE
login_manager.login_message_category = config.LOGIN_MESSAGE_CATEGORY

from . import models

with app.app_context():
    db.create_all()

from . import views


