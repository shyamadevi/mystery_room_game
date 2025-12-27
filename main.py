import pygame
import os
import math 
import cv2
import subprocess
import time  # For delay

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# --- CONFIG -----------------------------------------------------------------
ROOM_WIDTH, ROOM_HEIGHT = 1152, 768
INVENTORY_WIDTH = 200
INVENTORY_AREA_X = ROOM_WIDTH

right_door_unlocked = False
left_door_opened_time = 0  # NEW: Track when left door opened
game_won = False  # NEW: Game over state
win_timer = 0  # NEW: 2 second delay

pin_mode = None  
tv_state = "OFF"

SCREEN_WIDTH, SCREEN_HEIGHT = ROOM_WIDTH + INVENTORY_WIDTH, ROOM_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mystery Room")
clock = pygame.time.Clock()

# --- LOAD BACKGROUND --------------------------------------------------------
BG_PATH = os.path.join("assets", "images", "room.png")
room_bg_raw = pygame.image.load(BG_PATH).convert()
room_bg = pygame.transform.scale(room_bg_raw, (ROOM_WIDTH, ROOM_HEIGHT))

# --- LOAD ALL IMAGES --------------------------------------------------------
PIN_IMG_PATH = os.path.join("assets", "images", "pin.png")
SWITCH_IMG_PATH = os.path.join("assets", "images", "switch.png")
TV_PIN_IMG_PATH = os.path.join("assets", "images", "tv_pin.png")
LEFT_DOOR_IMG_PATH = os.path.join("assets", "images", "left_door.png")
RIGHT_DOOR_IMG_PATH = os.path.join("assets", "images", "right_door.png")  # NEW
OVER_IMG_PATH = os.path.join("assets", "images", "over.png")  # NEW

pin_img_raw = pygame.image.load(PIN_IMG_PATH).convert()
pin_img = pygame.transform.scale(pin_img_raw, (ROOM_WIDTH, ROOM_HEIGHT))
switch_img_raw = pygame.image.load(SWITCH_IMG_PATH).convert_alpha()
switch_img = pygame.transform.scale(switch_img_raw, (25, 45))
tv_pin_img_raw = pygame.image.load(TV_PIN_IMG_PATH).convert_alpha()
tv_pin_img = pygame.transform.scale(tv_pin_img_raw, (85, 70))
left_door_img_raw = pygame.image.load(LEFT_DOOR_IMG_PATH).convert_alpha()
left_door_img = pygame.transform.scale(left_door_img_raw, (280, 360))

# NEW IMAGES
right_door_img = pygame.image.load(RIGHT_DOOR_IMG_PATH).convert_alpha()
right_door_img = pygame.transform.scale(right_door_img, (200, 470))
over_img_raw = pygame.image.load(OVER_IMG_PATH).convert()
over_img = pygame.transform.scale(over_img_raw, (SCREEN_WIDTH, SCREEN_HEIGHT))

DRAWER_OPEN_IMG = pygame.image.load(os.path.join("assets", "images", "drawer.png")).convert_alpha()
HAMMER_IMG = pygame.image.load(os.path.join("assets", "images", "hammer.png")).convert_alpha()

# --- LOAD SOUNDS -------------------------------------------------------------
DRAWER_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "drowerOpenSound.mp3"))
DOOR_KNOCK_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "doorKnowking2.mp3"))
HORROR_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "horror.mp3"))
DRAWER_SOUND.set_volume(0.6)
DOOR_KNOCK_SOUND.set_volume(0.7)
HORROR_SOUND.set_volume(0.3)

# --- ALL INTERACTIVE OBJECTS -------------------------------------------------
KEYPAD_RECT = pygame.Rect(160, 260, 60, 80)
DRAWER_RECT = pygame.Rect(550, 370, 140, 100)
HAMMER_RECT = pygame.Rect(590, 400, 40, 20)
LEFT_DOOR_RECT = pygame.Rect(13, 130, 160, 340)
GLASS_CASE_RECT = pygame.Rect(295, 290, 40, 70)
RIGHT_DOOR_RECT = pygame.Rect(910, 100, 200, 470)
MIDDLE_RECT = pygame.Rect(580, 550, 80, 50)
RIGHT_DOOR_TV_RECT = pygame.Rect(745, 332, 100, 80)

INVENTORY_SLOT_RECT = pygame.Rect(ROOM_WIDTH + 60, 80, 80, 80)
RESTART_RECT = pygame.Rect(10, 10, 40, 40)
RETURN_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH - 120, 200, 60, 40)

# --- SCALE SPRITES ----------------------------------------------------------
DRAWER_OPEN_IMG = pygame.transform.scale(DRAWER_OPEN_IMG, (DRAWER_RECT.width, DRAWER_RECT.height))
HAMMER_IMG = pygame.transform.scale(HAMMER_IMG, (HAMMER_RECT.width, HAMMER_RECT.height))

# --- GAME STATE -------------------------------------------------------------
def reset_game():
    global drawer_open, hammer_taken, left_door_locked, message, message_timer
    global selected_item, keypad_active, otp_digits, door_just_touched
    global restart_rotating, restart_angle, restart_frames, restart_hover, tooltip_timer
    global glass_case_intact, room_power_on, tv_pin_unlocked, left_door_unlocked_visual
    global tv_state, pin_mode, right_door_unlocked, left_door_opened_time, game_won, win_timer
    
    drawer_open = False
    hammer_taken = False
    left_door_locked = True
    message = ""
    message_timer = 0
    selected_item = None
    keypad_active = False
    otp_digits = ["", "", "", ""]
    door_just_touched = False
    restart_rotating = False
    restart_angle = 0
    restart_frames = 0
    restart_hover = False
    tooltip_timer = 0
    glass_case_intact = True
    room_power_on = True
    tv_pin_unlocked = False
    left_door_unlocked_visual = False
    tv_state = "OFF"
    pin_mode = None
    right_door_unlocked = False
    left_door_opened_time = 0
    game_won = False
    win_timer = 0

# Initialize
reset_game()
FONT = pygame.font.SysFont(None, 32)
FONT_SMALL = pygame.font.SysFont(None, 24)
FONT_TINY = pygame.font.SysFont(None, 20)
FONT_OTP = pygame.font.SysFont(None, 48)
CORRECT_CODE = "6554"
OTP_CURSOR_BLINK = 0

HORROR_SOUND.play(loops=-1)

# --- HELPERS ----------------------------------------------------------------
def stop_foreground_sounds():
    global door_just_touched
    DOOR_KNOCK_SOUND.stop()
    door_just_touched = False

def set_message(text, frames=120):
    global message, message_timer
    message = text
    message_timer = frames

# --- FIXED BACK BUTTON HANDLING ---------------------------------------------
def get_back_rect():
    if keypad_active:
        panel_width, panel_height = 400, 160
        panel_rect = pygame.Rect((ROOM_WIDTH - panel_width) // 2, ROOM_HEIGHT - panel_height - 40, panel_width, panel_height)
        return pygame.Rect(panel_rect.x + panel_width - 40, panel_rect.y + 10, 30, 30)
    return None

# --- OTP INPUT HANDLING (UNCHANGED) -----------------------------------------
def handle_otp_keydown(event):
    global otp_digits, keypad_active, OTP_CURSOR_BLINK
    global left_door_locked, left_door_unlocked_visual
    global tv_pin_unlocked, pin_mode, right_door_unlocked, left_door_opened_time

    if not keypad_active:
        return

    current_pos = next((i for i, d in enumerate(otp_digits) if d == ""), 3)

    if event.key in (pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3,
                     pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7,
                     pygame.K_8, pygame.K_9):
        if current_pos < 4:
            otp_digits[current_pos] = event.unicode
            OTP_CURSOR_BLINK = 0

    elif event.key == pygame.K_BACKSPACE:
        if current_pos > 0:
            otp_digits[current_pos - 1] = ""

    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        code = "".join(otp_digits)

        if len(code) == 4:
            if pin_mode == "DOOR":
                if code == CORRECT_CODE:
                    left_door_locked = False
                    left_door_unlocked_visual = True
                    left_door_opened_time = pygame.time.get_ticks()  # NEW: Start timer
                    set_message("Door unlocked! 🚪", 180)
                else:
                    set_message("Wrong door code ❌", 120)

            elif pin_mode == "TV":
                if code == CORRECT_CODE:
                    tv_state = "UNLOCKED"
                    set_message("TV unlocked 📺", 180)
                    result = subprocess.run(["python", "sudoku.py"])
                    if result.returncode == 0:
                        right_door_unlocked = True
                        set_message("Right door unlocked! 🚪", 180)
                else:
                    set_message("Wrong TV PIN ❌", 120)

        otp_digits = ["", "", "", ""]
        keypad_active = False
        pin_mode = None

# --- COMPLETE CLICK HANDLING (FIXED) ----------------------------------------
def handle_click(pos):
    global tv_state, pin_mode, keypad_active, otp_digits
    global drawer_open, hammer_taken, selected_item, door_just_touched
    global restart_rotating, restart_angle, restart_frames
    global glass_case_intact, room_power_on, tv_pin_unlocked, left_door_unlocked_visual
    global right_door_unlocked
    
    x, y = pos
    
    # FIXED BACK BUTTON
    back_rect = get_back_rect()
    if keypad_active and back_rect and back_rect.collidepoint(pos):
        if pin_mode == "TV":
            tv_state = "OFF"
        keypad_active = False
        otp_digits = ["", "", "", ""]
        pin_mode = None
        set_message("PIN closed", 60)
        return

    # RETURN BUTTON (darkness screen)
    if RETURN_BUTTON_RECT.collidepoint(pos) and not room_power_on:
        room_power_on = True
        set_message("Lights restored!", 120)
        return
    
    # Restart
    if RESTART_RECT.collidepoint(pos):
        stop_foreground_sounds()
        reset_game()
        set_message("Game Restarted! 🔄", 180)
        restart_rotating = True
        restart_angle = 0
        restart_frames = 0
        return
    
    # Skip room interactions when lights off or game won
    if not room_power_on or game_won:
        return
        
    if x < ROOM_WIDTH:
        # KEYPAD
        if KEYPAD_RECT.collidepoint(pos):
            stop_foreground_sounds()
            pin_mode = "DOOR"
            keypad_active = True
            otp_digits = ["", "", "", ""]
            set_message("Enter door code", 120)
            return

        # MIDDLE RECT
        if MIDDLE_RECT.collidepoint(pos):
            tv_state = "IMAGE"
            set_message("TV powered on 📺", 120)
            return

        # RIGHT DOOR TV RECT
        if RIGHT_DOOR_TV_RECT.collidepoint(pos) and tv_state == "IMAGE":
            tv_state = "PIN"
            pin_mode = "TV"
            keypad_active = True
            otp_digits = ["", "", "", ""]
            set_message("Enter TV PIN", 120)
            return

        # GLASS CASE / SWITCH
        if GLASS_CASE_RECT.collidepoint(pos):
            if glass_case_intact and selected_item == "hammer":
                glass_case_intact = False
                stop_foreground_sounds()
                set_message("Glass broken! 💥", 120)
            elif not glass_case_intact:
                room_power_on = False
                set_message("Lights OFF! 🔌", 180)
            else:
                set_message("Glass case. Use hammer?", 120)
            return
        
        # Hammer
        if drawer_open and not hammer_taken and HAMMER_RECT.collidepoint(pos):
            hammer_taken = True
            stop_foreground_sounds()
            set_message("Picked up hammer. 🔨", 120)
            return
        
        # Drawer
        if DRAWER_RECT.collidepoint(pos):
            stop_foreground_sounds()
            drawer_open = not drawer_open
            DRAWER_SOUND.play()
            set_message("Drawer opened." if drawer_open else "Drawer closed.", 60)
            return
        
        # Left door
        if LEFT_DOOR_RECT.collidepoint(pos) and not KEYPAD_RECT.collidepoint(pos) and not GLASS_CASE_RECT.collidepoint(pos):
            if not door_just_touched:
                DOOR_KNOCK_SOUND.play()
                door_just_touched = True
            if left_door_locked:
                set_message("The door is locked. 🔑", 120)
            else:
                set_message("You opened the door! 🚪", 180)
            return
        
        # Right door
        if RIGHT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:
                DOOR_KNOCK_SOUND.play()
                door_just_touched = True
            if right_door_unlocked:
                screen.blit(right_door_img, RIGHT_DOOR_RECT.topleft)
                set_message("The door opens! 🚪", 180)
            else:
                set_message("The door is locked. 🔒", 120)
            return
    
    # Inventory
    else:
        if hammer_taken and INVENTORY_SLOT_RECT.collidepoint(pos):
            stop_foreground_sounds()
            if selected_item == "hammer":
                selected_item = None
                set_message("Deselected hammer.", 60)
            else:
                selected_item = "hammer"
                set_message("Selected hammer. 🔨", 60)

# --- MAIN LOOP --------------------------------------------------------------
running = True
mouse_pos = (0, 0)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            DOOR_KNOCK_SOUND.stop()
            HORROR_SOUND.stop()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            handle_otp_keydown(event)
    
    mouse_pos = pygame.mouse.get_pos()
    restart_hover = RESTART_RECT.collidepoint(mouse_pos)
    if restart_hover:
        tooltip_timer += 1
    else:
        tooltip_timer = 0
    
    OTP_CURSOR_BLINK += 1
    
    # --- WIN CONDITION: 2 seconds after left door opened ---
    if left_door_unlocked_visual and left_door_opened_time > 0:
        time_elapsed = (pygame.time.get_ticks() - left_door_opened_time) / 1000
        if time_elapsed >= 2.0 and not game_won:
            game_won = True
            win_timer = pygame.time.get_ticks()
    
    # --- DRAWING - GAME WON FIRST ---------------------------------------------
    if game_won:
        screen.blit(over_img, (0, 0))
        # Restart button still works
        cx, cy = RESTART_RECT.center
        radius_outer = 16
        thickness = 4
        start_angle = math.radians(60)
        end_angle = math.radians(330)
        arc_rect = pygame.Rect(cx - radius_outer, cy - radius_outer, radius_outer * 2, radius_outer * 2)
        pygame.draw.arc(screen, (255, 255, 255), arc_rect, start_angle, end_angle, thickness)
        head_angle = math.radians(60)
        tip_x = cx + radius_outer * math.cos(head_angle)
        tip_y = cy + radius_outer * math.sin(head_angle)
        arrow_len = 10
        dir_angle = head_angle - math.radians(30)
        ax = arrow_len * math.cos(dir_angle)
        ay = arrow_len * math.sin(dir_angle)
        arrow_points = [(tip_x, tip_y), (tip_x - ax - ay/3, tip_y - ay + ax/3), (tip_x - ax + ay/3, tip_y - ay - ax/3)]
        pygame.draw.polygon(screen, (255, 255, 255), arrow_points)
    elif not room_power_on:
        screen.blit(pin_img, (0, 0))
        pygame.draw.rect(screen, (0, 0, 0), RETURN_BUTTON_RECT, 0)
        pygame.draw.rect(screen, (200, 200, 200), RETURN_BUTTON_RECT, 3)
        return_text = FONT_SMALL.render("LIGHTS", True, (255, 255, 255))
        screen.blit(return_text, (RETURN_BUTTON_RECT.x + 5, RETURN_BUTTON_RECT.y + 10))
        if RETURN_BUTTON_RECT.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (50, 50, 50), RETURN_BUTTON_RECT, 0)
    else:
        # NORMAL ROOM DRAWING (your existing code)
        screen.fill((0, 0, 0))
        screen.blit(room_bg, (0, 0))
        
        if door_just_touched:
            door_just_touched = False
        
        # Restart button (unchanged)
        cx, cy = RESTART_RECT.center
        radius_outer = 16
        thickness = 4
        
        if restart_rotating:
            restart_angle += 20
            restart_frames += 1
            if restart_frames > 36:
                restart_rotating = False
                restart_angle = 0
        
        start_angle = math.radians(60 + restart_angle)
        end_angle = math.radians(330 + restart_angle)
        arc_rect = pygame.Rect(cx - radius_outer, cy - radius_outer, radius_outer * 2, radius_outer * 2)
        pygame.draw.arc(screen, (255, 255, 255), arc_rect, start_angle, end_angle, thickness)
        
        head_angle = math.radians(60 + restart_angle)
        tip_x = cx + radius_outer * math.cos(head_angle)
        tip_y = cy + radius_outer * math.sin(head_angle)
        arrow_len = 10
        dir_angle = head_angle - math.radians(30)
        ax = arrow_len * math.cos(dir_angle)
        ay = arrow_len * math.sin(dir_angle)
        arrow_points = [(tip_x, tip_y), (tip_x - ax - ay/3, tip_y - ay + ax/3), (tip_x - ax + ay/3, tip_y - ay - ax/3)]
        pygame.draw.polygon(screen, (255, 255, 255), arrow_points)
        
        if restart_hover and tooltip_timer > 30:
            tooltip_rect = pygame.Rect(55, 10, 150, 30)
            pygame.draw.rect(screen, (0, 0, 0), tooltip_rect, 0)
            pygame.draw.rect(screen, (255, 255, 255), tooltip_rect, 2)
            screen.blit(FONT_SMALL.render("Restart Game", True, (255, 255, 255)), (60, 15))
        
        # DEBUG OUTLINES
        # pygame.draw.rect(screen, (255, 0, 0), DRAWER_RECT, 2)
        # pygame.draw.rect(screen, (0, 255, 0), LEFT_DOOR_RECT, 2)
        # pygame.draw.rect(screen, (255, 128, 255), GLASS_CASE_RECT, 3)
        # pygame.draw.rect(screen, (0, 0, 255), RIGHT_DOOR_RECT, 2)
        # pygame.draw.rect(screen, (255, 255, 0), KEYPAD_RECT, 3)
        # pygame.draw.rect(screen, (0, 255, 255), MIDDLE_RECT, 2)
        # pygame.draw.rect(screen, (255, 0, 255), RIGHT_DOOR_TV_RECT, 2)
        
        # SMALL KEYPAD (unchanged)
        pygame.draw.rect(screen, (0, 0, 0), KEYPAD_RECT, 0)
        pygame.draw.rect(screen, (0, 0, 0), KEYPAD_RECT, 3)
        small_box_w, small_box_h = 12, 16
        small_start_x = KEYPAD_RECT.x + 3
        for i in range(4):
            box_x = small_start_x + i * (small_box_w + 2)
            pygame.draw.rect(screen, (40, 40, 40), (box_x, KEYPAD_RECT.y + 10, small_box_w, small_box_h), 0)
            pygame.draw.rect(screen, (200, 200, 200), (box_x, KEYPAD_RECT.y + 10, small_box_w, small_box_h), 1)
            if otp_digits[i]:
                digit_surf = FONT_TINY.render(otp_digits[i], True, (255, 255, 255))
                screen.blit(digit_surf, (box_x + 3, KEYPAD_RECT.y + 12))
        
        # TV PIN PANEL
        if tv_state in ("IMAGE", "PIN", "UNLOCKED"):
            screen.blit(tv_pin_img, RIGHT_DOOR_TV_RECT.topleft)
        
        # GLASS CASE
        if glass_case_intact:
            pass
        else:
            screen.blit(switch_img, GLASS_CASE_RECT.topleft)
        
        # LEFT DOOR IMAGE
        if left_door_unlocked_visual:
            screen.blit(left_door_img, LEFT_DOOR_RECT.topleft)
        
        # RIGHT DOOR IMAGE (NEW)
        if right_door_unlocked:
            screen.blit(right_door_img, RIGHT_DOOR_RECT.topleft)
        
        # Drawer + hammer
        if drawer_open:
            screen.blit(DRAWER_OPEN_IMG, DRAWER_RECT.topleft)
            if not hammer_taken:
                screen.blit(HAMMER_IMG, HAMMER_RECT.topleft)
        
        # Inventory (unchanged)
        pygame.draw.rect(screen, (20, 20, 20), (ROOM_WIDTH, 0, INVENTORY_WIDTH, SCREEN_HEIGHT), 0)
        screen.blit(FONT.render("Inventory", True, (255, 255, 255)), (ROOM_WIDTH + 40, 30))
        
        border_color = (255, 255, 0) if selected_item == "hammer" else (100, 100, 100)
        border_width = 4 if selected_item == "hammer" else 2
        pygame.draw.rect(screen, border_color, INVENTORY_SLOT_RECT, border_width)
        
        if hammer_taken:
            inv_hammer = pygame.transform.scale(HAMMER_IMG, (INVENTORY_SLOT_RECT.width - 20, INVENTORY_SLOT_RECT.height - 20))
            screen.blit(inv_hammer, INVENTORY_SLOT_RECT.inflate(-20, -20).topleft)
        
        if selected_item:
            screen.blit(FONT_SMALL.render(f"Selected: {selected_item}", True, (255, 255, 0)), (ROOM_WIDTH + 20, 170))
        
        # Zoomed keypad (unchanged)
        if keypad_active:
            panel_width, panel_height = 400, 160
            panel_rect = pygame.Rect((ROOM_WIDTH - panel_width) // 2, ROOM_HEIGHT - panel_height - 40, panel_width, panel_height)
            pygame.draw.rect(screen, (10, 10, 10), panel_rect, 0)
            pygame.draw.rect(screen, (200, 200, 200), panel_rect, 3)
            screen.blit(FONT.render("Enter 4-digit code:", True, (255, 255, 255)), (panel_rect.x + 20, panel_rect.y + 10))
            
            back_rect = pygame.Rect(panel_rect.x + panel_width - 40, panel_rect.y + 10, 30, 30)
            pygame.draw.rect(screen, (200, 50, 50), back_rect, 0)
            pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
            screen.blit(FONT.render("✕", True, (255, 255, 255)), (back_rect.x + 8, back_rect.y + 5))
            
            box_width, box_height = 65, 75
            start_x = panel_rect.x + 40
            for i in range(4):
                box_x = start_x + i * (box_width + 20)
                box_rect = pygame.Rect(box_x, panel_rect.y + 35, box_width, box_height)
                current_box = i == next((j for j, d in enumerate(otp_digits) if d == ""), 3)
                color = (0, 200, 255) if current_box else (50, 50, 50)
                pygame.draw.rect(screen, color, box_rect, 0)
                pygame.draw.rect(screen, (255, 255, 255), box_rect, 3)
                if otp_digits[i]:
                    screen.blit(FONT_OTP.render(otp_digits[i], True, (255, 255, 255)), (box_x + 18, panel_rect.y + 38))
                elif current_box and (OTP_CURSOR_BLINK % 40 < 20):
                    screen.blit(FONT_OTP.render("|", True, (0, 200, 255)), (box_x + 25, panel_rect.y + 38))
    
    # Messages
    if message and message_timer > 0 and room_power_on and not game_won:
        screen.blit(FONT.render(message, True, (255, 255, 255)), (40, SCREEN_HEIGHT - 50))
        message_timer -= 1
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
