import os
import base64
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# ================= CONFIG =================
GIFS_DIR = "gifs"
FRAMES_RAW = "frames_raw"
FRAMES_SELECTED = "frames_selected"
FRAMES_EDITED = "frames_edited"
GIFS_FINAL = "gifs_final"

FRAME_SKIP = 15
FRAME_DURATION = 80
LAST_FRAME_DURATION = 800

XAI_API_KEY = os.getenv("XAI_API_KEY")  # 👈 change if needed
XAI_ENDPOINT = "https://api.x.ai/v1/images/edits"
MODEL = "grok-vision-beta"
# ========================================


def ensure_dirs():
    for d in [FRAMES_RAW, FRAMES_SELECTED, FRAMES_EDITED, GIFS_FINAL]:
        os.makedirs(d, exist_ok=True)


# ---------- 1. Extract GIF frames ----------
def extract_gif_frames(gif_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    gif = Image.open(gif_path)
    idx = 0

    while True:
        try:
            gif.seek(idx)
            frame = gif.convert("RGB")
            frame.save(os.path.join(out_dir, f"frame_{idx:04d}.png"))
            idx += 1
        except EOFError:
            break


# ---------- 2. Select frames ----------
def select_frames(raw_dir, selected_dir, skip):
    os.makedirs(selected_dir, exist_ok=True)

    images = sorted(f for f in os.listdir(raw_dir) if f.endswith(".png"))
    if not images:
        return []

    selected = images[::skip]
    if images[-1] not in selected:
        selected.append(images[-1])

    for img in selected:
        Image.open(os.path.join(raw_dir, img)).save(
            os.path.join(selected_dir, img)
        )

    return selected



import base64
import httpx
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
    timeout=httpx.Timeout(3600.0),
)

def grok_edit_image(input_path, output_path):
    if not os.getenv("XAI_API_KEY"):
        raise RuntimeError("XAI_API_KEY not set")

    # Read image
    with open(input_path, "rb") as f:
        img_bytes = f.read()

    # Convert to data URL (THIS IS THE KEY FIX)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    image_url = f"data:image/png;base64,{img_b64}"

    prompt = (
        "Change the shirt color from grey to pure white. "
        "Change the shorts color from black to dark green. "
        "Do not change image size, pose, lighting, background, "
        "or proportions. Preserve all details exactly."
        "remove the logo on the shirt and shorts."
    )

    response = client.responses.create(
        model="grok-4",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": image_url,
                        "detail": "high",
                    },
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )

    # Extract edited image
    for msg in response.output:
        for content in msg.content:
            if content["type"] == "output_image":
                out_b64 = content["image_base64"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(out_b64))
                return

    raise RuntimeError("❌ Grok did not return an image")

# ---------- 4. Process frames with AI ----------
def process_frames_with_ai(selected_dir, edited_dir):
    os.makedirs(edited_dir, exist_ok=True)

    frames = sorted(f for f in os.listdir(selected_dir) if f.endswith(".png"))

    for frame in frames:
        src = os.path.join(selected_dir, frame)
        dst = os.path.join(edited_dir, frame)

        if os.path.exists(dst):
            continue

        grok_edit_image(src, dst)


# ---------- 5. Build GIF ----------
def build_gif(frames_dir, output_gif):
    images = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    if not images:
        return

    frames = [
        Image.open(os.path.join(frames_dir, img)).convert("RGB")
        for img in images
    ]

    durations = [FRAME_DURATION] * (len(frames) - 1) + [LAST_FRAME_DURATION]

    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0
    )


# ---------- 6. Full pipeline ----------
def process_gif(gif_name):
    base = gif_name.replace(".gif", "")

    raw_dir = os.path.join(FRAMES_RAW, base)
    selected_dir = os.path.join(FRAMES_SELECTED, base)
    edited_dir = os.path.join(FRAMES_EDITED, base)
    final_gif = os.path.join(GIFS_FINAL, gif_name)

    if os.path.exists(final_gif):
        print(f"✅ Skipping (already processed): {gif_name}")
        return

    extract_gif_frames(os.path.join(GIFS_DIR, gif_name), raw_dir)
    select_frames(raw_dir, selected_dir, FRAME_SKIP)
    process_frames_with_ai(selected_dir, edited_dir)
    build_gif(edited_dir, final_gif)

    print(f"🎉 Done: {final_gif}")


# ---------- 7. Run ----------
if __name__ == "__main__":
    ensure_dirs()

    gifs = [f for f in os.listdir(GIFS_DIR) if f.endswith(".gif")]
    for gif in gifs:
        process_gif(gif)