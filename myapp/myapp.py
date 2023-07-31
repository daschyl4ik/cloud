from flask import Flask, render_template, url_for, request, flash, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm, UploadFileForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os
#for uploading pictures
from werkzeug.utils import secure_filename
#to return the uploaded image
from flask import send_from_directory


DEBUG = True
UPLOAD_FOLDER = './static/images/temp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
SECRET_KEY = os.urandom(20).hex()

app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY #"u863f45fac06ee7fdbe526410a398f3e82dd77184"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cloud.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#max file size is 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)


login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Войдите в аккаунт, чтобы просматривать содержимое страницы"
login_manager.login_message_category = "success"

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Users.query.get(int(user_id))


#таблица для регистрации юзеров
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    psw = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(20), nullable = False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<users {self.id}>"

#таблица для хранения фото:
class Photos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    thumbnail = db.Column(db.LargeBinary)
    minio_url = db.Column(db.String)

#create db
with app.app_context():
    db.create_all()

@app.route("/")
@app.route("/index")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("photos"))
    return redirect(url_for("login"))


@app.route("/login", methods =["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("photos"))
    
    form = LoginForm()
    #если данные введены корректно(валидаторы) и отправлены по пост запросу
    if form.validate_on_submit():
             #получаем инфу по пользователю из дб по мейлу
        user = Users.query.filter_by(email=form.email.data).first()
            #если инфа пользователю получена и пароль ок
        if user and check_password_hash(user.psw, form.psw.data):
            rm = form.remember.data
            login_user(user, remember=rm)
        return redirect(url_for("photos"))
        flash ("Неверная пара email/пароль", "error")
               
    return render_template("login.html", title="Авторизация", form = form)
        

@app.route("/register", methods =["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = Users.query.filter_by(email=form.email.data).first()
            if user:
                  flash("Пользователь с таким email уже зарегистрирован", "error")  
            hash = generate_password_hash(form.psw.data)
            u = Users(email=form.email.data, psw = hash, name = form.name.data)
            db.session.add(u)
            db.session.flush()
            db.session.commit()
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            print("Ошибка добавления в БД")

    return render_template("register.html", title = "Регистрация", form = form)


@app.route("/photos")
@login_required
def photos():
    return render_template("photos.html", title="Фото", name = current_user.name)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("login"))


#check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST", "GET"])
def upload():
    form = UploadFileForm()
    if form.validate_on_submit():
        files = request.files.getlist("file")  # Get the list of files
        for file in files:
               
            if not allowed_file(file.filename):
                print(f"Skipping {file.filename} (not allowed extension)")
                continue  # Skip to the next iteration without processing the invalid file
        
            try:
                file.save(os.path.join(
                    app.config["UPLOAD_FOLDER"], 
                    secure_filename(file.filename)
                    ))

            except:
                flash ("Что-то пошло не так...", "error")
                return redirect(url_for("upload"))
                    
        flash ("Файлы загружены", "success")
        return redirect(url_for("upload"))
    return render_template("upload.html", form = form)


@app.errorhandler(413)
def request_entity_too_large(error):
    flash ("Файл не должен превышать 16 Мб", "error")
    return redirect(url_for("upload"))
    



#errors:
#413 - too large
#7z file keeps on spinning. uploading? should not
#files with the same names are changed. check if the filename exists!
#if several files none will be uploaded

if __name__ == "__main__":
    app.run(debug=True)


######################################
#Чтение данных из ДБ с sql alchemy
# Users.query.all()    __repr__() - как возвращать значения
# [<users 1>, <users 2>, <users 3>]

# res = Users.query.all()
# получить мейл:
# res[0].email

# показать первый в списке:
# f = Users.query.first()
# f.id

# users.query.filter_by(id=2).all()
# [<users 2>]

# users.query.filter(Users.id == 1).all()
# users.query.filter(Users.id > 1).all()

# users.query.limit(2).all()

# users.query.order_by(users.email).all()

# users.query.order_by(users.email.desc()).all()

# users.query.get(2)

#res = db.session.query(Users, Profiles).join(Profiles, Users.id == Profiles.user_id).all()

#pr = db.relationship("Profiles", backref = "users", uselist=False)

#############################