import pygame
import cv2
import numpy as np
import json
import os
import shutil
import subprocess


# --- Configuration ---
VIDEO_PATH = "2.mp4"
CORNERS_FILE = "corners.json"
# USB mount prefixes used for copying the corners file after it is loaded
USB_MOUNT_POINTS_PREFIX = ["/media/"]


def load_corners():
   try:
       with open(CORNERS_FILE, 'r') as f:
           return json.load(f)
   except (FileNotFoundError, json.JSONDecodeError):
       print(f"Warning: Could not read {CORNERS_FILE}. Will try again.")
       return None


def find_usb_root():
   """Return the path to the first detected USB mount or None."""
   for prefix in USB_MOUNT_POINTS_PREFIX:
       if os.path.exists(prefix):
           for name in os.listdir(prefix):
               usb_path = os.path.join(prefix, name)
               if os.path.isdir(usb_path):
                   return usb_path
   return None


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


   video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
   video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

   corners = load_corners()
   if not corners:
      subprocess.run(["python3", "setup_corners.py"])
      corners = load_corners()
      if not corners:
         print("Error: Could not load corners even after running setup.")
         pygame.quit()
         return

   usb_root = find_usb_root()
   if usb_root:
      try:
         shutil.copyfile(CORNERS_FILE, os.path.join(usb_root, CORNERS_FILE))
         print(f"Copied {CORNERS_FILE} to {usb_root}")
      except Exception as e:
         print(f"Warning: failed to copy corners to USB: {e}")

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
    # Corners are copied to a USB drive if one is detected
    main()

