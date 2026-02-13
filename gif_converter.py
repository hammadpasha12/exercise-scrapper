import imageio

video_path = "https://static.virtuagym.com/videos/2023_id3151m.mp4"
gif_path = "output2.gif"

reader = imageio.get_reader(video_path)
fps = reader.get_meta_data()['fps']

frames = []
for frame in reader:
    frames.append(frame)

imageio.mimsave(gif_path, frames, fps=fps)
