import pygame
import os

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
DOOR_KNOCK_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "doorKnowking.mp3"))
HORROR_SOUND = pygame.mixer.Sound(os.path.join("assets", "images", "horror.mp3"))

# Set volumes
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

# --- SCALE SPRITES TO FIT THEIR RECTS --------------------------------------
DRAWER_OPEN_IMG = pygame.transform.scale(
    DRAWER_OPEN_IMG, (DRAWER_RECT.width, DRAWER_RECT.height)
)
HAMMER_IMG = pygame.transform.scale(
    HAMMER_IMG, (HAMMER_RECT.width, HAMMER_RECT.height)
)

# --- GAME STATE -------------------------------------------------------------
drawer_open = False
hammer_taken = False

left_door_locked = True

message = ""
message_timer = 0

FONT = pygame.font.SysFont(None, 32)
FONT_SMALL = pygame.font.SysFont(None, 24)

# Inventory selection
selected_item = None 

# Keypad / code input state
keypad_active = False
current_code = ""
CODE_LENGTH = 4
CORRECT_CODE = "1234"

# Sound states
horror_playing = False
door_just_touched = False  # Track single door knock

# --- HELPERS ----------------------------------------------------------------
def stop_foreground_sounds():
    """Stop drawer and door knock, but keep horror background"""
    global door_just_touched
    DOOR_KNOCK_SOUND.stop()
    door_just_touched = False

def set_message(text, frames=120):
    global message, message_timer
    message = text
    message_timer = frames

# START BACKGROUND MUSIC IMMEDIATELY
HORROR_SOUND.play(loops=-1)  # Continuous loop from start
horror_playing = True

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

    x, y = pos

    # Click in room area
    if x < ROOM_WIDTH:
        # 1) Hammer click (in drawer)
        if drawer_open and not hammer_taken and HAMMER_RECT.collidepoint(pos):
            hammer_taken = True
            stop_foreground_sounds()
            set_message("Picked up hammer.", 120)
            return

        # 2) Drawer click
        if DRAWER_RECT.collidepoint(pos):
            stop_foreground_sounds()
            drawer_open = not drawer_open
            DRAWER_SOUND.play()  # Play once
            set_message("Drawer opened." if drawer_open else "Drawer closed.", 60)
            return

        # 3) Left door click - KNOCK ONLY ONCE
        if LEFT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:  # Play knock ONLY if not just played
                DOOR_KNOCK_SOUND.play()  # Play ONCE only
                door_just_touched = True
            if left_door_locked:
                set_message("The door is locked.", 120)
            else:
                set_message("You opened the door!", 120)
            return

        # 4) Right door click - KNOCK ONLY ONCE
        if RIGHT_DOOR_RECT.collidepoint(pos):
            if not door_just_touched:  # Play knock ONLY if not just played
                DOOR_KNOCK_SOUND.play()  # Play ONCE only
                door_just_touched = True
            set_message("The door is locked.", 120)
            return

        # 5) Keypad panel click
        if KEYPAD_RECT.collidepoint(pos):
            stop_foreground_sounds()
            keypad_active = True
            return

    # Click in inventory area
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

    screen.fill((0, 0, 0))
    screen.blit(room_bg, (0, 0))

    # Reset door touch after short delay (visual feedback only)
    if door_just_touched:
        door_just_touched = False  # Reset for next click

    # Debug outlines
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

    # Inventory slot border
    if selected_item == "hammer":
        border_color = (255, 255, 0)
        border_width = 4
    else:
        border_color = (100, 100, 100)
        border_width = 2

    pygame.draw.rect(screen, border_color, INVENTORY_SLOT_RECT, border_width)

    # Hammer in inventory
    if hammer_taken:
        inv_hammer = pygame.transform.scale(
            HAMMER_IMG,
            (INVENTORY_SLOT_RECT.width - 20, INVENTORY_SLOT_HEIGHT := INVENTORY_SLOT_RECT.height - 20)
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

    # Message at bottom
    if message and message_timer > 0:
        msg_surf = FONT.render(message, True, (255, 255, 255))
        screen.blit(msg_surf, (40, SCREEN_HEIGHT - 40))
        message_timer -= 1

# --- MAIN LOOP --------------------------------------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            DOOR_KNOCK_SOUND.stop()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            handle_keydown(event)

    draw()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
