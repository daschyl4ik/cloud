from flask import render_template, url_for, redirect, flash, request
from flask_login import login_user, current_user, logout_user
from . import forms, models, db, config, minio_connect, app
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import os
from datetime import datetime
from werkzeug.utils import secure_filename


def index():
    if current_user.is_authenticated:
        return redirect(url_for("photos"))
    return redirect(url_for("login"))


def login():
    if current_user.is_authenticated:
        return redirect(url_for("photos"))
    
    form = forms.LoginForm()
    #if the data is valid upon checking by validators and sent via POST
    if form.validate_on_submit():
        try:
        #get the user's data from db
            user = models.Users.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.psw, form.psw.data):
                rm = form.remember.data
                login_user(user, remember=rm)
                return redirect(url_for("photos"))
            elif not user:
                flash ("Пользатель с таким email не зарегистрирован", "error")
                return redirect(url_for("login"))
            else:
                flash ("Неверный пароль", "error")
                return redirect(url_for("login"))
        except Exception as e:
            print("Ошибка БД: " + str(e))
            return redirect(url_for("login"))
    return render_template("login.html", title="Авторизация", form = form)


def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        try:
            user = models.Users.query.filter_by(email=form.email.data).first()
            if user:
                  flash("Пользователь с таким email уже зарегистрирован", "error")  
            hash = generate_password_hash(form.psw.data)
            u = models.Users(email=form.email.data, psw = hash, name = form.name.data)
            db.session.add(u)
            db.session.flush()
            db.session.commit()
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            print("Ошибка БД: " + str(e))
            return redirect(url_for("register"))

    return render_template("register.html", title = "Регистрация", form = form)


def photos():
    user_photos = (
        models.Photos.query.filter_by(user_id=current_user.id)
        .order_by(models.Photos.image_date.desc())
        .all()
    )
    
    thumbnail_images_urls = [get_image_url(photo.thumbnail_name) for photo in user_photos]
    images_urls = [get_image_url(photo.name) for photo in user_photos]
    images_thumbnails_urls = zip(images_urls, thumbnail_images_urls)

    return render_template("photos.html", title="Фото", name = current_user.name, images_thumbnails_urls=images_thumbnails_urls)



def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("login"))

#functions below are used within the upload
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

#if a file has cyrilic letters or '—'(assigned automatically by windows when a file is copied), upload fails. To fix, we will change the problematic symbols:
def cyr_to_lat(string):
    legend = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
        'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': 'y', 'ы': 'y', 'ь': "'", 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y',
        'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F',
        'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': 'Y', 'Ы': 'Y', 'Ь': "'", 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
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

#to have a unique name for every file uploaded
def update_image_name(image, new_image_name, new_image_thumbnail_name):
    try:
        image.name = new_image_name
        image.thumbnail_name = new_image_thumbnail_name
        db.session.commit()
        print("Image name updated")
    except Exception as e:
        print("image name was not updated", str(e))

#compress an image
def image_compress(filename, image_name):
    try:
        im = Image.open(config.UPLOAD_FOLDER + '/' + filename)
        compessed_image_path = os.path.join(config.COMPRESSED_IMAGE_FOLDER + image_name)
        im.save(compessed_image_path, optimize=True, quality=50, lossless = True)
        print("files compressed")
    except Exception as e:
        print("compression failed", str(e))

#create a thumbnail
def create_thumbnail(filename, image_thumbnail_name):
    try:
        size = (256, 256)
        im = Image.open(os.path.join(config.UPLOAD_FOLDER, filename))
        image_width, image_height = im.size
        #crop the image to get a square for a nice thumbnail
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
        cropped_image.save(os.path.join(config.THUMBNAILS_FOLDER, image_thumbnail_name))
        print('Thumbnail created')
    except Exception as e:
        print("Thumbnail creation failed:", str(e))

#try to get a date from exif data if available to enhance sorting
def get_datetime(filename):
    date_time_format = '%Y:%m:%d %H:%M:%S'
    im = Image.open(os.path.join(config.UPLOAD_FOLDER, filename))
    exif = im._getexif()
    try:
        #when an image was created
        datetimeoriginal = exif.get(36867)
        #convert from the string to the datetime object
        datetime_original = datetime.strptime(datetimeoriginal, date_time_format)
        return datetime_original
    except:
        pass

    try:
        #when an image was scanned 
        datetimedigitized = exif.get(36868)
        datetime_digitized =  datetime.strptime(datetimedigitized, date_time_format)
        return datetime_digitized
    except:
        pass

    try:
        #when an image was modified
        datetimefilechanged = exif.get(306)
        datetime_filechanged =  datetime.strptime(datetimefilechanged, date_time_format)
        return datetime_filechanged
    except:
        pass

    datetime_now = datetime.now()
    return datetime_now

#upload an image to minio
def minio_upload_image(object_name, file_path):
    try:
        result = minio_connect.client.fput_object(minio_connect.bucket_name, object_name, file_path)
        print('created: {0} with etag: {1}'.format (result.object_name, result.etag))
    except Exception as e:
        print("Couldn't upload file to minio ", str(e))

# generate a temporary URL for an object in minio, default expiry is 7 days
def get_image_url(image_name):
    try:
        url = minio_connect.client.presigned_get_object(minio_connect.bucket_name,image_name)
        return url
    except Exception as e:
        print("Didn't get image URL: ", str(e))


def upload():
    form = forms.UploadFileForm()
    if form.validate_on_submit():
        #get the list of files chosen
        files = request.files.getlist("file") 
        for file in files:
               
            if not allowed_file(file.filename):
                print(f"Skipping {file.filename} (not allowed extension)")
                #skip to the next iteration without processing the invalid file
                continue
                
            #if a file exceeds the size set, continue with other files    
            #if file.content_length > app.config['MAX_CONTENT_LENGTH']:
            if file.content_length > config.MAX_FILE_SIZE:
                print(f"Skipping. {file.filename} exceeds the maximum allowed size of 16 MB")
                continue

            try:
                #trasliterate a filename
                latin_filename = cyr_to_lat(file.filename)
                #save to uploads folder
                uploaded_filename = os.path.join(config.UPLOAD_FOLDER, secure_filename(latin_filename))
                #uploaded_filename = os.path.join(
                #    config.UPLOAD_FOLDER, 
                 #   secure_filename(latin_filename))
                try:
                    file.save(uploaded_filename)
                except:
                    print("it didn't work")
                u_id = current_user.id
                #get exif date
                image_exif_date = get_datetime(latin_filename)
                image = models.Photos(user_id = u_id, name = latin_filename, image_date = image_exif_date)
                #add to database
                db.session.add(image)
                db.session.flush()
                db.session.commit()
                print("Файлы добавлены в базу данных")
                image_id = image.id
                image_name = f'{str(current_user.id)}_{str(image_id)}_{secure_filename(latin_filename)}'
                image_thumbnail_name = f'{str(current_user.id)}_{str(image_id)}_thumbnail_{secure_filename(latin_filename)}'
                #update image name in db
                update_image_name(image, image_name, image_thumbnail_name)
                #compress image
                image_compress(latin_filename, image_name)
                #create thumbnail
                create_thumbnail(latin_filename, image_thumbnail_name)
                #delete the original file saved to temp
                os.remove(uploaded_filename)
                #upload thumbnail and full size image to minio
                compessed_image_path = os.path.join(config.COMPRESSED_IMAGE_FOLDER + image_name)
                minio_upload_image(image_name, compessed_image_path)
                thumbnail_image_path = os.path.join(config.THUMBNAILS_FOLDER + image_thumbnail_name)
                minio_upload_image(image_thumbnail_name, thumbnail_image_path)

            except Exception as e:
                flash ("Ошибка: " + str(e), "error")
                return redirect(url_for("upload"))
                
        flash ("Файлы загружены", "success")
        return redirect(url_for("photos"))

    return render_template("upload.html", form = form)