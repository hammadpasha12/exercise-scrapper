import csv
import os
import uuid
import requests
import boto3
import subprocess
from urllib.parse import urlparse
import mimetypes
from dotenv import load_dotenv

load_dotenv()

# ==========================
# CONFIG
# ==========================
INPUT_CSV = "analyzed_exercises.csv"
OUTPUT_CSV = "output_analyzed.csv"

S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
S3_BASE_PATH = "exercises"
TMP_DIR = "tmp"

FFMPEG_PATH = r"C:\Users\User\Downloads\ffmpeg-2026-02-09-git-9bfa1635ae-full_build\ffmpeg-2026-02-09-git-9bfa1635ae-full_build\bin\ffmpeg.exe"

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
# VIDEO → GIF USING FFMPEG
# ==========================
def convert_video_to_gif_ffmpeg(video_local_path: str) -> str:
    gif_filename = os.path.join(TMP_DIR, f"{uuid.uuid4()}.gif")
    command = [
        FFMPEG_PATH,
        "-i", video_local_path,
        "-vf", "fps=30,scale=480:-1:flags=lanczos",
        "-loop", "0",
        gif_filename
    ]
    subprocess.run(command, check=True)
    return gif_filename

# ==========================
# MAIN LOOP
# ==========================
counter = 0

with open(INPUT_CSV, newline="", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ["gif_url"]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        print("🚀 Starting upload to S3...")
        for row in reader:
            gif_s3_url = ""

            video_url = row.get("video_url_male")
            if video_url and is_valid_file_url(video_url):
                try:
                    counter += 1
                    video_name = filename_from_url(video_url)
                    video_local = os.path.join(TMP_DIR, video_name)

                    print(f"⬇️ [{counter}] Downloading video: {video_url}")
                    download_file(video_url, video_local)

                    print(f"🎬 [{counter}] Converting video to GIF using FFmpeg")
                    gif_local = convert_video_to_gif_ffmpeg(video_local)

                    gif_s3_key = f"{S3_BASE_PATH}/gifs/{os.path.basename(gif_local)}"
                    print(f"⬆️ [{counter}] Uploading GIF to S3: {gif_s3_key}")
                    upload_to_s3(gif_local, gif_s3_key)

                    gif_s3_url = build_s3_url(gif_s3_key)
                    print(f"✅ [{counter}] Uploaded GIF URL: {gif_s3_url}")

                    # cleanup
                    os.remove(video_local)
                    os.remove(gif_local)

                except Exception as e:
                    print(f"❌ [{counter}] Failed for {video_url}: {e}")

            row["gif_url"] = gif_s3_url
            writer.writerow(row)

print("✅ All GIFs uploaded and CSV updated.")