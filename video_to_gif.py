import os
import pandas as pd
import requests
from moviepy.editor import VideoFileClip
from tqdm import tqdm

# ================= CONFIG =================
CSV_PATH = "analyzed_exercises.csv"
VIDEO_COL = "video_url"

VIDEOS_DIR = "videos"
GIFS_DIR = "gifs"

GIF_FPS = 10
GIF_WIDTH = 480   # resize for lighter gifs
# =========================================

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(GIFS_DIR, exist_ok=True)


def download_video(url, out_path):
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def convert_to_gif(video_path, gif_path):
    with VideoFileClip(video_path) as clip:
        clip = clip.resize(width=GIF_WIDTH)
        clip.write_gif(gif_path, fps=GIF_FPS)


def main():
    df = pd.read_csv(CSV_PATH)

    urls = df[VIDEO_COL].dropna().unique()

    for url in tqdm(urls, desc="Processing videos"):
        filename = os.path.basename(url)
        name, _ = os.path.splitext(filename)

        video_path = os.path.join(VIDEOS_DIR, filename)
        gif_path = os.path.join(GIFS_DIR, f"{name}.gif")

        # ---- Skip if GIF already exists (append behavior) ----
        if os.path.exists(gif_path):
            continue

        # ---- Download if missing ----
        if not os.path.exists(video_path):
            try:
                download_video(url, video_path)
            except Exception as e:
                print(f"Failed to download {url}: {e}")
                continue

        # ---- Convert to GIF ----
        try:
            convert_to_gif(video_path, gif_path)
        except Exception as e:
            print(f"Failed to convert {video_path}: {e}")


if __name__ == "__main__":
    main()