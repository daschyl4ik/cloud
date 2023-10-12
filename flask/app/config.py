import os


DEBUG = True
SECRET_KEY = os.urandom(20).hex()
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///C:/repos/cloud/flask/app/instance/cloud.db'
 #'sqlite:///cloud.db'
#MAX_CONTENT_LENGTH = 16 * 1024 * 1024
MAX_FILE_SIZE = 16 * 1024 * 1024


#constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = './app/static/images/temp/'
COMPRESSED_IMAGE_FOLDER = './app/static/images/compressed/'
THUMBNAILS_FOLDER = './app/static/images/thumbnails/'
APP_LOG_FILE = 'cloudapp.log'


LOGIN_MESSAGE = "Войдите в аккаунт, чтобы просматривать содержимое страницы"
LOGIN_MESSAGE_CATEGORY = "success"

#test environment
# MINIO_ENDPOINT = 'play.min.io'
# MINIO_ACCESS_KEY = 'Q3AM3UQ867SPQQA43P2F'
# MINIO_SECRET_KEY = 'zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG'
# MINIO_BUCKET_NAME = 'cloudmain'

#when running in docker
# MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')
# MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
# MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY')
# MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME')

MINIO_ENDPOINT = '157.175.196.105:9000'
MINIO_ACCESS_KEY = 'myminioadmin'
MINIO_SECRET_KEY = 'myminioadmin'
MINIO_BUCKET_NAME = 'cloudmain'