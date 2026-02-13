import csv
import os
import uuid
import requests
import boto3
import imageio
from urllib.parse import urlparse
import mimetypes
from dotenv import load_dotenv

load_dotenv()

# ==========================
# CONFIG
# ==========================
INPUT_CSV = "analyzed_exercises.csv"  # CSV with video_url_male column
OUTPUT_CSV = "output_analyzed.csv"    # CSV with gif_url column

S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
S3_BASE_PATH = "exercises"
TMP_DIR = "tmp"

os.makedirs(TMP_DIR, exist_ok=True)

# ==========================
# S3 CLIENT
# ==========================
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv("AWS_REGION")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

s3 = session.client("s3")

# ==========================
# UTILS
# ==========================
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

def build_s3_url(s3_key: str) -> str:
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

def filename_from_url(url: str) -> str:
    return os.path.basename(urlparse(url).path)

def is_valid_file_url(url: str) -> bool:
    path = urlparse(url).path
    filename = os.path.basename(path)
    return bool(filename)

# ==========================
# VIDEO → GIF
# ==========================
def convert_video_to_gif(video_local_path: str) -> str:
    gif_filename = os.path.join(TMP_DIR, f"{uuid.uuid4()}.gif")
    reader = imageio.get_reader(video_local_path)
    fps = reader.get_meta_data().get("fps", 10)

    frames = []
    for i, frame in enumerate(reader):
        frames.append(frame)

    imageio.mimsave(gif_filename, frames, fps=fps)
    reader.close()
    return gif_filename

# ==========================
# MAIN LOOP
# ==========================
with open(INPUT_CSV, newline="", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ["gif_url"]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            gif_s3_url = ""

            video_url = row.get("video_url_male")
            if video_url and is_valid_file_url(video_url):
                try:
                    video_name = filename_from_url(video_url)
                    video_local = os.path.join(TMP_DIR, video_name)

                    print(f"⬇️ Downloading video: {video_url}")
                    download_file(video_url, video_local)

                    print(f"🎬 Converting video to GIF")
                    gif_local = convert_video_to_gif(video_local)

                    gif_s3_key = f"{S3_BASE_PATH}/gifs/{os.path.basename(gif_local)}"
                    print(f"⬆️ Uploading GIF to S3: {gif_s3_key}")
                    upload_to_s3(gif_local, gif_s3_key)

                    gif_s3_url = build_s3_url(gif_s3_key)

                    # cleanup
                    os.remove(video_local)
                    os.remove(gif_local)

                except Exception as e:
                    print(f"❌ Failed for {video_url}: {e}")

            row["gif_url"] = gif_s3_url
            writer.writerow(row)

print("✅ Done. GIFs uploaded and CSV updated")