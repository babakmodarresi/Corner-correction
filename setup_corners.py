import pygame
import json
import os


# --- Configuration ---
CORNERS_FILE = "corners.json"


# --- Colors ---
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)


COLOR_LINE = (255, 255, 255)
COLOR_GREEN = (50, 220, 50)
COLOR_BLUE = (50, 50, 220)


def load_or_create_corners(width, height):
   if os.path.exists(CORNERS_FILE):
       try:
           with open(CORNERS_FILE, 'r') as f:
               data = json.load(f)
               return [data['tl'], data['tr'], data['br'], data['bl']]
       except (json.JSONDecodeError, KeyError):
           print(f"Warning: '{CORNERS_FILE}' is corrupt or invalid. Creating new defaults.")
  
   inset = 50
   return [
       [inset, inset],
       [width - inset, inset],
       [width - inset, height - inset],
       [inset, height - inset]
   ]


def save_corners(corners_list):
   corner_data = {
       "tl": corners_list[0],
       "tr": corners_list[1],
       "br": corners_list[2],
       "bl": corners_list[3]
   }
   with open(CORNERS_FILE, 'w') as f:
       json.dump(corner_data, f, indent=4)
   print(f"Corners saved to {CORNERS_FILE}")


def main():
   pygame.init()


   info = pygame.display.Info()
   screen_width, screen_height = info.current_w, info.current_h
   screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
   pygame.display.set_caption("Interactive Corner Setup")


   corners = load_or_create_corners(screen_width, screen_height)
  
   selected_corner = 0
   running = True
   clock = pygame.time.Clock()


   font = pygame.font.Font(None, 36)
   small_font = pygame.font.Font(None, 28)


   while running:
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               running = False
           if event.type == pygame.KEYDOWN:
               if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                   running = False
              
               if event.key == pygame.K_SPACE:
                   selected_corner = (selected_corner + 1) % 4
              
               if event.key == pygame.K_s:
                   save_corners(corners)


               mods = pygame.key.get_mods()
               move_amount = 10 if mods & pygame.KMOD_SHIFT else 1
              
               if event.key == pygame.K_UP:    corners[selected_corner][1] -= move_amount
               if event.key == pygame.K_DOWN:  corners[selected_corner][1] += move_amount
               if event.key == pygame.K_LEFT:  corners[selected_corner][0] -= move_amount
               if event.key == pygame.K_RIGHT: corners[selected_corner][0] += move_amount


       screen.fill(COLOR_BLACK)
       pygame.draw.lines(screen, COLOR_LINE, True, corners, 3)


       # draw circle at each corner
       for i, pos in enumerate(corners):
           color = COLOR_BLUE if i == selected_corner else COLOR_GREEN
           pygame.draw.circle(screen, color, pos, 10)


       corner_names = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]


       status_text = f"Selected: {corner_names[selected_corner]}"
       status_surf = font.render(status_text, True, COLOR_WHITE)
       screen.blit(status_surf, (20, 20))
      
       coord_text = f"Coords: ({corners[selected_corner][0]}, {corners[selected_corner][1]})"
       coord_surf = font.render(coord_text, True, COLOR_WHITE)
       screen.blit(coord_surf, (20, 60))


       controls_text = "[Arrows] Move | [Shift+Arrows] Move 10px | [Space] Next Corner | [S] Save | [Q] Quit"
       controls_surf = small_font.render(controls_text, True, COLOR_WHITE)
       screen.blit(controls_surf, (20, screen_height - 40))


       pygame.display.flip()
       clock.tick(60)


   save_corners(corners)
   pygame.quit()


if __name__ == "__main__":
   main()

