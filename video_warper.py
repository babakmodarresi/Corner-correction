import pygame
import cv2
import numpy as np
import json
import os
import hashlib
import tempfile
import time
import vlc
from gpiozero import MotionSensor


# --- Configuration ---
VIDEO_PATH = "2.mp4"
CORNERS_FILE = "corners.json"
CACHE_DIR = tempfile.gettempdir()
MOTION_PIN = 10
NO_MOTION_TIMEOUT = 2.0
MIN_VOLUME = 30
MAX_VOLUME = 100
VOLUME_STEP = 5


def load_corners():
   try:
       with open(CORNERS_FILE, 'r') as f:
           return json.load(f)
   except (FileNotFoundError, json.JSONDecodeError):
       print(f"Warning: Could not read {CORNERS_FILE}. Will try again.")
       return None


def preprocess_video(video_path, screen_width, screen_height, corners):
    """Warp the entire video to a temporary cached file."""
    cache_key = json.dumps(corners, sort_keys=True) + video_path
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()[:8]
    out_path = os.path.join(
        CACHE_DIR, f"warped_{os.path.basename(video_path)}_{cache_hash}.mp4"
    )
    if os.path.exists(out_path):
        return out_path

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (screen_width, screen_height))

    src_pts = np.float32([[0, 0], [src_w, 0], [src_w, src_h], [0, src_h]])
    dst_pts = np.float32([
        corners["tl"],
        corners["tr"],
        corners["br"],
        corners["bl"],
    ])
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        warped = cv2.warpPerspective(
            frame, matrix, (screen_width, screen_height), borderValue=(0, 0, 0)
        )
        writer.write(warped)

    cap.release()
    writer.release()
    return out_path


def main():
    pygame.init()
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    print(f"Pygame screen initialized at: {screen_width}x{screen_height}")
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Warped Video Player")
    pygame.mouse.set_visible(False)

    corners = load_corners()
    if not corners:
        print("No corner configuration found.")
        pygame.quit()
        return

    try:
        warped_path = preprocess_video(
            VIDEO_PATH, screen_width, screen_height, corners
        )
    except IOError as e:
        print(e)
        pygame.quit()
        return

    instance = vlc.Instance(" --input-repeat=999999999 -q --no-xlib")
    player = instance.media_player_new()
    media = instance.media_new(warped_path)
    player.set_media(media)
    player.audio_set_volume(MAX_VOLUME)

    window_info = pygame.display.get_wm_info().get("window")
    if window_info:
        # Direct VLC output to the same window created by pygame
        try:
            player.set_xwindow(window_info)
        except AttributeError:
            player.set_hwnd(window_info)

    player.play()
    time.sleep(1)  # allow VLC time to start

    pir = MotionSensor(MOTION_PIN)
    last_motion = time.time()

    running = True
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    while running:
        if not player.is_playing():
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        if pir.is_active:
            last_motion = time.time()

        current_time = time.time()
        current_volume = player.audio_get_volume()

        if current_time < last_motion + NO_MOTION_TIMEOUT:
            if current_volume < MAX_VOLUME:
                player.audio_set_volume(min(current_volume + VOLUME_STEP, MAX_VOLUME))
        else:
            if current_volume > MIN_VOLUME:
                player.audio_set_volume(max(current_volume - VOLUME_STEP, MIN_VOLUME))

        screen.fill((0, 0, 0))
        status = f"Volume: {player.audio_get_volume()}"
        text_surface = font.render(status, True, (255, 255, 255))
        screen.blit(text_surface, (20, 20))
        pygame.display.flip()

        clock.tick(30)

    player.stop()
    player.release()
    pygame.quit()


if __name__ == "__main__":
   # TO DO: ADD USB AUTOMOUNT LOGIC!!
   main()

