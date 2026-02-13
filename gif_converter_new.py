from PIL import Image
import os

frames_dir = "frames"   # folder containing images
output_gif = "output3.gif"

# Get sorted list of images
images = sorted(
    [f for f in os.listdir(frames_dir) if f.endswith(".png")]
)

# Pick every 5th image starting from 0
selected_images = images[::10]

# selected_images = []
# selected_images.append(images[0])  # Ensure first image is included
# selected_images.append(images[19])
# selected_images.append(images[39])
# selected_images.append(images[59])
# selected_images.append(images[76])

# Ensure last image is included
if images[-1] not in selected_images:
    selected_images.append(images[-1])

# Load images
frames = [
    Image.open(os.path.join(frames_dir, img)).convert("RGB")
    for img in selected_images
]

durations = [80] * (len(frames) - 1) + [800]

# Save as GIF
frames[0].save(
    output_gif,
    save_all=True,
    append_images=frames[1:],
    duration=300,
    loop=0
)

print(f"GIF created with {len(frames)} frames: {output_gif}")