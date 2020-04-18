from django.conf import settings
import boto3
from botocore.config import Config

def s3_upload_creds(filename, attachment):
    s3 = boto3.client(
        's3',
        aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME, 
        config=Config(signature_version='s3v4')
        )
    conditions = [{"acl": "public-read"}]
    if attachment:
        conditions.append(["starts-with", "$Content-Disposition", ""])
    return s3.generate_presigned_post(
        Bucket = settings.AWS_STORAGE_BUCKET_NAME,
        Key = filename,
        Conditions = conditions
    )
