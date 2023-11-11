from minio import Minio
from . import config

client = Minio (endpoint = config.MINIO_ENDPOINT,
  access_key = config.MINIO_ACCESS_KEY,
  secret_key = config.MINIO_SECRET_KEY,
  secure = True) #to access http

bucket_name = config.MINIO_BUCKET_NAME

#for debug only
if client.bucket_exists(bucket_name):
    print(bucket_name, "bucket exists.")
else:
    client.make_bucket(bucket_name)
    print(bucket_name, "bucket created.")
