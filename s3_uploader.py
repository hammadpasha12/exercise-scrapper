import csv
import os
import requests
import boto3
from urllib.parse import urlparse
from dotenv import load_dotenv
import mimetypes

load_dotenv()

INPUT_CSV = "output_batch_1.csv"
OUTPUT_CSV = "new_output_batch_1.csv"

S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
S3_BASE_PATH = "exercises"
TMP_DIR = "tmp"
# ------------------------

os.makedirs(TMP_DIR, exist_ok=True)

s3 = boto3.client("s3")

count=1

def download_file(url: str, local_path: str):
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def upload_to_s3(local_path: str, s3_key: str):
    content_type, _ = mimetypes.guess_type(local_path)

    s3.upload_file(
        local_path,
        S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": content_type or "application/octet-stream"}
    )


def filename_from_url(url: str) -> str:
    return os.path.basename(urlparse(url).path)


def build_s3_url(s3_key: str) -> str:
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"


def is_valid_file_url(url: str) -> bool:
    """
    Returns True if URL points to an actual file, not just a base path.
    """
    path = urlparse(url).path
    filename = os.path.basename(path)
    return bool(filename)  # True if filename exists


with open(INPUT_CSV, newline="", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)

    fieldnames = reader.fieldnames + [
        "s3_video_url",
        "s3_thumbnail_url",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        print("🚀 Starting upload to S3...")
        for row in reader:
            print(f"🔄 Processing exercise {count}: {row.get('name')}")
            count += 1
            
            s3_video_url = ""
            s3_thumbnail_url = ""

            video_url = row.get("video_url")
            thumbnail_url = row.get("thumbnail_url")

            # ---------- VIDEO ----------
            if video_url and is_valid_file_url(video_url):
                video_name = filename_from_url(video_url)
                video_local = os.path.join(TMP_DIR, video_name)
                video_s3_key = f"{S3_BASE_PATH}/videos/{video_name}"

                print(f"⬇️ Downloading video: {video_url}")
                download_file(video_url, video_local)

                print(f"⬆️ Uploading video to S3: {video_s3_key}")
                upload_to_s3(video_local, video_s3_key)

                s3_video_url = build_s3_url(video_s3_key)
                os.remove(video_local)

            # ---------- THUMBNAIL ----------
            if thumbnail_url and is_valid_file_url(thumbnail_url):
                thumb_name = filename_from_url(thumbnail_url)
                thumb_local = os.path.join(TMP_DIR, thumb_name)
                thumb_s3_key = f"{S3_BASE_PATH}/thumbnails/{thumb_name}"

                print(f"⬇️ Downloading thumbnail: {thumbnail_url}")
                download_file(thumbnail_url, thumb_local)

                print(f"⬆️ Uploading thumbnail to S3: {thumb_s3_key}")
                upload_to_s3(thumb_local, thumb_s3_key)

                s3_thumbnail_url = build_s3_url(thumb_s3_key)
                os.remove(thumb_local)

            # Add new columns
            row["s3_video_url"] = s3_video_url
            row["s3_thumbnail_url"] = s3_thumbnail_url

            writer.writerow(row)


print("✅ Upload complete & CSV updated with S3 URLs")
