from cloud import app, login_manager
from flask import render_template
from models import Users
import funcs
from flask_login import login_required


@app.route("/hello",  methods =["GET"])
def hello():
    return render_template("hello.html")


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Users.query.get(int(user_id))


@app.route("/")
@app.route("/index")
def index():
    return funcs.index


@app.route("/login", methods =["POST", "GET"])
def login():
    return funcs.login()


@app.route("/register", methods =["POST", "GET"])
def register():
    return funcs.register()


@app.route("/photos")
@login_required
def photos():
    return funcs.photos()


@app.route("/logout")
@login_required
def logout():
    return funcs.logout()


@app.route("/upload", methods=["POST", "GET"])
def upload():
    return funcs.upload()


# #Have to test it and add more error handlers like 404
# @app.errorhandler(413)
# def request_entity_too_large(error):
#     return funcs.request_entity_too_large(error)

