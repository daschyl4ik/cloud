from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import LOGIN_MESSAGE, LOGIN_MESSAGE_CATEGORY

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

login_manager = LoginManager(app)

login_manager.login_view = "login"
login_manager.login_message = LOGIN_MESSAGE
login_manager.login_message_category = LOGIN_MESSAGE_CATEGORY

with app.app_context():
    db.create_all()

import views


