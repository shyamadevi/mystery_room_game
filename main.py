import pygame
import os
import math  # rotation ke liye
import cv2
import os

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# --- CONFIG -----------------------------------------------------------------
ROOM_WIDTH, ROOM_HEIGHT = 1152, 768
INVENTORY_WIDTH = 200
#tv 
TV_RECT = pygame.Rect(665, 255, 220, 155)
# TV frame position (outer)
TV_FRAME_RECT = pygame.Rect(635, 255, 240, 180)


# Actual screen inside TV (inner)
TV_SCREEN_RECT = pygame.Rect(680, 285, 150, 115)



TV_TILT_ANGLE = -2
  # negative = tilt left, positive = tilt right

SCREEN_WIDTH, SCREEN_HEIGHT = ROOM_WIDTH + INVENTORY_WIDTH, ROOM_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mystery Room")
clock = pygame.time.Clock()

# --- LOAD BACKGROUND --------------------------------------------------------
BG_PATH = os.path.join("assets", "images", "room.png")
room_bg_raw = pygame.image.load(BG_PATH).convert()
room_bg = pygame.transform.scale(room_bg_raw, (ROOM_WIDTH, ROOM_HEIGHT))

# --- LOAD SPRITES -----------------------------------------------------------
DRAWER_OPEN_IMG = pygame.image.load(
    os.path.join("assets", "images", "drawer.png")
).convert_alpha()

HAMMER_IMG = pygame.image.load(
    os.path.join("assets", "images", "hammer.png")
).convert_alpha()

#---LOAD TV FRAMES --------------------------------------------------------
tv_frame = pygame.image.load(
    os.path.join("assets", "images", "tv_frame.png")
).convert_alpha()

tv_frame = pygame.transform.scale(tv_frame, TV_FRAME_RECT.size)


#LOAD VIDEO
video = cv2.VideoCapture(
    os.path.join("assets", "videos", "tv.mp4")
)

# --- LOAD SOUNDS -------------------------------------------------------------
DRAWER_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "drowerOpenSound.mp3"))
DOOR_KNOCK_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "doorKnowking2.mp3"))
HORROR_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "horror.mp3"))

DRAWER_SOUND.set_volume(0.6)
DOOR_KNOCK_SOUND.set_volume(0.7)
HORROR_SOUND.set_volume(0.3)

# --- INTERACTIVE OBJECTS (RECTS) -------------------------------------------
DRAWER_RECT = pygame.Rect(550, 370, 140, 100)
HAMMER_RECT = pygame.Rect(590, 400, 40, 20)

LEFT_DOOR_RECT = pygame.Rect(110, 150, 160, 340)
RIGHT_DOOR_RECT = pygame.Rect(930, 230, 140, 280)

INVENTORY_AREA_X = ROOM_WIDTH
INVENTORY_SLOT_RECT = pygame.Rect(INVENTORY_AREA_X + 60, 80, 80, 80)

KEYPAD_RECT = pygame.Rect(160, 260, 60, 80)

# Restart icon area (top-left chhota square)
RESTART_RECT = pygame.Rect(10, 10, 40, 40)

# --- SCALE SPRITES ----------------------------------------------------------
DRAWER_OPEN_IMG = pygame.transform.scale(
    DRAWER_OPEN_IMG, (DRAWER_RECT.width, DRAWER_RECT.height)
)
HAMMER_IMG = pygame.transform.scale(
    HAMMER_IMG, (HAMMER_RECT.width, HAMMER_RECT.height)
)

# --- GAME STATE -------------------------------------------------------------
def reset_game():
    global drawer_open, hammer_taken, left_door_locked, message, message_timer
    global selected_item, keypad_active, current_code, door_just_touched
    global restart_rotating, restart_angle, restart_frames

    drawer_open = False
    hammer_taken = False
    left_door_locked = True
    message = ""
    message_timer = 0
    selected_item = None
    keypad_active = False
    current_code = ""
    door_just_touched = False
    restart_rotating = False
    restart_angle = 0
    restart_frames = 0

drawer_open = False
hammer_taken = False
left_door_locked = True

message = ""
message_timer = 0

FONT = pygame.font.SysFont(None, 32)
FONT_SMALL = pygame.font.SysFont(None, 24)

selected_item = None
keypad_active = False
current_code = ""
CODE_LENGTH = 4
CORRECT_CODE = "1234"

door_just_touched = False

# Restart animation state
restart_rotating = False
restart_angle = 0        # degrees
restart_frames = 0       # kitne frame se rotate ho raha hai

# --- HELPERS ----------------------------------------------------------------
def stop_foreground_sounds():
    """Drawer / knock band karo, horror bg chalta rahe."""
    global door_just_touched
    DOOR_KNOCK_SOUND.stop()
    door_just_touched = False

def set_message(text, frames=120):
    global message, message_timer
    message = text
    message_timer = frames

# Background horror music continuous
HORROR_SOUND.play(loops=-1)

# --- INPUT LOGIC ------------------------------------------------------------
def handle_keydown(event):
    global current_code, keypad_active, left_door_locked

    if not keypad_active:
        return

    if event.key in (pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3,
                     pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7,
                     pygame.K_8, pygame.K_9):
        if len(current_code) < CODE_LENGTH:
            digit = event.unicode
            current_code += digit

    elif event.key == pygame.K_BACKSPACE:
        current_code = current_code[:-1]

    elif event.key == pygame.K_RETURN:
        if len(current_code) == CODE_LENGTH:
            if current_code == CORRECT_CODE:
                left_door_locked = False
                set_message("Door unlocked!")
            else:
                set_message("Wrong code.")
        else:
            set_message("Enter 4 digits.")
        current_code = ""
        keypad_active = False

def handle_click(pos):
    global drawer_open, hammer_taken, selected_item, keypad_active, door_just_touched
    global restart_rotating, restart_angle, restart_frames

    x, y = pos

    # --- Restart icon click -------------------------------------------------
    if RESTART_RECT.collidepoint(pos):
        stop_foreground_sounds()
        reset_game()
        set_message("Game Restarted!", 120)

        # rotation animation start
        restart_rotating = True
        restart_angle = 0
        restart_frames = 0
        return
    # ------------------------------------------------------------------------

    # Room area
    if x < ROOM_WIDTH:
        # Hammer click
        if drawer_open and not hammer_taken and HAMMER_RECT.collidepoint(pos):
            hammer_taken = True
            stop_foreground_sounds()
            set_message("Picked up hammer.", 120)
            return

        # Drawer click
        if DRAWER_RECT.collidepoint(pos):
            stop_foreground_sounds()
            drawer_open = not drawer_open
            DRAWER_SOUND.play()
            set_message("Drawer opened." if drawer_open else "Drawer closed.", 60)
            return

        # Left door click
        if LEFT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:
                DOOR_KNOCK_SOUND.play()
                door_just_touched = True
            if left_door_locked:
                set_message("The door is locked.", 120)
            else:
                set_message("You opened the door!", 120)
            return

        # Right door click
        if RIGHT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:
                DOOR_KNOCK_SOUND.play()
                door_just_touched = True
            set_message("The door is locked.", 120)
            return

        # Keypad click
        if KEYPAD_RECT.collidepoint(pos):
            stop_foreground_sounds()
            keypad_active = True
            return

    # Inventory area
    else:
        if hammer_taken and INVENTORY_SLOT_RECT.collidepoint(pos):
            stop_foreground_sounds()
            if selected_item == "hammer":
                selected_item = None
                set_message("Deselected hammer.", 60)
            else:
                selected_item = "hammer"
                set_message("Selected hammer.", 60)
        return

# --- DRAW -------------------------------------------------------------------
def draw():
    global message_timer, door_just_touched
    global restart_rotating, restart_angle, restart_frames

    screen.fill((0, 0, 0))
    screen.blit(room_bg, (0, 0))
    draw_tv()
    pygame.display.flip()

    if door_just_touched:
        door_just_touched = False

    # --- Restart symbol (rotating) -----------------------------------------
    cx = RESTART_RECT.x + RESTART_RECT.width // 2
    cy = RESTART_RECT.y + RESTART_RECT.height // 2
    center = (cx, cy)

    radius_outer = 16
    thickness = 4

    # rotation update
    if restart_rotating:
        restart_angle += 20      # speed (degree per frame)
        restart_frames += 1
        # kitni der ghoomega (yahan ~360*2 / 20 = 36 frames, lagbhag 2 turn)
        if restart_frames > 36:
            restart_rotating = False
            restart_angle = 0

    base_start = 60
    base_end = 330
    start_angle = math.radians(base_start + restart_angle)
    end_angle = math.radians(base_end + restart_angle)

    arc_rect = pygame.Rect(
        cx - radius_outer,
        cy - radius_outer,
        radius_outer * 2,
        radius_outer * 2
    )

    pygame.draw.arc(
        screen,
        (255, 255, 255),
        arc_rect,
        start_angle,
        end_angle,
        thickness
    )

    # Arrow head, same rotation ke sath
    head_angle_deg = base_start + restart_angle
    head_angle = math.radians(head_angle_deg)
    tip_x = cx + radius_outer * math.cos(head_angle)
    tip_y = cy + radius_outer * math.sin(head_angle)

    arrow_len = 10
    # tangent-like direction
    dir_angle = head_angle - math.radians(30)
    ax = arrow_len * math.cos(dir_angle)
    ay = arrow_len * math.sin(dir_angle)

    arrow_points = [
        (tip_x, tip_y),
        (tip_x - ax - ay/3, tip_y - ay + ax/3),
        (tip_x - ax + ay/3, tip_y - ay - ax/3),
    ]
    pygame.draw.polygon(screen, (255, 255, 255), arrow_points)
    # ------------------------------------------------------------------------

    # Debug outlines (chahe to hata sakti ho)
    pygame.draw.rect(screen, (255, 0, 0), DRAWER_RECT, 2)
    pygame.draw.rect(screen, (0, 255, 0), LEFT_DOOR_RECT, 2)
    pygame.draw.rect(screen, (0, 0, 255), RIGHT_DOOR_RECT, 2)
    pygame.draw.rect(screen, (255, 255, 0), KEYPAD_RECT, 2)

    # Drawer + hammer
    if drawer_open:
        screen.blit(DRAWER_OPEN_IMG, DRAWER_RECT.topleft)
        if not hammer_taken:
            screen.blit(HAMMER_IMG, HAMMER_RECT.topleft)

    # Inventory panel
    pygame.draw.rect(
        screen, (20, 20, 20),
        (INVENTORY_AREA_X, 0, INVENTORY_WIDTH, SCREEN_HEIGHT), 0
    )
    inv_text = FONT.render("Inventory", True, (255, 255, 255))
    screen.blit(inv_text, (INVENTORY_AREA_X + 40, 30))

    # Inventory slot
    if selected_item == "hammer":
        border_color = (255, 255, 0)
        border_width = 4
    else:
        border_color = (100, 100, 100)
        border_width = 2

    pygame.draw.rect(screen, border_color, INVENTORY_SLOT_RECT, border_width)

    if hammer_taken:
        inv_hammer = pygame.transform.scale(
            HAMMER_IMG,
            (INVENTORY_SLOT_RECT.width - 20, INVENTORY_SLOT_RECT.height - 20)
        )
        screen.blit(inv_hammer, INVENTORY_SLOT_RECT.inflate(-20, -20).topleft)

    # Keypad UI
    if keypad_active:
        panel_width, panel_height = 260, 80
        panel_rect = pygame.Rect(
            (ROOM_WIDTH - panel_width) // 2,
            ROOM_HEIGHT - panel_height - 80,
            panel_width,
            panel_height
        )
        pygame.draw.rect(screen, (10, 10, 10), panel_rect, 0)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)

        prompt = FONT_SMALL.render("Enter 4-digit code:", True, (255, 255, 255))
        screen.blit(prompt, (panel_rect.x + 10, panel_rect.y + 10))

        box_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 35, panel_width - 20, 30)
        pygame.draw.rect(screen, (0, 0, 0), box_rect, 0)
        pygame.draw.rect(screen, (200, 200, 200), box_rect, 1)

        code_display = current_code + "_" * (CODE_LENGTH - len(current_code))
        code_surf = FONT.render(code_display, True, (0, 255, 0))
        screen.blit(code_surf, (box_rect.x + 10, box_rect.y + 3))

    # Selected item text
    if selected_item:
        sel_text = FONT_SMALL.render(f"Selected: {selected_item}", True, (255, 255, 0))
        screen.blit(sel_text, (INVENTORY_AREA_X + 20, 170))

    # Message bottom
    if message and message_timer > 0:
        msg_surf = FONT.render(message, True, (255, 255, 255))
        screen.blit(msg_surf, (40, SCREEN_HEIGHT - 40))
        message_timer -= 1


#tv frame
def draw_tv():
    ret, frame = video.read()
    if not ret:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = video.read()

    # Convert OpenCV → pygame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, TV_SCREEN_RECT.size)
    frame = frame.swapaxes(0, 1)

    video_surface = pygame.surfarray.make_surface(frame)

    # Rotate slightly
    video_surface = pygame.transform.rotozoom(video_surface, TV_TILT_ANGLE, 1)
    frame_surface = pygame.transform.rotozoom(tv_frame, TV_TILT_ANGLE, 1)

    # Correct centering
    video_rect = video_surface.get_rect(center=TV_SCREEN_RECT.center)
    frame_rect = frame_surface.get_rect(center=TV_FRAME_RECT.center)

    # Draw order
    screen.blit(video_surface, video_rect)
    screen.blit(frame_surface, frame_rect)



# --- MAIN LOOP --------------------------------------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            DOOR_KNOCK_SOUND.stop()
            HORROR_SOUND.stop()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            handle_keydown(event)

    draw()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
