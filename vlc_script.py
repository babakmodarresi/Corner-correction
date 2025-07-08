
from gpiozero import MotionSensor
import vlc
import time
import os
import glob # Added for finding files matching a pattern


pir = MotionSensor(10) # Assuming GPIO10, adjust if different


instance = vlc.Instance(" --input-repeat=999999999 -q --no-xlib")


last_motion = time.time()


# --- Configuration ---
DEFAULT_VIDEO_FILE = "/home/noorderlicht/video.mp4"
USB_MOUNT_POINTS_PREFIX = ["/media/"]
VIDEO_EXTENSIONS = ["*.mp4", "*.avi", "*.mkv", "*.mov"]
NO_MOTION_TIMEOUT = 2.0
MIN_VOLUME = 30
MAX_VOLUME = 100
VOLUME_STEP = 5


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
                           return video_files # Return list of found video files
   print("⚠️ No USB drive with video files found.")
   return []


def play_video(video_file_path):
   global last_motion # No need for 'image_process' if it's not used


   print(f"🎬 attempting to play: {video_file_path}")
   if not os.path.exists(video_file_path):
       print(f"❌ Error: no video found at {video_file_path}")
       return


   player = instance.media_player_new()
   media = instance.media_new(video_file_path)
   player.set_media(media)
   player.audio_set_volume(100)


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




if __name__ == "__main__":
   try:
       while True:
           usb_videos = find_usb_video_files()
           video_to_play = DEFAULT_VIDEO_FILE


           if usb_videos:
               video_to_play = usb_videos[0]
               print(f"💡 USB video: {video_to_play}")
           else:
               print(f"💡 default video: {video_to_play}")


           play_video(video_to_play)
           print("--- Loop restarting ---")
           time.sleep(1)


   except KeyboardInterrupt:
       print("\n🚫 exiting")
   finally:
       print("🧹 schoon")





