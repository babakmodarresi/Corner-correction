import pygame
import cv2
import numpy as np
import json
import os
import vlc
from gpiozero import MotionSensor
import time
import threading


# --- Configuration ---
VIDEO_PATH = "2.mp4"
CORNERS_FILE = "corners.json"

# Motion controlled audio settings
NO_MOTION_TIMEOUT = 2.0
MIN_VOLUME = 30
MAX_VOLUME = 100
VOLUME_STEP = 5

# Initialize VLC and motion sensor
pir = MotionSensor(10)
instance = vlc.Instance(" --input-repeat=999999999 -q --no-xlib")
last_motion = time.time()


def load_corners():
   try:
       with open(CORNERS_FILE, 'r') as f:
           return json.load(f)
   except (FileNotFoundError, json.JSONDecodeError):
       print(f"Warning: Could not read {CORNERS_FILE}. Will try again.")
       return None


def play_video(video_file_path):
    """Play video with VLC while adjusting volume based on motion."""
    global last_motion

    print(f"🎬 attempting to play: {video_file_path}")
    if not os.path.exists(video_file_path):
        print(f"❌ Error: no video found at {video_file_path}")
        return

    player = instance.media_player_new()
    media = instance.media_new(video_file_path)
    player.set_media(media)
    player.audio_set_volume(MAX_VOLUME)

    if player.play() == -1:
        print(f"❌ Error: could not play {video_file_path}")
        player.release()
        return

    print(f"▶️ Playing: {video_file_path}")
    time.sleep(1)

    while player.is_playing():
        if pir.is_active:
            last_motion = time.time()

        current_time = time.time()
        current_volume = player.audio_get_volume()

        if current_time < last_motion + NO_MOTION_TIMEOUT:
            if current_volume < MAX_VOLUME:
                new_volume = min(current_volume + VOLUME_STEP, MAX_VOLUME)
                if new_volume != current_volume:
                    print("new volume: ", new_volume)
                    player.audio_set_volume(new_volume)
        else:
            if current_volume > MIN_VOLUME:
                new_volume = max(current_volume - VOLUME_STEP, MIN_VOLUME)
                if new_volume != current_volume:
                    print("new volume: ", new_volume)
                    player.audio_set_volume(new_volume)
        time.sleep(0.2)

    print(f"⏹️ Finished playing: {video_file_path}")
    player.release()



def main():
    pygame.init()
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    print(f"Pygame screen initialized at: {screen_width}x{screen_height}")
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Warped Video Player")
    pygame.mouse.set_visible(False)


    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {VIDEO_PATH}")
        pygame.quit()
        return

    # Start VLC playback with motion controlled volume
    video_thread = threading.Thread(target=play_video, args=(VIDEO_PATH,), daemon=True)
    video_thread.start()

    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    corners = None
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False

        ret, frame_bgr = cap.read()

        if not ret:
            print("End of video. Looping...")
            cap.release()
            cap = cv2.VideoCapture(VIDEO_PATH)
            continue

        loaded_corners = load_corners()
        if loaded_corners:
            corners = loaded_corners

        if not corners:
            clock.tick(30)
            continue

        src_pts = np.float32([[0, 0], [video_width, 0], [video_width, video_height], [0, video_height]])
        dst_pts = np.float32([corners['tl'], corners['tr'], corners['br'], corners['bl']])

        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

        warped_frame_bgr = cv2.warpPerspective(
            frame_bgr,
            matrix,
            (screen_width, screen_height),
            borderValue=(0, 0, 0)
        )

        frame_rgb = cv2.cvtColor(warped_frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb = frame_rgb.transpose([1, 0, 2])

        pygame_surface = pygame.surfarray.make_surface(frame_rgb)

        screen.blit(pygame_surface, (0, 0))

        pygame.display.flip()

        clock.tick(60)

    cap.release()
    pygame.quit()


if __name__ == "__main__":
   # TO DO: ADD USB AUTOMOUNT LOGIC!!
   main()

