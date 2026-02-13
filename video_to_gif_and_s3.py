import os
import uuid
import requests
import imageio
import boto3
import pandas as pd

# ==========================
# CONFIG
# ==========================
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")

INPUT_CSV = "analyzed_exercises.csv"   # CSV with video_url_male column
OUTPUT_CSV = "output_analyzed.csv"     # CSV with gif_url column

# ==========================
# S3 CLIENT USING SESSION
# ==========================
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

s3 = session.client("s3")

# ==========================
# DOWNLOAD VIDEO
# ==========================
def download_video(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    filename = f"{uuid.uuid4()}.mp4"
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    return filename

# ==========================
# CONVERT VIDEO TO GIF
# ==========================
def convert_to_gif(video_path):
    gif_filename = video_path.replace(".mp4", ".gif")

    reader = imageio.get_reader(video_path)
    fps = reader.get_meta_data().get("fps", 10)

    frames = []
    for i, frame in enumerate(reader):
        frames.append(frame)

    imageio.mimsave(gif_filename, frames, fps=fps)
    reader.close()

    return gif_filename

# ==========================
# UPLOAD TO S3
# ==========================
def upload_to_s3(file_path):
    s3_key = f"gifs/{os.path.basename(file_path)}"

    s3.upload_file(
        file_path,
        S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": "image/gif"},
    )

    gif_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
    return gif_url

# ==========================
# MAIN PROCESS FUNCTION
# ==========================
def process_videos(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    gif_urls = []

    for url in df['video_url_male']:
        try:
            print(f"Processing: {url}")
            video_file = download_video(url)
            gif_file = convert_to_gif(video_file)
            gif_url = upload_to_s3(gif_file)

            gif_urls.append(gif_url)

            # cleanup
            os.remove(video_file)
            os.remove(gif_file)

        except Exception as e:
            print(f"Failed for {url}: {e}")
            gif_urls.append(None)

    df['gif_url'] = gif_urls
    df.to_csv(output_csv, index=False)
    print(f"✅ Done. CSV saved to {output_csv}")

# ==========================
# USAGE
# ==========================
if __name__ == "__main__":
    process_videos(INPUT_CSV, OUTPUT_CSV)