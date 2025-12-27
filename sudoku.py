import pygame
import sys
import random

pygame.init()

GRID_SIZE = 4
NUMBERS = [1, 2, 3, 4]

# AUR CHHOTI SIZE
WIDTH, HEIGHT = 200, 200      # yahan se poora sudoku chhota ho gaya
CELL_SIZE = WIDTH // GRID_SIZE

BOTTOM_PANEL_H = 60
SCREEN_H = HEIGHT + BOTTOM_PANEL_H

screen = pygame.display.set_mode((WIDTH, SCREEN_H))
pygame.display.set_caption("4x4 Sudoku (small)")

FONT = pygame.font.SysFont(None, 24)
FONT_SMALL = pygame.font.SysFont(None, 18)

CHECK_RECT = pygame.Rect(WIDTH // 2 - 45, HEIGHT + 15, 90, 30)

def generate_base_solution():
    return [
        [1, 2, 3, 4],
        [3, 4, 1, 2],
        [2, 1, 4, 3],
        [4, 3, 2, 1],
    ]

def permute_numbers(grid):
    mapping = NUMBERS[:]
    random.shuffle(mapping)
    mp = {i + 1: mapping[i] for i in range(4)}
    new = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            row.append(mp[grid[r][c]])
        new.append(row)
    return new

def swap_rows_in_band(grid):
    g = [row[:] for row in grid]
    if random.random() < 0.5:
        g[0], g[1] = g[1], g[0]
    if random.random() < 0.5:
        g[2], g[3] = g[3], g[2]
    return g

def swap_cols_in_band(grid):
    g = [row[:] for row in grid]
    if random.random() < 0.5:
        for r in range(GRID_SIZE):
            g[r][0], g[r][1] = g[r][1], g[r][0]
    if random.random() < 0.5:
        for r in range(GRID_SIZE):
            g[r][2], g[r][3] = g[r][3], g[r][2]
    return g

def generate_random_solution():
    g = generate_base_solution()
    g = permute_numbers(g)
    g = swap_rows_in_band(g)
    g = swap_cols_in_band(g)
    return g

def make_puzzle_from_solution(solution, holes=5):
    g = [row[:] for row in solution]
    cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
    random.shuffle(cells)
    for i in range(min(holes, len(cells))):
        r, c = cells[i]
        g[r][c] = 0
    return g

SOLUTION = generate_random_solution()
PUZZLE = make_puzzle_from_solution(SOLUTION, holes=5)

grid = [row[:] for row in PUZZLE]
selected = None
message = ""
message_color = (255, 255, 255)
bad_cells = []
current_key = None

def validate_4x4(grid):
    bad = []
    for r in range(GRID_SIZE):
        seen = {}
        for c in range(GRID_SIZE):
            v = grid[r][c]
            if v == 0:
                continue
            if v not in NUMBERS:
                bad.append((r, c))
            elif v in seen:
                bad.append((r, c))
                bad.append((r, seen[v]))
            else:
                seen[v] = c
    for c in range(GRID_SIZE):
        seen = {}
        for r in range(GRID_SIZE):
            v = grid[r][c]
            if v == 0:
                continue
            if v not in NUMBERS:
                bad.append((r, c))
            elif v in seen:
                bad.append((r, c))
                bad.append((seen[v], c))
            else:
                seen[v] = r
    bad = list(set(bad))
    ok = (len(bad) == 0 and
          all(all(v != 0 for v in row) for row in grid) and
          grid == SOLUTION)
    return ok, bad

def draw_grid():
    screen.fill((255, 255, 255))

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if (r, c) in bad_cells:
                pygame.draw.rect(screen, (255, 200, 200), rect)
            else:
                pygame.draw.rect(screen, (255, 255, 255), rect)

    for i in range(GRID_SIZE + 1):
        y = i * CELL_SIZE
        pygame.draw.line(screen, (0, 0, 0), (0, y), (WIDTH, y), 2)
    for j in range(GRID_SIZE + 1):
        x = j * CELL_SIZE
        pygame.draw.line(screen, (0, 0, 0), (x, 0), (x, HEIGHT), 2)

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            v = grid[r][c]
            if v != 0:
                txt = FONT.render(str(v), True, (0, 0, 0))
                tx = c * CELL_SIZE + CELL_SIZE // 2 - txt.get_width() // 2
                ty = r * CELL_SIZE + CELL_SIZE // 2 - txt.get_height() // 2
                screen.blit(txt, (tx, ty))

    if selected is not None:
        r, c = selected
        rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, (0, 0, 255), rect, 2)

    pygame.draw.rect(screen, (30, 30, 30), (0, HEIGHT, WIDTH, BOTTOM_PANEL_H))

    pygame.draw.rect(screen, (70, 130, 70), CHECK_RECT)
    pygame.draw.rect(screen, (255, 255, 255), CHECK_RECT, 2)
    chk_txt = FONT_SMALL.render("CHECK", True, (255, 255, 255))
    screen.blit(chk_txt, (CHECK_RECT.x + CHECK_RECT.width//2 - chk_txt.get_width()//2,
                          CHECK_RECT.y + CHECK_RECT.height//2 - chk_txt.get_height()//2))

    msg_txt = FONT_SMALL.render(message, True, message_color)
    screen.blit(msg_txt, (8, HEIGHT + 8))

    pygame.display.flip()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if y < HEIGHT:
                c = x // CELL_SIZE
                r = y // CELL_SIZE
                selected = (r, c)
            elif CHECK_RECT.collidepoint(event.pos):
                ok, bad_cells = validate_4x4(grid)
                if ok:
                    message = "Sudoku Solved!"
                    message_color = (0, 255, 0)

                    draw_grid()
                    pygame.display.flip()
                    pygame.time.delay(800)

                    pygame.quit()
                    sys.exit(0)   # ✅ SUCCESS → return TRUE to main.py

                else:
                    message = "Repeated / wrong numbers!"
                    message_color = (255, 80, 80)

        elif event.type == pygame.KEYDOWN:
            if selected is not None and event.unicode in ("1", "2", "3", "4"):
                r, c = selected
                grid[r][c] = int(event.unicode)
                message = ""
                bad_cells = []
            elif event.key == pygame.K_BACKSPACE:
                if selected is not None:
                    r, c = selected
                    grid[r][c] = 0
                    message = ""
                    bad_cells = []

    draw_grid()

pygame.quit()
sys.exit(1)       # ❌ failed / closed without solving

