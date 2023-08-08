from flask import render_template, url_for, redirect, flash, request
from flask_login import login_user, current_user, logout_user
from forms import LoginForm, RegisterForm, UploadFileForm
from models import Users, Photos
from werkzeug.security import generate_password_hash, check_password_hash
from cloud import db
from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, COMPRESSED_IMAGE_FOLDER, THUMBNAILS_PATH
from PIL import Image
import os
from datetime import datetime
from minio_connect import client, bucket_name
from cloud import app
from werkzeug.utils import secure_filename


def index():
    if current_user.is_authenticated:
        return redirect(url_for("photos"))
    return redirect(url_for("login"))


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


def photos():
    return render_template("photos.html", title="Фото", name = current_user.name)


def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("login"))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def image_compress(filename, image_name):
    try:
        im = Image.open(UPLOAD_FOLDER + '/' + filename)
        compessed_image_path = os.path.join(COMPRESSED_IMAGE_FOLDER + image_name)
        im.save(compessed_image_path, optimize=True, quality=50, lossless = True)
        print("files compressed")
    except:
        print("compression failed")
        pass


def create_thumbnail(filename, image_thumbnail_name):
    try:
        size = (256, 256)
        im = Image.open(UPLOAD_FOLDER + '/' + filename)
        im.thumbnail(size)
        im.save(os.path.join(THUMBNAILS_PATH + image_thumbnail_name))
        print('thumbnail created')
    except:
        print("thumbnail creation failed")
        pass


def get_datetime(filename):
    im = Image.open(UPLOAD_FOLDER + '/' + filename)
    exif = im._getexif()
    try:
        datetimeoriginal = exif.get(36867)
        return datetimeoriginal
    except:
        pass

    try:
        datetimedigitized = exif.get(36868)
        return datetimedigitized
    except:
        pass

    try:
        datetimefilechanged = exif.get(306)
        return datetimefilechanged
    except:
        pass

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string


def minio_upload_image(object_name, file_path):
    result = client.fput_object(bucket_name, object_name, file_path)
    print('created: {0} with etag: {1}'.format (result.object_name, result.etag))


def get_image_url(image_name):
    try:
    # Generate a temporary URL, default expiry is 7 days
        url = client.presigned_get_object(bucket_name,image_name)
        # print(image_url)
        return url
    except:
        print("Get image URL: failed")
        pass


def upload():
    form = UploadFileForm()
    if form.validate_on_submit():
        files = request.files.getlist("file")  # Get the list of files
        for file in files:
               
            if not allowed_file(file.filename):
                print(f"Skipping {file.filename} (not allowed extension)")
                continue  # Skip to the next iteration without processing the invalid file
        
            try:
                uploaded_filename = os.path.join(
                    app.config["UPLOAD_FOLDER"], 
                    secure_filename(file.filename))
                file.save(uploaded_filename)
                u_id = current_user.id
                image = Photos(user_id = u_id, name = file.filename)
                db.session.add(image)
                db.session.flush()
                db.session.commit()
                print("Файлы добавлены в базу данных")
                image_id = image.id
                print(image_id)
                image_name = f'{str(current_user.id)}_{str(image_id)}_{secure_filename(file.filename)}'
                #update the name in db
                try:
                    image.name = image_name
                    db.session.commit()
                    print("Image name updated")
                except:
                    print("image name was not updated")
                    pass
                image_compress(file.filename, image_name)
                image_thumbnail_name = f'{str(current_user.id)}_{str(image_id)}_thumbnail_{secure_filename(file.filename)}'
                create_thumbnail(file.filename, image_thumbnail_name)
                datetime = get_datetime(file.filename)
                print("date written is " + str(datetime))
                #удаляем загруженный ранее файл, он больше не нужен
                os.remove(uploaded_filename)
                #test
                compessed_image_path = os.path.join(COMPRESSED_IMAGE_FOLDER + image_name)
                minio_upload_image(image_name, compessed_image_path)
                image_url = get_image_url(image_name)
                print(image_url)
                thumbnail_image_path = os.path.join(THUMBNAILS_PATH + image_thumbnail_name)
                minio_upload_image(image_thumbnail_name, thumbnail_image_path)
                thumbnail_image_url = get_image_url(image_thumbnail_name)
                print(thumbnail_image_url)

            except:
                flash ("Что-то пошло не так...", "error")
                return redirect(url_for("upload"))
                    
        flash ("Файлы загружены", "success")
        return f'<img src="{image_url}" alt="image"><img src="{thumbnail_image_url}" alt="thumbnail_image">'
        #return redirect(url_for("upload"))
    return render_template("upload.html", form = form)

