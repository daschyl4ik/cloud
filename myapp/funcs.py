from flask import render_template, url_for, redirect, flash, request
from flask_login import login_user, current_user, logout_user
from forms import LoginForm, RegisterForm, UploadFileForm
from models import Users, Photos
from werkzeug.security import generate_password_hash, check_password_hash
from cloud import db
from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, COMPRESSED_IMAGE_FOLDER, THUMBNAILS_FOLDER
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
        except Exception as e:
            db.session.rollback()
            print("Ошибка добавления в БД", str(e))

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


def update_image_name(filename, db_image_name, new_image_name):
    try:
        db_image_name = new_image_name
        db.session.commit()
        print("Image name updated")
    except Exception as e:
        print("image name was not updated", str(e))
        pass


def image_compress(filename, image_name):
    try:
        im = Image.open(UPLOAD_FOLDER + '/' + filename)
        compessed_image_path = os.path.join(COMPRESSED_IMAGE_FOLDER + image_name)
        im.save(compessed_image_path, optimize=True, quality=50, lossless = True)
        print("files compressed")
    except Exception as e:
        print("compression failed", str(e))
        pass


def create_thumbnail(filename, image_thumbnail_name):
    try:
        size = (256, 256)
        im = Image.open(os.path.join(UPLOAD_FOLDER, filename))
        image_width, image_height = im.size
        #crop the image to get square image for the thumbnail
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
    except Exception as e:
        print("Didn't image URL: ", str(e))
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
                #save to uploads folder
                uploaded_filename = os.path.join(
                    app.config["UPLOAD_FOLDER"], 
                    secure_filename(file.filename))
                file.save(uploaded_filename)
                u_id = current_user.id
                #image_datetime = get_datetime(file.filename) , date = image_datetime
                image = Photos(user_id = u_id, name = file.filename)
                db.session.add(image)
                db.session.flush()
                db.session.commit()
                print("Файлы добавлены в базу данных")
                image_id = image.id
                #for debug, to be deleted
                print(image_id)
                image_name = f'{str(current_user.id)}_{str(image_id)}_{secure_filename(file.filename)}'
                #update the name in db
                update_image_name(file.filename, image.name, image_name)
                # try:
                #     image.name = image_name
                #     db.session.commit()
                #     print("Image name updated")
                # except:
                #     print("image name was not updated")
                #     pass
                #compress image
                image_compress(file.filename, image_name)
                #create thumbnail
                thumbnail_image_name = f'{str(current_user.id)}_{str(image_id)}_thumbnail_{secure_filename(file.filename)}'
                create_thumbnail(file.filename, thumbnail_image_name)
                # datetime = get_datetime(file.filename)
                # print("date written is " + str(datetime))
                #удаляем загруженный ранее файл, он больше не нужен
                os.remove(uploaded_filename)
                #test
                compessed_image_path = os.path.join(COMPRESSED_IMAGE_FOLDER + image_name)
                minio_upload_image(image_name, compessed_image_path)
                image_url = get_image_url(image_name)
                print(image_url)
                thumbnail_image_path = os.path.join(THUMBNAILS_FOLDER + thumbnail_image_name)
                minio_upload_image(thumbnail_image_name, thumbnail_image_path)
                thumbnail_image_url = get_image_url(thumbnail_image_name)
                print(thumbnail_image_url)

            except Exception as e:
                flash ("Что-то пошло не так...", "error")
                print ("File not uploaded: ", str(e))
                return redirect(url_for("upload"))
        photos = Photos.query.filter_by(user_id=current_user.id).all()
        print(photos)            
        flash ("Файлы загружены", "success")
        return f'<img src="{image_url}" alt="image"><img src="{thumbnail_image_url}" alt="thumbnail_image">'
        #return redirect(url_for("upload"))

    return render_template("upload.html", form = form)


# photos = Photos.query.filter_by(user_id=current_user.id).all()
# print(photos)
