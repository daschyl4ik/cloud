from . import app, login_manager, models, funcs
from flask import render_template
from flask_login import login_required


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return models.Users.query.get(int(user_id))

@app.route("/")
def index():
    return funcs.index()


@app.route("/login", methods =["POST", "GET"])
def login():
    return funcs.login()


@app.route("/register", methods =["POST", "GET"])
def register():
    return funcs.register()


@app.route("/photos",  methods = ["GET"])
@login_required
def photos():
    return funcs.photos()


@app.route("/logout")
@login_required
def logout():
    return funcs.logout()


@app.route("/upload", methods=["POST", "GET"])
@login_required
def upload():
    return funcs.upload()


