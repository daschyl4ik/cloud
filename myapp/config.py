import os


DEBUG = True
SECRET_KEY = os.urandom(20).hex()
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///cloud.db'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024


# CACHE_TYPE = 'SimpleCache'
# CACHE_DEFAULT_TIMEOUT = 300 

#constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = './static/images/temp/'
COMPRESSED_IMAGE_FOLDER = './static/images/compressed/'
THUMBNAILS_PATH = './static/images/thumbnails/'


LOGIN_MESSAGE = "Войдите в аккаунт, чтобы просматривать содержимое страницы"
LOGIN_MESSAGE_CATEGORY = "success"

#for minio
ENDPOINT = 'play.min.io'
ACCESS_KEY = 'Q3AM3UQ867SPQQA43P2F'
SECRET_KEY_MINIO = 'zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG'
BUCKET_NAME = 'cloudmain'