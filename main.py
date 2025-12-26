import pygame
import os
import math

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# --- CONFIG -----------------------------------------------------------------
ROOM_WIDTH, ROOM_HEIGHT = 1152, 768
INVENTORY_WIDTH = 200
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

# --- LOAD SOUNDS -------------------------------------------------------------
DRAWER_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "drowerOpenSound.mp3"))
DOOR_KNOCK_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "doorKnowking2.mp3"))
HORROR_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "horror.mp3"))
DRAWER_SOUND.set_volume(0.6)
DOOR_KNOCK_SOUND.set_volume(0.7)
HORROR_SOUND.set_volume(0.3)

# --- INTERACTIVE OBJECTS (RECTS) ---------------------------------------------
KEYPAD_RECT = pygame.Rect(160, 260, 60, 80)  # Always visible small keypad
DRAWER_RECT = pygame.Rect(550, 370, 140, 100)
HAMMER_RECT = pygame.Rect(590, 400, 40, 20)
LEFT_DOOR_RECT = pygame.Rect(110, 150, 160, 340)  # Avoids keypad area
RIGHT_DOOR_RECT = pygame.Rect(930, 230, 140, 280)
INVENTORY_SLOT_RECT = pygame.Rect(ROOM_WIDTH + 60, 80, 80, 80)
RESTART_RECT = pygame.Rect(10, 10, 40, 40)

# --- SCALE SPRITES ----------------------------------------------------------
DRAWER_OPEN_IMG = pygame.transform.scale(DRAWER_OPEN_IMG, (DRAWER_RECT.width, DRAWER_RECT.height))
HAMMER_IMG = pygame.transform.scale(HAMMER_IMG, (HAMMER_RECT.width, HAMMER_RECT.height))

# --- GAME STATE -------------------------------------------------------------
def reset_game():
    global drawer_open, hammer_taken, left_door_locked, message, message_timer
    global selected_item, keypad_active, otp_digits, door_just_touched
    global restart_rotating, restart_angle, restart_frames, restart_hover, tooltip_timer
    
    drawer_open = False
    hammer_taken = False
    left_door_locked = True
    message = ""
    message_timer = 0
    selected_item = None
    keypad_active = False  # Full zoom state
    otp_digits = ["", "", "", ""]
    door_just_touched = False
    restart_rotating = False
    restart_angle = 0
    restart_frames = 0
    restart_hover = False
    tooltip_timer = 0

# Initialize
reset_game()
FONT = pygame.font.SysFont(None, 32)
FONT_SMALL = pygame.font.SysFont(None, 24)
FONT_TINY = pygame.font.SysFont(None, 20)  # For small keypad
FONT_OTP = pygame.font.SysFont(None, 48)
CORRECT_CODE = "1234"
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

# --- OTP INPUT HANDLING -----------------------------------------------------
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
    
    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
        code = "".join(otp_digits)
        if len(code) == 4:
            if code == CORRECT_CODE:
                left_door_locked = False
                set_message("Door unlocked! ✓", 180)
            else:
                set_message("Wrong code! ❌", 120)
                otp_digits = ["", "", "", ""]
        keypad_active = False  # Close after submit

# --- CLICK HANDLING ---------------------------------------------------------
def handle_click(pos):
    global drawer_open, hammer_taken, selected_item, keypad_active, door_just_touched
    global restart_rotating, restart_angle, restart_frames, restart_hover, tooltip_timer
    
    x, y = pos
    
    # Restart first
    if RESTART_RECT.collidepoint(pos):
        stop_foreground_sounds()
        reset_game()
        set_message("Game Restarted! 🔄", 180)
        restart_rotating = True
        restart_angle = 0
        restart_frames = 0
        return
    
    # Room area
    if x < ROOM_WIDTH:
        # KEYPAD - Toggle zoom
        if KEYPAD_RECT.collidepoint(pos):
            stop_foreground_sounds()
            keypad_active = not keypad_active  # Toggle on/off
            if not keypad_active:
                otp_digits = ["", "", "", ""]  # Reset when closing
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
        
        # Left door (adjusted to avoid keypad)
        if LEFT_DOOR_RECT.collidepoint(pos) and not KEYPAD_RECT.collidepoint(pos):
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
    
    # Mouse hover
    mouse_pos = pygame.mouse.get_pos()
    restart_hover = RESTART_RECT.collidepoint(mouse_pos)
    if restart_hover:
        tooltip_timer += 1
    else:
        tooltip_timer = 0
    
    OTP_CURSOR_BLINK += 1
    
    # --- DRAWING -----------------------------------------------------------
    screen.fill((0, 0, 0))
    screen.blit(room_bg, (0, 0))
    
    if door_just_touched:
        door_just_touched = False
    
    # Restart button + tooltip (same as before)
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
    arrow_points = [(tip_x, tip_y),
                   (tip_x - ax - ay/3, tip_y - ay + ax/3),
                   (tip_x - ax + ay/3, tip_y - ay - ax/3)]
    pygame.draw.polygon(screen, (255, 255, 255), arrow_points)
    
    if restart_hover and tooltip_timer > 30:
        tooltip_rect = pygame.Rect(55, 10, 150, 30)
        pygame.draw.rect(screen, (0, 0, 0), tooltip_rect, 0)
        pygame.draw.rect(screen, (255, 255, 255), tooltip_rect, 2)
        tooltip_text = FONT_SMALL.render("Restart Game", True, (255, 255, 255))
        screen.blit(tooltip_text, (60, 15))
    
    # Debug outlines
    pygame.draw.rect(screen, (255, 0, 0), DRAWER_RECT, 2)
    pygame.draw.rect(screen, (0, 255, 0), LEFT_DOOR_RECT, 2)
    pygame.draw.rect(screen, (0, 0, 255), RIGHT_DOOR_RECT, 2)
    
    # **SMALL KEYPAD - ALWAYS VISIBLE**
    pygame.draw.rect(screen, (255, 255, 0), KEYPAD_RECT, 0)
    pygame.draw.rect(screen, (0, 0, 0), KEYPAD_RECT, 3)
    
    # 4 tiny boxes inside yellow keypad
    small_box_w, small_box_h = 12, 16
    small_start_x = KEYPAD_RECT.x + 3
    small_start_y = KEYPAD_RECT.y + 10
    for i in range(4):
        box_x = small_start_x + i * (small_box_w + 2)
        box_y = small_start_y
        pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, small_box_w, small_box_h), 0)
        pygame.draw.rect(screen, (200, 200, 200), (box_x, box_y, small_box_w, small_box_h), 1)
        
        if otp_digits[i]:  # Show digits even in small view
            digit_surf = FONT_TINY.render(otp_digits[i], True, (255, 255, 255))
            digit_rect = digit_surf.get_rect(center=(box_x + small_box_w//2, box_y + small_box_h//2))
            screen.blit(digit_surf, digit_rect)
    
    # Drawer + hammer
    if drawer_open:
        screen.blit(DRAWER_OPEN_IMG, DRAWER_RECT.topleft)
        if not hammer_taken:
            screen.blit(HAMMER_IMG, HAMMER_RECT.topleft)
    
    # Inventory (same)
    pygame.draw.rect(screen, (20, 20, 20), (ROOM_WIDTH, 0, INVENTORY_WIDTH, SCREEN_HEIGHT), 0)
    inv_text = FONT.render("Inventory", True, (255, 255, 255))
    screen.blit(inv_text, (ROOM_WIDTH + 40, 30))
    
    border_color = (255, 255, 0) if selected_item == "hammer" else (100, 100, 100)
    border_width = 4 if selected_item == "hammer" else 2
    pygame.draw.rect(screen, border_color, INVENTORY_SLOT_RECT, border_width)
    
    if hammer_taken:
        inv_hammer = pygame.transform.scale(HAMMER_IMG, (INVENTORY_SLOT_RECT.width - 20, INVENTORY_SLOT_RECT.height - 20))
        screen.blit(inv_hammer, INVENTORY_SLOT_RECT.inflate(-20, -20).topleft)
    
    if selected_item:
        sel_text = FONT_SMALL.render(f"Selected: {selected_item}", True, (255, 255, 0))
        screen.blit(sel_text, (ROOM_WIDTH + 20, 170))
    
    # **ZOOMED FULL KEYPAD (when active)**
    if keypad_active:
        panel_width, panel_height = 400, 160
        panel_y = ROOM_HEIGHT - panel_height - 40
        panel_rect = pygame.Rect((ROOM_WIDTH - panel_width) // 2, panel_y, panel_width, panel_height)
        
        # Main panel
        pygame.draw.rect(screen, (10, 10, 10), panel_rect, 0)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 3)
        
        # Title
        prompt = FONT.render("Enter 4-digit code:", True, (255, 255, 255))
        screen.blit(prompt, (panel_rect.x + 20, panel_rect.y + 10))
        
        # **BACK BUTTON (X)**
        back_rect = pygame.Rect(panel_rect.x + panel_width - 40, panel_rect.y + 10, 30, 30)
        pygame.draw.rect(screen, (200, 50, 50), back_rect, 0)
        pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
        back_x_surf = FONT.render("✕", True, (255, 255, 255))
        screen.blit(back_x_surf, (back_rect.x + 8, back_rect.y + 5))
        
        # 4 big OTP boxes
        box_width, box_height = 65, 75
        box_spacing = 20
        start_x = panel_rect.x + 40
        
        for i in range(4):
            box_x = start_x + i * (box_width + box_spacing)
            box_y = panel_rect.y + 35
            box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            
            # Highlight current empty box
            current_box = i == next((j for j, d in enumerate(otp_digits) if d == ""), 3)
            color = (0, 200, 255) if current_box else (50, 50, 50)
            pygame.draw.rect(screen, color, box_rect, 0)
            pygame.draw.rect(screen, (255, 255, 255), box_rect, 3)
            
            # Digit or cursor
            if otp_digits[i]:
                digit_surf = FONT_OTP.render(otp_digits[i], True, (255, 255, 255))
                screen.blit(digit_surf, (box_x + 18, box_y + 12))
            elif current_box and (OTP_CURSOR_BLINK % 40 < 20):
                cursor_surf = FONT_OTP.render("|", True, (0, 200, 255))
                screen.blit(cursor_surf, (box_x + 25, box_y + 12))
        
        # Instructions
        instr = FONT_SMALL.render("Numbers 0-9 | Backspace | Enter to submit", True, (150, 150, 150))
        screen.blit(instr, (panel_rect.x + 20, panel_rect.y + 120))
        
        # **BACK BUTTON CLICK DETECTION** (in main loop above this would be handled)
        if back_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 100, 100), back_rect, 0)  # Hover effect
    
    # Click back button
    if keypad_active:
        back_rect = pygame.Rect((ROOM_WIDTH - 400 + 360), ROOM_HEIGHT - 200 - 40 + 10, 30, 30)
        if back_rect.collidepoint(mouse_pos):
            # Hover effect already drawn above
            if pygame.mouse.get_pressed()[0]:  # Left click held
                keypad_active = False
                otp_digits = ["", "", "", ""]
    
    # Messages
    if message and message_timer > 0:
        msg_surf = FONT.render(message, True, (255, 255, 255))
        screen.blit(msg_surf, (40, SCREEN_HEIGHT - 50))
        message_timer -= 1
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
