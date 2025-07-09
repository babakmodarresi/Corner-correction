import pygame
import cv2
import numpy as np
import json
import os
import glob


# --- Configuration ---
VIDEO_PATH = "2.mp4"
CORNERS_FILE = "corners.json"
USB_MOUNT_POINTS_PREFIX = ["/media/"]
VIDEO_EXTENSIONS = ["*.mp4", "*.avi", "*.mkv", "*.mov"]


def load_corners():
    try:
        with open(CORNERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Could not read {CORNERS_FILE}. Will try again.")
        return None


def find_usb_video_files():
    """Return the first video file found on mounted USB drives."""
    for prefix in USB_MOUNT_POINTS_PREFIX:
        if os.path.exists(prefix):
            for root_dir in os.listdir(prefix):
                usb_path = os.path.join(prefix, root_dir)
                if os.path.isdir(usb_path):
                    for ext in VIDEO_EXTENSIONS:
                        files = glob.glob(os.path.join(usb_path, "**", ext), recursive=True)
                        if files:
                            return files[0]
    return None


def preprocess_video(video_path: str):
    """Open the given video path and return a capture object."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return None
    return cap


def main():
   pygame.init()
   info = pygame.display.Info()
   screen_width, screen_height = info.current_w, info.current_h
   print(f"Pygame screen initialized at: {screen_width}x{screen_height}")
   screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
   pygame.display.set_caption("Warped Video Player")
   pygame.mouse.set_visible(False)


   usb_video = find_usb_video_files()
   video_source = usb_video if usb_video else VIDEO_PATH

   cap = preprocess_video(video_source)
   if cap is None:
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
           cap = preprocess_video(video_source)
           if cap is None:
               break
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

