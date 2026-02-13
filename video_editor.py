import cv2
import numpy as np
from moviepy.editor import VideoFileClip

def change_shirt_color(frame):
    frame = frame.copy()
    h, w, _ = frame.shape

    # ---------- 1. Manual shirt polygon ----------
    shirt_poly = np.array([[
        (int(0.32*w), int(0.12*h)),  # left neck
        (int(0.60*w), int(0.12*h)),  # right neck
        (int(0.68*w), int(0.32*h)),  # right shoulder
        (int(0.62*w), int(0.50*h)),  # right waist
        (int(0.40*w), int(0.50*h)),  # left waist
        (int(0.28*w), int(0.32*h)),  # left shoulder
    ]], dtype=np.int32)

    shirt_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(shirt_mask, shirt_poly, 255)

    # ---------- 2. HSV refinement inside shirt ----------
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_gray = np.array([0, 0, 110])
    upper_gray = np.array([180, 55, 240])
    color_mask = cv2.inRange(hsv, lower_gray, upper_gray)

    final_mask = cv2.bitwise_and(color_mask, shirt_mask)

    # ---------- 3. Morphological smoothing ----------
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)

    # ---------- 4. Recolor ----------
    target_hue = 110   # blue
    target_sat = 170

    hsv[..., 0] = np.where(final_mask > 0, target_hue, hsv[..., 0])
    hsv[..., 1] = np.where(final_mask > 0, target_sat, hsv[..., 1])

    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


clip = VideoFileClip(
    "D:\\hammad\\projects\\exercise_scrapper\\2023_db006.mp4"
)

edited = clip.fl_image(change_shirt_color)

edited.write_videofile(
    "output.mp4",
    codec="libx264",
    audio_codec="aac"
)