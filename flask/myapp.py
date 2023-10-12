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
from PIL import Image
from minio import Minio
from minio.error import S3Error
from flask_caching import Cache


DEBUG = True
UPLOAD_FOLDER = './static/images/temp/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
SECRET_KEY = os.urandom(20).hex()
COMPRESSED_IMAGE_FOLDER = './static/images/compressed/'
THUMBNAILS_PATH = './static/images/thumbnails/'


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 600
}



app = Flask(__name__)


# tell Flask to use the above defined config
app.config.from_mapping(config)
cache = Cache(app)


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
    name = db.Column(db.String, nullable = False)
    thumbnail_name = db.Column(db.String, nullable = True)
    image_date = db.Column(db.DateTime)


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
        else:
            flash ("Неверная пара email/пароль", "error")
            return redirect(url_for("login"))

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


@app.route("/photos", methods = ["GET"])
@login_required
def photos():
    user_photos = (
        Photos.query.filter_by(user_id=current_user.id)
        .order_by(Photos.image_date.desc())
        .all()
    )

    thumbnail_images_urls = [get_image_url(photo.thumbnail_name) for photo in user_photos]
    images_urls = [get_image_url(photo.name) for photo in user_photos]
    images_thumbnails_urls = zip(images_urls, thumbnail_images_urls)

    return render_template("photos.html", title="Фото", name = current_user.name, images_thumbnails_urls=images_thumbnails_urls)




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




def image_compress(filename, image_name):
    try:
        im = Image.open(os.path.join(UPLOAD_FOLDER, filename))
        compessed_image_path = os.path.join(COMPRESSED_IMAGE_FOLDER + image_name)
        im.save(compessed_image_path, optimize=True, quality=50, lossless = True)
        print("File compressed")
    except:
        print("Compression failed")
        pass

def crop_image(filename):
    try:
        im = Image.open(os.path.join(UPLOAD_FOLDER, filename))
        size = im.size
        image_width = size[0]
        image_height = size[1]
        if image_height > image_width:
            #вычисляем разницу между высотой и шириной, делим на 2
            total_crop_value = image_height - image_width
            crop_value = total_crop_value/2
            cropped_image = im.crop((0,crop_value,image_width, image_height - crop_value))
            cropped_image.save(os.path.join(THUMBNAILS_PATH + 'cropped.jpg'))
        elif image_width > image_height:
            #вычисляем разницу между высотой и шириной, делим на 2
            total_crop_value = image_width - image_height
            crop_value = total_crop_value/2
            im.crop(crop_value,0,image_width - crop_value, image_height)
            im.save(os.path.join(THUMBNAILS_PATH + 'cropped.jpg'))
        else:
            pass
    except:
        print('File not cropped')
        pass


def create_thumbnail(filename, image_thumbnail_name):
    try:
        size = (256, 256)
        im = Image.open(os.path.join(UPLOAD_FOLDER, filename))
        image_width, image_height = im.size
        #crop the image to get square image for the
        if image_height > image_width:
            total_crop_value = image_height - image_width
            crop_value = total_crop_value / 2
            cropped_image = im.crop((0, crop_value, image_width, image_height - crop_value))
        elif image_width > image_height:
            total_crop_value = image_width - image_height
            crop_value = total_crop_value / 2
            cropped_image = im.crop((crop_value, 0, image_width - crop_value, image_height))
        else:
            cropped_image = im
        
        cropped_image.thumbnail(size)
        cropped_image.save(os.path.join(THUMBNAILS_PATH, image_thumbnail_name))
        print('Thumbnail created')
    except Exception as e:
        print("Thumbnail creation failed:", str(e))
        pass


def get_datetime(filename):
    im = Image.open(UPLOAD_FOLDER + '/' + filename)
    exif = im._getexif()
    date_time_format = '%Y:%m:%d %H:%M:%S'
    try:
        datetimeoriginal = exif.get(36867) #когда изображение было создано
        #конвертируем из строки в datetime object
        datetime_original = datetime.strptime(datetimeoriginal, date_time_format)
        return datetime_original
    except:
        pass

    try:
        datetimedigitized = exif.get(36868) #когда изображение было отсканировано
        datetime_digitized =  datetime.strptime(datetimedigitized, date_time_format)
        return datetime_digitized
    except:
        pass

    try:
        datetimefilechanged = exif.get(306) #дата изменения изображения
        datetime_filechanged =  datetime.strptime(datetimefilechanged, date_time_format)
        return datetime_filechanged
    except:
        pass

    datetime_now = datetime.now()
    return datetime_now


def cyr_to_lat(string):
    legend = {
        'а': 'a',
        'б': 'b',
        'в': 'v',
        'г': 'g',
        'д': 'd',
        'е': 'e',
        'ё': 'yo',
        'ж': 'zh',
        'з': 'z',
        'и': 'i',
        'й': 'y',
        'к': 'k',
        'л': 'l',
        'м': 'm',
        'н': 'n',
        'о': 'o',
        'п': 'p',
        'р': 'r',
        'с': 's',
        'т': 't',
        'у': 'u',
        'ф': 'f',
        'х': 'h',
        'ц': 'ts',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'shch',
        'ъ': 'y',
        'ы': 'y',
        'ь': "'",
        'э': 'e',
        'ю': 'yu',
        'я': 'ya',
        'А': 'A',
        'Б': 'B',
        'В': 'V',
        'Г': 'G',
        'Д': 'D',
        'Е': 'E',
        'Ё': 'Yo',
        'Ж': 'Zh',
        'З': 'Z',
        'И': 'I',
        'Й': 'Y',
        'К': 'K',
        'Л': 'L',
        'М': 'M',
        'Н': 'N',
        'О': 'O',
        'П': 'P',
        'Р': 'R',
        'С': 'S',
        'Т': 'T',
        'У': 'U',
        'Ф': 'F',
        'Х': 'H',
        'Ц': 'Ts',
        'Ч': 'Ch',
        'Ш': 'Sh',
        'Щ': 'Shch',
        'Ъ': 'Y',
        'Ы': 'Y',
        'Ь': "'",
        'Э': 'E',
        'Ю': 'Yu',
        'Я': 'Ya',
        '—': '-',
    }
    new_string = ""
    for s in string:
        if s in legend:
            new_string += legend[s]
        elif s == " ":
            new_string += "_"
        else:
            new_string += s

    return new_string


#---------------------------------MINIO--------------
#____________________________________________________
#test public minio endpoint, to be changed
client = Minio (endpoint = 'play.min.io',
  access_key = 'Q3AM3UQ867SPQQA43P2F',
  secret_key = 'zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG',
  secure = True)

bucket_name = 'cloudnew'

#for debug only
if client.bucket_exists(bucket_name):
    print(bucket_name, "bucket exists.")
else:
    client.make_bucket(bucket_name)
    print(bucket_name, "bucket created.")

def minio_upload_image(object_name, file_path):
    result = client.fput_object(bucket_name, object_name, file_path)
    print('created: {0} with etag: {1}'.format (result.object_name, result.etag))


#----------------------CACHE--------------------
#____________________________________________________

#@cache.cached(timeout=3600, key_prefix = "image_url")
# def get_image_url(image_name):
#         # Generate a temporary URL for the image with 1 hour expiration time
#     client.presigned_get_object(
#         bucket_name,
#         image_name,
#         expires=3600  # 1 hour expiration time in seconds
#         )
#     # except S3Error as e:
#     #     pass
#         #return f'Error: {e}'
def get_image_url(image_name):
    try:
    # Generate a temporary URL, default expiry is 7 days
        url = client.presigned_get_object(bucket_name,image_name)
        # print(image_url)
        return url
    except:
        print("Get image URL: failed")
        pass


def update_image_name(image, new_image_name, new_image_thumbnail_name):
    try:
        image.name = new_image_name
        image.thumbnail_name = new_image_thumbnail_name
        db.session.commit()
        print("Image name updated")
    except:
        print("image name was not updated")
        pass




@app.route("/upload", methods=["POST", "GET"])
@login_required
def upload():
    form = UploadFileForm()
    if form.validate_on_submit():
        files = request.files.getlist("file")  # Get the list of files
        for file in files:
               
            if not allowed_file(file.filename):
                print(f"Skipping. {file.filename} (not allowed extension)")
                continue  # Skip to the next iteration without processing the invalid file
            
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                print(f"Skipping. {file.filename} exceeds the maximum allowed size of 16 MB")
                continue

            try:
                latin_filename = cyr_to_lat(file.filename)
                print(latin_filename)
                uploaded_filename = os.path.join(
                    app.config["UPLOAD_FOLDER"], 
                    secure_filename(latin_filename))
                file.save(uploaded_filename)
                u_id = current_user.id
                image_exif_date = get_datetime(latin_filename)
                print(image_exif_date)
                image = Photos(user_id = u_id, name = latin_filename, image_date = image_exif_date)
                db.session.add(image)
                db.session.flush()
                db.session.commit()
                print("Файлы добавлены в базу данных")
                image_id = image.id
                image_name = f'{str(current_user.id)}_{str(image_id)}_{secure_filename(latin_filename)}'
                #update the name in db
                image_thumbnail_name = f'{str(current_user.id)}_{str(image_id)}_thumbnail_{secure_filename(latin_filename)}'
                update_image_name(image, image_name, image_thumbnail_name)
                # try:
                #     image.name = image_name
                #     image.thumbnail_name = image_thumbnail_name
                #     db.session.commit()
                #     print("Image name updated")
                # except:
                #     print("image name was not updated")
                #     pass
                image_compress(latin_filename, image_name)
                #crop_image(latin_filename)
                create_thumbnail(latin_filename, image_thumbnail_name)
                datetime = get_datetime(latin_filename)                   
                print("date written is " + str(datetime))
                #удаляем загруженный ранее файл, он больше не нужен
                os.remove(uploaded_filename)
                #upload thumbnail and full size image to minio
                compessed_image_path = os.path.join(COMPRESSED_IMAGE_FOLDER + image_name)
                minio_upload_image(image_name, compessed_image_path)
                thumbnail_image_path = os.path.join(THUMBNAILS_PATH + image_thumbnail_name)
                minio_upload_image(image_thumbnail_name, thumbnail_image_path)

            except:
                flash ("Что-то пошло не так...", "error")
                return redirect(url_for("photos"))
        
        flash ("Файлы загружены", "success")
        return redirect(url_for("photos"))

    return render_template("upload.html", form = form)


@app.errorhandler(413)
def request_entity_too_large(error):
    flash ("Файл не должен превышать 16 Мб", "error")
    return redirect(url_for("photos"))
    


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