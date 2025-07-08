import pygame
import cv2
import numpy as np
import json
import os
import glob
import setup_corners


# --- Configuration ---
DEFAULT_VIDEO_FILE = "2.mp4"
USB_MOUNT_POINTS_PREFIX = ["/media/"]
VIDEO_EXTENSIONS = ["*.mp4", "*.avi", "*.mkv", "*.mov"]
CORNERS_FILE = "corners.json"


def find_usb_video_files():
    """Checks common USB mount points for video files."""
    for prefix in USB_MOUNT_POINTS_PREFIX:
        if os.path.exists(prefix):
            for root_dir in os.listdir(prefix):
                usb_path = os.path.join(prefix, root_dir)
                if os.path.isdir(usb_path):
                    print(f"🔍 Checking USB drive: {usb_path}")
                    for ext in VIDEO_EXTENSIONS:
                        video_files = glob.glob(os.path.join(usb_path, "**", ext), recursive=True)
                        if video_files:
                            print(f"✅ Found video on USB: {video_files}")
                            return video_files
    print("⚠️ No USB drive with video files found.")
    return []


def load_corners():
   try:
       with open(CORNERS_FILE, 'r') as f:
           return json.load(f)
   except (FileNotFoundError, json.JSONDecodeError):
       print(f"Warning: Could not read {CORNERS_FILE}. Will try again.")
       return None


def main():
    pygame.init()
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    print(f"Pygame screen initialized at: {screen_width}x{screen_height}")
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Warped Video Player")
    pygame.mouse.set_visible(False)

    usb_videos = find_usb_video_files()
    if not usb_videos:
        print("No USB video found. Launching corner setup...")
        setup_corners.main()
        usb_videos = find_usb_video_files()

    if usb_videos:
        video_path = usb_videos[0]
        print(f"Using USB video: {video_path}")
    else:
        video_path = DEFAULT_VIDEO_FILE
        print(f"Using default video: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        pygame.quit()
        return

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
            usb_videos = find_usb_video_files()
            if usb_videos:
                video_path = usb_videos[0]
                print(f"Using USB video: {video_path}")
            else:
                video_path = DEFAULT_VIDEO_FILE
                print(f"Using default video: {video_path}")
            cap = cv2.VideoCapture(video_path)
            video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
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
   main()

