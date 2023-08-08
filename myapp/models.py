from cloud import db
from flask_login import UserMixin
from datetime import datetime


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    psw = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(20), nullable = False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Photos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String, nullable = False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
