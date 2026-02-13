from PIL import Image
import os

gif_path = "output2.gif"
output_dir = "frames"

os.makedirs(output_dir, exist_ok=True)

gif = Image.open(gif_path)

for i in range(gif.n_frames):
    gif.seek(i)
    frame = gif.convert("RGBA")  # keep transparency
    frame.save(f"{output_dir}/frame_{i:03d}.png")

print(f"Extracted {gif.n_frames} frames")
