from minio import Minio
from config import ENDPOINT, ACCESS_KEY, SECRET_KEY_MINIO, BUCKET_NAME


client = Minio (endpoint = ENDPOINT,
  access_key = ACCESS_KEY,
  secret_key = SECRET_KEY_MINIO,
  secure = True)

bucket_name = BUCKET_NAME

#for debug only
if client.bucket_exists(bucket_name):
    print(bucket_name, "bucket exists.")
else:
    client.make_bucket(bucket_name)
    print(bucket_name, "bucket created.")
