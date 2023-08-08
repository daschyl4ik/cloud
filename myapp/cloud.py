from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import LOGIN_MESSAGE, LOGIN_MESSAGE_CATEGORY
# CACHE_TYPE, CACHE_DEFAULT_TIMEOUT

app = Flask(__name__)
app.config.from_object('config')

# app.config['CACHE_TYPE'] = CACHE_TYPE
# app.config['CACHE_DEFAULT_TIMEOUT'] = CACHE_DEFAULT_TIMEOUT
# cache = Cache(app)

db = SQLAlchemy(app)

login_manager = LoginManager(app)

login_manager.login_view = "login"
login_manager.login_message = LOGIN_MESSAGE
login_manager.login_message_category = LOGIN_MESSAGE_CATEGORY

with app.app_context():
    db.create_all()

import views


