"""
s3_uploader.py
--------------
Uploads processed Parquet files to AWS S3 (raw and processed zones).
"""

import os
import boto3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "bomb-transistor-pipeline")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")


def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def upload_file(local_path: str, s3_key: str, bucket: str = S3_BUCKET):
    s3 = get_s3_client()
    logger.info(f"Uploading {local_path} → s3://{bucket}/{s3_key}")
    s3.upload_file(local_path, bucket, s3_key)
    logger.info(f"✅ Uploaded: s3://{bucket}/{s3_key}")


def upload_raw_hdf5(local_path: str):
    filename = Path(local_path).name
    s3_key = f"raw/bomb/{filename}"
    upload_file(local_path, s3_key)


def upload_processed_parquet(local_path: str):
    filename = Path(local_path).name
    s3_key = f"processed/bomb/{filename}"
    upload_file(local_path, s3_key)


if __name__ == "__main__":
    raw_file = "./data/raw/Technology_A_data.hdf5"
    parquet_file = "./data/parquet/bomb_transistor_flat.parquet"

    if os.path.exists(raw_file):
        upload_raw_hdf5(raw_file)

    if os.path.exists(parquet_file):
        upload_processed_parquet(parquet_file)
