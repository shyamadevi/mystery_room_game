import pygame
import os
import math 

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# --- CONFIG -----------------------------------------------------------------
ROOM_WIDTH, ROOM_HEIGHT = 1152, 768
INVENTORY_WIDTH = 200
INVENTORY_AREA_X = ROOM_WIDTH

TV_RECT = pygame.Rect(665, 255, 220, 155)
TV_FRAME_RECT = pygame.Rect(635, 255, 240, 180)
TV_SCREEN_RECT = pygame.Rect(680, 285, 150, 115)
TV_TILT_ANGLE = -2

SCREEN_WIDTH, SCREEN_HEIGHT = ROOM_WIDTH + INVENTORY_WIDTH, ROOM_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mystery Room")
clock = pygame.time.Clock()

# --- LOAD BACKGROUND --------------------------------------------------------
BG_PATH = os.path.join("assets", "images", "room.png")
room_bg_raw = pygame.image.load(BG_PATH).convert()
room_bg = pygame.transform.scale(room_bg_raw, (ROOM_WIDTH, ROOM_HEIGHT))

# --- LOAD IMAGES ------------------------------------------------------------
PIN_IMG_PATH = os.path.join("assets", "images", "pin.png")
SWITCH_IMG_PATH = os.path.join("assets", "images", "switch.png")
DRAWER_OPEN_IMG = pygame.image.load(os.path.join("assets", "images", "drawer.png")).convert_alpha()
HAMMER_IMG = pygame.image.load(os.path.join("assets", "images", "hammer.png")).convert_alpha()

pin_img_raw = pygame.image.load(PIN_IMG_PATH).convert()
pin_img = pygame.transform.scale(pin_img_raw, (ROOM_WIDTH, ROOM_HEIGHT))
switch_img_raw = pygame.image.load(SWITCH_IMG_PATH).convert_alpha()
switch_img = pygame.transform.scale(switch_img_raw, (25, 45))  # match glass rect

DRAWER_OPEN_IMG = pygame.transform.scale(DRAWER_OPEN_IMG, (140, 100))
HAMMER_IMG = pygame.transform.scale(HAMMER_IMG, (40, 20))

# --- LOAD SOUNDS ------------------------------------------------------------
DRAWER_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "drowerOpenSound.mp3"))
DOOR_KNOCK_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "doorKnowking2.mp3"))
HORROR_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "horror.mp3"))
GLASS_BREAK_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "glassBroken.mp3"))
SWITCH_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "lightWitch.mp3"))  # new

DRAWER_SOUND.set_volume(0.6)
DOOR_KNOCK_SOUND.set_volume(0.7)
HORROR_SOUND.set_volume(0.3)
GLASS_BREAK_SOUND.set_volume(0.7)
SWITCH_SOUND.set_volume(0.7)

# --- INTERACTIVE OBJECTS ----------------------------------------------------
KEYPAD_RECT = pygame.Rect(160, 260, 60, 80)
DRAWER_RECT = pygame.Rect(550, 370, 140, 100)
HAMMER_RECT = pygame.Rect(590, 400, 40, 20)
LEFT_DOOR_RECT = pygame.Rect(110, 130, 160, 340)
GLASS_CASE_RECT = pygame.Rect(295, 290, 40, 70)
RIGHT_DOOR_RECT = pygame.Rect(930, 230, 140, 280)
INVENTORY_SLOT_RECT = pygame.Rect(ROOM_WIDTH + 60, 80, 80, 80)
RESTART_RECT = pygame.Rect(10, 10, 40, 40)
RETURN_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH - 120, 200, 60, 40)

# --- GAME STATE -------------------------------------------------------------
def reset_game():
    global drawer_open, hammer_taken, left_door_locked, message, message_timer
    global selected_item, keypad_active, otp_digits, door_just_touched
    global restart_rotating, restart_angle, restart_frames, restart_hover, tooltip_timer
    global glass_case_intact, glass_switch_triggered, room_power_on
    
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
    glass_switch_triggered = False
    room_power_on = True

reset_game()

# --- FONTS -------------------------------------------------------------
FONT = pygame.font.SysFont(None, 32)
FONT_SMALL = pygame.font.SysFont(None, 24)
FONT_TINY = pygame.font.SysFont(None, 20)
FONT_OTP = pygame.font.SysFont(None, 48)

CORRECT_CODE = "1234"
OTP_CURSOR_BLINK = 0

# --- HELPERS ------------------------------------------------------------
def stop_foreground_sounds():
    global door_just_touched
    DOOR_KNOCK_SOUND.stop()
    door_just_touched = False

def set_message(text, frames=120):
    global message, message_timer
    message = text
    message_timer = frames

# --- OTP HANDLING --------------------------------------------------------
def handle_otp_keydown(event):
    global otp_digits, keypad_active, left_door_locked, OTP_CURSOR_BLINK
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
        if current_pos >= 0:
            otp_digits[current_pos] = ""
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        code = "".join(otp_digits)
        if len(code) == 4:
            if code == CORRECT_CODE:
                left_door_locked = False
                set_message("Door unlocked! ✓", 180)
            else:
                set_message("Wrong code! ❌", 120)
                otp_digits = ["", "", "", ""]
        keypad_active = False

# --- CLICK HANDLER -------------------------------------------------------
def handle_click(pos):
    global drawer_open, hammer_taken, selected_item, keypad_active, door_just_touched
    global restart_rotating, restart_angle, restart_frames
    global glass_case_intact, glass_switch_triggered, room_power_on
    
    x, y = pos
    
    # RETURN BUTTON
    if RETURN_BUTTON_RECT.collidepoint(pos) and not room_power_on:
        room_power_on = True
        SWITCH_SOUND.play()  # Play sound when lights restored
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
    
    if not room_power_on:
        return
    
    if x < ROOM_WIDTH:
        # KEYPAD
        if KEYPAD_RECT.collidepoint(pos):
            stop_foreground_sounds()
            keypad_active = not keypad_active
            if not keypad_active:
                otp_digits[:] = ["", "", "", ""]
            return
        
        # GLASS CASE (switch)
        if GLASS_CASE_RECT.collidepoint(pos):
            if glass_case_intact and selected_item == "hammer":
                glass_case_intact = False
                glass_switch_triggered = True
                stop_foreground_sounds()
                GLASS_BREAK_SOUND.play()          # Play glass break sound
                set_message("Glass broken! 💥", 120)
            elif not glass_case_intact:
                room_power_on = not room_power_on
                SWITCH_SOUND.play()               # Play switch on/off sound
                set_message("Toggled switch!", 120)
            else:
                set_message("Glass case. Use hammer?", 120)
            return
        
        # HAMMER PICK
        if drawer_open and not hammer_taken and HAMMER_RECT.collidepoint(pos):
            hammer_taken = True
            stop_foreground_sounds()
            set_message("Picked up hammer. 🔨", 120)
            return
        
        # DRAWER
        if DRAWER_RECT.collidepoint(pos):
            stop_foreground_sounds()
            drawer_open = not drawer_open
            DRAWER_SOUND.play()
            set_message("Drawer opened." if drawer_open else "Drawer closed.", 60)
            return
        
        # LEFT DOOR
        if LEFT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:
                DOOR_KNOCK_SOUND.play()
                door_just_touched = True
            if left_door_locked:
                set_message("The door is locked. 🔑", 120)
            else:
                set_message("You opened the door! 🚪", 180)
            return
        
        # RIGHT DOOR
        if RIGHT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:
                DOOR_KNOCK_SOUND.play()
                door_just_touched = True
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

# --- START HORROR SOUND -------------------------------------------------
HORROR_SOUND.play(loops=-1)

# --- MAIN LOOP ----------------------------------------------------------
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
    
    # DRAW ROOM -----------------------------------------------------------
    if not room_power_on:
        screen.blit(pin_img, (0, 0))
        pygame.draw.rect(screen, (0, 0, 0), RETURN_BUTTON_RECT, 0)
        pygame.draw.rect(screen, (200, 200, 200), RETURN_BUTTON_RECT, 3)
        return_text = FONT_SMALL.render("LIGHTS", True, (255, 255, 255))
        screen.blit(return_text, (RETURN_BUTTON_RECT.x + 5, RETURN_BUTTON_RECT.y + 10))
    else:
        screen.fill((0, 0, 0))
        screen.blit(room_bg, (0, 0))
        
        # Draw objects (debug)
        pygame.draw.rect(screen, (255, 0, 0), DRAWER_RECT, 2)
        pygame.draw.rect(screen, (0, 255, 0), LEFT_DOOR_RECT, 2)
        pygame.draw.rect(screen, (255, 128, 255), GLASS_CASE_RECT, 3)
        pygame.draw.rect(screen, (0, 0, 255), RIGHT_DOOR_RECT, 2)
        pygame.draw.rect(screen, (255, 255, 0), KEYPAD_RECT, 3)
        
        if not glass_case_intact:
            screen.blit(switch_img, GLASS_CASE_RECT.topleft)
        
        if drawer_open:
            screen.blit(DRAWER_OPEN_IMG, DRAWER_RECT.topleft)
            if not hammer_taken:
                screen.blit(HAMMER_IMG, HAMMER_RECT.topleft)
        
        # Inventory
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
    
    # Message
    if message and message_timer > 0 and room_power_on:
        screen.blit(FONT.render(message, True, (255, 255, 255)), (40, SCREEN_HEIGHT - 50))
        message_timer -= 1
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
