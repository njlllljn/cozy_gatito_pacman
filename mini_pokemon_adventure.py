"""
Mini Pokémon Adventure
======================
A simple 2D grid-based adventure game inspired by early Pokémon games.
Made with pygame — no external assets needed, just shapes and colors!

Requirements:
    pip install pygame numpy

Run:
    python mini_pokemon_adventure.py

Controls:
    Arrow keys  — Move player
    P           — Pause
    ESC         — Quit
"""

import pygame
import sys
import random
import math
import time

pygame.init()
pygame.mixer.init()

# ──────────────────────────────────────────────
#  CONSTANTS
# ──────────────────────────────────────────────

TILE_SIZE   = 56
GRID_COLS   = 10
GRID_ROWS   = 10
MAP_WIDTH   = TILE_SIZE * GRID_COLS   # 560
MAP_HEIGHT  = TILE_SIZE * GRID_ROWS   # 560
PANEL_WIDTH = 220
SCREEN_W    = MAP_WIDTH + PANEL_WIDTH  # 780
SCREEN_H    = MAP_HEIGHT               # 560
FPS         = 60

# Colours
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0)
LIGHT_GREEN  = (168, 230, 160)
DARK_GREEN   = (34,  139, 34)
WALL_OUTLINE = (22,  90,  22)
PLAYER_BLUE  = (58,  105, 230)
PLAYER_DARK  = (30,  60,  160)
COIN_YELLOW  = (255, 210, 0)
COIN_SHINE   = (255, 245, 120)
COIN_OUTLINE = (200, 150, 0)
ENEMY_RED    = (220, 60,  60)
ENEMY_DARK   = (140, 20,  20)
PANEL_BG     = (40,  40,  80)
PANEL_LIGHT  = (60,  60,  110)
GOLD         = (255, 200, 50)
SILVER       = (200, 200, 200)
ORANGE_TEXT  = (255, 140, 30)
CYAN         = (100, 220, 220)
PINK         = (255, 160, 200)
BUTTON_GREEN = (60,  180, 60)
BUTTON_HOVER = (80,  220, 80)
BUTTON_RED   = (200, 50,  50)
BUTTON_RED_H = (240, 80,  80)
HEART_RED    = (230, 40,  40)
STAR_YELLOW  = (255, 215, 0)
STAR_GREY    = (120, 120, 120)

# ── Per-level settings 
# (enemy_count, enemy_speed_divisor, coins)
# enemy_speed_divisor: higher = slower enemies
LEVEL_SETTINGS = [
    {"enemies": 1, "enemy_slowness": 55, "coins": 6},   # level 1 — very easy
    {"enemies": 1, "enemy_slowness": 40, "coins": 7},   # level 2 — moderate
    {"enemies": 2, "enemy_slowness": 28, "coins": 8},   # level 3 — slightly tricky
]

TOTAL_LIVES       = 3
MAX_LEVELS        = 3
FAST_TIME_LIMIT   = 30   # seconds → 3 stars
MEDIUM_TIME_LIMIT = 60   # seconds → 2 stars

# ──────────────────────────────────────────────
#  SOUND GENERATION
# ──────────────────────────────────────────────

import numpy as np

def generate_sound(freq, duration_ms, volume=0.4, wave="sine"):
    sample_rate = 44100
    n_samples   = int(sample_rate * duration_ms / 1000)
    t           = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    if wave == "sine":
        data = np.sin(2 * np.pi * freq * t)
    elif wave == "square":
        data = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        data = np.random.uniform(-1, 1, n_samples)
    fade = max(1, n_samples // 10)
    data[-fade:] *= np.linspace(1, 0, fade)
    data = (data * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)

def generate_jingle(notes, duration_ms, volume=0.35):
    """Sequence of (freq, ms) pairs stitched into one sound."""
    sample_rate = 44100
    all_samples = []
    for freq, dur in notes:
        n = int(sample_rate * dur / 1000)
        t = np.linspace(0, dur / 1000, n, endpoint=False)
        wave = np.sin(2 * np.pi * freq * t)
        fade = max(1, n // 8)
        wave[-fade:] *= np.linspace(1, 0, fade)
        all_samples.append(wave)
    combined = np.concatenate(all_samples)
    combined = (combined * volume * 32767).astype(np.int16)
    stereo   = np.column_stack([combined, combined])
    return pygame.sndarray.make_sound(stereo)

try:
    SFX_COIN    = generate_sound(880,  120, 0.35, "sine")
    SFX_BUMP    = generate_sound(180,  80,  0.20, "square")
    SFX_HURT    = generate_sound(200,  300, 0.30, "square")
    SFX_GO      = generate_sound(520,  180, 0.30, "sine")
    # Short rising arpeggio jingle played when a level is beaten
    SFX_LEVEL_WIN = generate_jingle(
        [(523, 120), (659, 120), (784, 120), (1047, 300)], 660, 0.38
    )
    # Big happy fanfare for final win
    SFX_FINAL_WIN = generate_jingle(
        [(523, 100), (659, 100), (784, 100), (1047, 150),
         (784, 80),  (1047, 80), (1319, 400)], 1010, 0.38
    )
    SOUNDS_OK = True
except Exception:
    SOUNDS_OK = False

def play_sfx(sfx):
    if SOUNDS_OK:
        try:
            sfx.play()
        except Exception:
            pass


#  LEVEL MAPS  (0=open, 1=wall)


LEVEL_MAPS = [
    # Level 1 — open and friendly
    [
        [1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,0,0,0,0,0,1],
        [1,0,1,1,0,0,1,1,0,1],
        [1,0,1,0,0,0,0,1,0,1],
        [1,0,0,0,1,1,0,0,0,1],
        [1,0,0,0,1,1,0,0,0,1],
        [1,0,1,0,0,0,0,1,0,1],
        [1,0,1,1,0,0,1,1,0,1],
        [1,0,0,0,0,0,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1],
    ],
    # Level 2 — a little more winding
    [
        [1,1,1,1,1,1,1,1,1,1],
        [1,0,0,1,0,0,0,0,0,1],
        [1,0,0,1,0,1,1,1,0,1],
        [1,0,0,0,0,1,0,0,0,1],
        [1,1,1,1,0,1,0,1,1,1],
        [1,0,0,0,0,0,0,0,0,1],
        [1,0,1,1,1,0,1,1,0,1],
        [1,0,0,0,1,0,0,1,0,1],
        [1,1,0,0,0,0,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1],
    ],
    # Level 3 — spiral with clear entrance/exit so every tile is reachable
    [
        [1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,0,0,0,0,0,1],
        [1,0,1,1,1,1,1,1,0,1],
        [1,0,1,0,0,0,0,1,0,1],
        [1,0,1,0,1,1,0,1,0,1],
        [1,0,1,0,0,1,0,1,0,1],
        [1,0,1,0,0,0,0,1,0,1],
        [1,0,1,1,1,1,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1],
    ],
]


#  HELPERS


def get_open_tiles(level_map):
    tiles = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if level_map[row][col] == 0:
                tiles.append((col, row))
    return tiles

def tile_to_pixel(col, row):
    return col * TILE_SIZE, row * TILE_SIZE

def pixel_center(col, row):
    x, y = tile_to_pixel(col, row)
    return x + TILE_SIZE // 2, y + TILE_SIZE // 2


#  DRAWING — map tiles, characters, UI

def draw_tile_bg(surface, col, row):
    x, y = tile_to_pixel(col, row)
    colour = LIGHT_GREEN if (col + row) % 2 == 0 else (155, 220, 148)
    pygame.draw.rect(surface, colour, (x, y, TILE_SIZE, TILE_SIZE))

def draw_wall(surface, col, row):
    x, y = tile_to_pixel(col, row)
    pygame.draw.rect(surface, DARK_GREEN, (x, y, TILE_SIZE, TILE_SIZE))
    pygame.draw.rect(surface, (60, 170, 60), (x, y, TILE_SIZE, 6))
    pygame.draw.rect(surface, WALL_OUTLINE, (x, y, TILE_SIZE, TILE_SIZE), 2)

def draw_player(surface, col, row, anim_tick):
    cx, cy = pixel_center(col, row)
    half   = TILE_SIZE // 2 - 4
    body   = pygame.Rect(cx - half + 4, cy - half + 2, (half - 4) * 2, half * 2 - 2)
    pygame.draw.ellipse(surface, PLAYER_BLUE, body)
    pygame.draw.ellipse(surface, PLAYER_DARK, body, 2)
    head_r = half - 4
    pygame.draw.circle(surface, PLAYER_BLUE,  (cx, cy - half + 2), head_r)
    pygame.draw.circle(surface, PLAYER_DARK,  (cx, cy - half + 2), head_r, 2)
    eye_y = cy - half + 1
    for ex in (cx - 5, cx + 5):
        pygame.draw.circle(surface, WHITE,       (ex, eye_y), 4)
    pygame.draw.circle(surface, PLAYER_DARK, (cx - 4, eye_y), 2)
    pygame.draw.circle(surface, PLAYER_DARK, (cx + 4, eye_y), 2)
    foot_off = int(math.sin(anim_tick * 0.2) * 3)
    pygame.draw.ellipse(surface, PLAYER_DARK, (cx - 10, cy + half - 4 + foot_off,  10, 7))
    pygame.draw.ellipse(surface, PLAYER_DARK, (cx + 2,  cy + half - 4 - foot_off,  10, 7))

def draw_coin(surface, col, row, anim_tick):
    cx, cy = pixel_center(col, row)
    spin   = abs(math.sin(anim_tick * 0.05 + col * 0.7 + row * 1.1))
    w      = max(4, int(20 * spin))
    rect   = pygame.Rect(cx - w // 2, cy - 10, w, 20)
    pygame.draw.ellipse(surface, COIN_YELLOW, rect)
    if w > 8:
        pygame.draw.ellipse(surface, COIN_SHINE, (cx - w // 2 + 3, cy - 7, w // 3, 7))
    pygame.draw.ellipse(surface, COIN_OUTLINE, rect, 2)

def draw_enemy(surface, col, row, anim_tick):
    cx, cy = pixel_center(col, row)
    r      = TILE_SIZE // 2 - 6
    cy    += int(math.sin(anim_tick * 0.07) * 3)
    body   = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.ellipse(surface, ENEMY_RED,  body)
    pygame.draw.ellipse(surface, ENEMY_DARK, body, 2)
    for i in range(3):
        sx  = cx - r + i * (r * 2 // 3) + 4
        syt = cy + r - 4
        pts = [(sx, syt), (sx + 6, syt + 8), (sx + 12, syt)]
        pygame.draw.polygon(surface, ENEMY_RED,  pts)
        pygame.draw.polygon(surface, ENEMY_DARK, pts, 1)
    pygame.draw.circle(surface, WHITE, (cx - 7, cy - 3), 5)
    pygame.draw.circle(surface, WHITE, (cx + 7, cy - 3), 5)
    pygame.draw.circle(surface, BLACK, (cx - 6, cy - 3), 3)
    pygame.draw.circle(surface, BLACK, (cx + 8, cy - 3), 3)
    pygame.draw.line(surface, BLACK, (cx - 11, cy - 8), (cx - 3, cy - 6), 2)
    pygame.draw.line(surface, BLACK, (cx + 11, cy - 8), (cx + 3, cy - 6), 2)

def draw_heart(surface, x, y, filled=True):
    c = HEART_RED if filled else (80, 80, 80)
    pygame.draw.circle(surface, c, (x + 5,  y + 5), 5)
    pygame.draw.circle(surface, c, (x + 15, y + 5), 5)
    pygame.draw.polygon(surface, c, [(x, y + 7), (x + 10, y + 20), (x + 20, y + 7)])

def draw_star(surface, cx, cy, r, filled):
    colour = STAR_YELLOW if filled else STAR_GREY
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        dist  = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(angle) * dist, cy + math.sin(angle) * dist))
    pygame.draw.polygon(surface, colour, pts)
    pygame.draw.polygon(surface, BLACK,  pts, 1)

def draw_button(surface, rect, text, font, hovered):
    colour = BUTTON_HOVER if hovered else BUTTON_GREEN
    pygame.draw.rect(surface, colour, rect, border_radius=10)
    pygame.draw.rect(surface, WHITE,  rect, 2,  border_radius=10)
    lbl = font.render(text, True, WHITE)
    surface.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                       rect.centery - lbl.get_height() // 2))

def draw_panel(surface, score, timer_secs, lives, level, coins_left, paused):
    panel_rect = pygame.Rect(MAP_WIDTH, 0, PANEL_WIDTH, SCREEN_H)
    pygame.draw.rect(surface, PANEL_BG, panel_rect)
    pygame.draw.line(surface, PANEL_LIGHT, (MAP_WIDTH, 0), (MAP_WIDTH, SCREEN_H), 3)

    f_big   = pygame.font.SysFont("Arial", 22, bold=True)
    f_med   = pygame.font.SysFont("Arial", 18)
    f_small = pygame.font.SysFont("Arial", 14)

    px, py = MAP_WIDTH + 15, 15

    for txt, col in [("Mini Pokémon", GOLD), ("Adventure", GOLD)]:
        surface.blit(f_big.render(txt, True, col), (px, py))
        py += 26
    py += 8
    pygame.draw.line(surface, PANEL_LIGHT, (MAP_WIDTH + 10, py), (MAP_WIDTH + PANEL_WIDTH - 10, py), 1)
    py += 10

    surface.blit(f_med.render(f"Level  {level} / {MAX_LEVELS}", True, CYAN), (px, py))
    py += 32

    surface.blit(f_med.render("Score", True, SILVER), (px, py))
    surface.blit(f_big.render(str(score), True, GOLD), (px, py + 20))
    py += 55

    mins, secs = timer_secs // 60, timer_secs % 60
    surface.blit(f_med.render("Time", True, SILVER), (px, py))
    surface.blit(f_big.render(f"{mins:02d}:{secs:02d}", True, ORANGE_TEXT), (px, py + 20))
    py += 55

    surface.blit(f_med.render("Coins left", True, SILVER), (px, py))
    surface.blit(f_big.render(str(coins_left), True, COIN_YELLOW), (px, py + 20))
    py += 55

    surface.blit(f_med.render("Lives", True, SILVER), (px, py))
    py += 22
    for i in range(TOTAL_LIVES):
        draw_heart(surface, px + i * 26, py, filled=(i < lives))
    py += 30

    pygame.draw.line(surface, PANEL_LIGHT, (MAP_WIDTH + 10, py + 5), (MAP_WIDTH + PANEL_WIDTH - 10, py + 5), 1)
    py += 18

    surface.blit(f_small.render("Controls:", True, PINK), (px, py))
    py += 18
    for line in ["↑↓←→  Move", "P     Pause", "ESC   Quit"]:
        surface.blit(f_small.render(line, True, SILVER), (px, py))
        py += 16

    if paused:
        py += 10
        surface.blit(f_big.render("PAUSED", True, (255, 80, 80)), (px, py))


#  PARTICLES


def spawn_coin_particles(particles, col, row):
    cx, cy = pixel_center(col, row)
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.0)
        particles.append({
            "x": float(cx), "y": float(cy),
            "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed,
            "life": random.randint(20, 35), "max_life": 35,
            "colour": random.choice([COIN_YELLOW, COIN_SHINE, WHITE]),
            "size": random.randint(3, 7),
        })

def spawn_hurt_particles(particles, col, row):
    cx, cy = pixel_center(col, row)
    for _ in range(10):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 3)
        particles.append({
            "x": float(cx), "y": float(cy),
            "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed,
            "life": random.randint(15, 30), "max_life": 30,
            "colour": random.choice([HEART_RED, (255, 120, 60), ORANGE_TEXT]),
            "size": random.randint(4, 8),
        })

def spawn_confetti_burst(confetti_list, n=160):
    """Launch a big burst of confetti from random top positions — for the win screen."""
    confetti_colours = [
        (255, 80,  80),  (255, 200, 50),  (50,  200, 255),
        (180, 100, 255), (80,  255, 120), (255, 140, 30),
        (255, 80,  180), (100, 255, 200),
    ]
    for _ in range(n):
        confetti_list.append({
            "x"    : random.uniform(0, SCREEN_W),
            "y"    : random.uniform(-60, 0),
            "vx"   : random.uniform(-2, 2),
            "vy"   : random.uniform(2, 6),
            "rot"  : random.uniform(0, 360),
            "rot_v": random.uniform(-8, 8),
            "w"    : random.randint(7, 14),
            "h"    : random.randint(4, 9),
            "colour": random.choice(confetti_colours),
            "life" : random.randint(160, 260),
            "max_life": 260,
        })

def update_and_draw_particles(surface, particles):
    alive = []
    for p in particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
        p["life"] -= 1
        if p["life"] <= 0:
            continue
        alpha = p["life"] / p["max_life"]
        size  = max(1, int(p["size"] * alpha))
        pygame.draw.circle(surface, p["colour"], (int(p["x"]), int(p["y"])), size)
        alive.append(p)
    particles[:] = alive

def update_and_draw_confetti(surface, confetti_list):
    alive = []
    for c in confetti_list:
        c["x"]   += c["vx"]
        c["y"]   += c["vy"]
        c["vy"]  += 0.10          # gentle gravity
        c["vx"]  *= 0.995         # tiny air resistance
        c["rot"] += c["rot_v"]
        c["life"] -= 1
        if c["life"] <= 0 or c["y"] > SCREEN_H + 20:
            continue
        alpha = min(1.0, c["life"] / 40)   # fade out near end
        # Draw as a small rotated rectangle
        cx, cy = c["x"], c["y"]
        hw, hh = c["w"] / 2, c["h"] / 2
        angle  = math.radians(c["rot"])
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        pts = []
        for rx, ry in corners:
            pts.append((
                cx + rx * cos_a - ry * sin_a,
                cy + rx * sin_a + ry * cos_a,
            ))
        # Fade colour
        r, g, b = c["colour"]
        faded = (int(r * alpha), int(g * alpha), int(b * alpha))
        pygame.draw.polygon(surface, faded, pts)
        alive.append(c)
    confetti_list[:] = alive

# ──────────────────────────────────────────────
#  ENEMY LOGIC
# ──────────────────────────────────────────────

def move_enemy(enemy, level_map, player_col, player_row, slowness):
    enemy["move_timer"] -= 1
    if enemy["move_timer"] > 0:
        return
    enemy["move_timer"] = random.randint(slowness - 10, slowness + 10)

    col, row = enemy["col"], enemy["row"]
    if random.random() < 0.35:
        dc = (1 if player_col > col else -1) if player_col != col else 0
        dr = (1 if player_row > row else -1) if player_row != row else 0
        if dc != 0 and dr != 0:
            dc, dr = (dc, 0) if random.random() < 0.5 else (0, dr)
    else:
        dc, dr = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])

    nc, nr = col + dc, row + dr
    if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and level_map[nr][nc] == 0:
        enemy["col"], enemy["row"] = nc, nr

# ──────────────────────────────────────────────
#  GAME / LEVEL INIT
# ──────────────────────────────────────────────

def init_level(level_index):
    settings  = LEVEL_SETTINGS[level_index]
    level_map = LEVEL_MAPS[level_index]
    open_tiles = get_open_tiles(level_map)

    player_start = open_tiles[0]
    candidates   = [t for t in open_tiles if t != player_start]
    random.shuffle(candidates)

    coins   = candidates[:settings["coins"]]
    e_tiles = [t for t in candidates[settings["coins"]:]]
    enemies = []
    for i in range(min(settings["enemies"], len(e_tiles))):
        ec, er = e_tiles[i]
        enemies.append({
            "col": ec, "row": er,
            "move_timer": random.randint(20, settings["enemy_slowness"]),
        })

    return {
        "level_map"    : level_map,
        "player_col"   : player_start[0],
        "player_row"   : player_start[1],
        "coins"        : list(coins),
        "enemies"      : enemies,
        "particles"    : [],
        "anim_tick"    : 0,
        "invincible"   : 0,
        "move_cooldown": 0,
        "slowness"     : settings["enemy_slowness"],
    }

def init_game():
    return {
        "scene"          : "start",
        "score"          : 0,
        "lives"          : TOTAL_LIVES,
        "level_index"    : 0,
        "start_time"     : None,
        "elapsed_time"   : 0,
        "level"          : init_level(0),
        # used by the level-complete celebration screen
        "celebration_timer": 0,
        "celebration_particles": [],
        # used by the final win confetti
        "confetti"       : [],
        "confetti_done"  : False,
    }

# ──────────────────────────────────────────────
#  MOVEMENT
# ──────────────────────────────────────────────

def try_move(state, dc, dr):
    lv = state["level"]
    if lv["move_cooldown"] > 0:
        return False
    nc = lv["player_col"] + dc
    nr = lv["player_row"] + dr
    if not (0 <= nc < GRID_COLS and 0 <= nr < GRID_ROWS):
        play_sfx(SFX_BUMP)
        return False
    if lv["level_map"][nr][nc] == 1:
        play_sfx(SFX_BUMP)
        return False
    lv["player_col"] = nc
    lv["player_row"] = nr
    lv["move_cooldown"] = 8
    return True

# ──────────────────────────────────────────────
#  START SCREEN  (animated, way nicer)
# ──────────────────────────────────────────────

# Pre-built floating orb data so they don't jitter every frame
_orbs = []
_rng  = random.Random(99)
for _i in range(14):
    _orbs.append({
        "x"    : _rng.uniform(0, SCREEN_W),
        "y"    : _rng.uniform(0, SCREEN_H),
        "r"    : _rng.randint(18, 55),
        "speed": _rng.uniform(0.3, 0.9),
        "phase": _rng.uniform(0, math.pi * 2),
        "col"  : _rng.choice([
            (80, 50, 160), (50, 80, 200), (160, 100, 40),
            (40, 120, 80), (160, 50, 100), (50, 130, 160),
        ]),
    })

def draw_start_screen(surface, mouse_pos, tick):
    """Animated start screen with floating orbs, animated title, preview sprites."""
    surface.fill((18, 18, 48))

    # ── Floating background orbs ──
    for orb in _orbs:
        oy = orb["y"] + math.sin(tick * 0.01 * orb["speed"] + orb["phase"]) * 18
        pygame.draw.circle(surface, orb["col"], (int(orb["x"]), int(oy)), orb["r"])
        # soft inner highlight
        hr = max(4, orb["r"] // 3)
        hx = int(orb["x"]) - orb["r"] // 4
        hy = int(oy) - orb["r"] // 4
        pygame.draw.circle(surface, (min(255, orb["col"][0] + 60),
                                     min(255, orb["col"][1] + 60),
                                     min(255, orb["col"][2] + 60)), (hx, hy), hr)

    # ── Animated Pokéball top-centre decoration ──
    pb_cx, pb_cy = SCREEN_W // 2, 48
    pb_r   = 32
    bob    = int(math.sin(tick * 0.06) * 5)
    pb_cy += bob
    pygame.draw.circle(surface, (220, 50, 50),  (pb_cx, pb_cy), pb_r)
    pygame.draw.circle(surface, WHITE,           (pb_cx, pb_cy + pb_r // 2), pb_r // 2 + 1)
    pygame.draw.line(surface,   BLACK,           (pb_cx - pb_r, pb_cy), (pb_cx + pb_r, pb_cy), 3)
    pygame.draw.circle(surface, BLACK,           (pb_cx, pb_cy), 9)
    pygame.draw.circle(surface, (200, 200, 200), (pb_cx, pb_cy), 6)
    pygame.draw.circle(surface, BLACK,           (pb_cx, pb_cy), pb_r, 3)

    cx = SCREEN_W // 2

    # ── Title with wobble ──
    f_huge = pygame.font.SysFont("Arial", 54, bold=True)
    f_big  = pygame.font.SysFont("Arial", 30, bold=True)
    f_med  = pygame.font.SysFont("Arial", 19)
    f_sm   = pygame.font.SysFont("Arial", 15)

    # Each letter wobbles slightly offset in time
    title1 = "Mini Pokémon"
    title2 = "Adventure"
    t1_surf = f_huge.render(title1, True, GOLD)
    t2_surf = f_huge.render(title2, True, COIN_YELLOW)

    # Gentle vertical wobble on whole title lines
    t1_y = 92  + int(math.sin(tick * 0.04) * 3)
    t2_y = 152 + int(math.sin(tick * 0.04 + 0.8) * 3)
    surface.blit(t1_surf, (cx - t1_surf.get_width() // 2, t1_y))
    surface.blit(t2_surf, (cx - t2_surf.get_width() // 2, t2_y))

    # ── Divider line ──
    pygame.draw.line(surface, (80, 80, 160), (cx - 200, 210), (cx + 200, 210), 2)

    # ── Instruction lines ──
    instructions = [
        ("Collect all coins before the ghosts catch you!", (180, 200, 255)),
        ("3 levels — each one a little trickier!",          (160, 190, 240)),
        ("You have 3 lives. Touch a ghost = lose one.",     (255, 160, 160)),
    ]
    for i, (line, col) in enumerate(instructions):
        s = f_med.render(line, True, col)
        surface.blit(s, (cx - s.get_width() // 2, 225 + i * 26))

    # ── Sprite preview row ──
    preview_y = 340
    items = [
        ("You",    "player"),
        ("Coin",   "coin"),
        ("Ghost",  "enemy"),
        ("Wall",   "wall"),
    ]
    total_w  = len(items) * 110
    sx       = cx - total_w // 2 + 20

    for label, kind in items:
        # Draw the actual sprite (same functions used in-game)
        # We fake a col/row by converting pixel center back
        fake_col = sx // TILE_SIZE
        fake_row = (preview_y - 14) // TILE_SIZE
        # Just draw directly using cx/cy
        pcx, pcy = sx, preview_y

        if kind == "player":
            # mini player
            pygame.draw.circle(surface, PLAYER_BLUE, (pcx, pcy), 16)
            pygame.draw.circle(surface, PLAYER_DARK, (pcx, pcy), 16, 2)
            pygame.draw.circle(surface, WHITE,       (pcx - 5, pcy - 4), 4)
            pygame.draw.circle(surface, WHITE,       (pcx + 5, pcy - 4), 4)
            pygame.draw.circle(surface, PLAYER_DARK, (pcx - 4, pcy - 4), 2)
            pygame.draw.circle(surface, PLAYER_DARK, (pcx + 4, pcy - 4), 2)
        elif kind == "coin":
            spin = abs(math.sin(tick * 0.05))
            w    = max(4, int(20 * spin))
            pygame.draw.ellipse(surface, COIN_YELLOW,  (pcx - w // 2, pcy - 10, w, 20))
            pygame.draw.ellipse(surface, COIN_OUTLINE, (pcx - w // 2, pcy - 10, w, 20), 2)
        elif kind == "enemy":
            bob2 = int(math.sin(tick * 0.07) * 3)
            pygame.draw.circle(surface, ENEMY_RED,  (pcx, pcy + bob2), 15)
            pygame.draw.circle(surface, ENEMY_DARK, (pcx, pcy + bob2), 15, 2)
            pygame.draw.circle(surface, WHITE, (pcx - 5, pcy - 3 + bob2), 4)
            pygame.draw.circle(surface, WHITE, (pcx + 5, pcy - 3 + bob2), 4)
            pygame.draw.circle(surface, BLACK, (pcx - 4, pcy - 3 + bob2), 2)
            pygame.draw.circle(surface, BLACK, (pcx + 4, pcy - 3 + bob2), 2)
        elif kind == "wall":
            pygame.draw.rect(surface, DARK_GREEN,   (pcx - 15, pcy - 15, 30, 30))
            pygame.draw.rect(surface, (60, 170, 60),(pcx - 15, pcy - 15, 30, 5))
            pygame.draw.rect(surface, WALL_OUTLINE, (pcx - 15, pcy - 15, 30, 30), 2)

        lbl = f_sm.render(label, True, SILVER)
        surface.blit(lbl, (pcx - lbl.get_width() // 2, preview_y + 24))
        sx += 110

    # ── Pulsing START button ──
    pulse_scale = 1.0 + 0.04 * math.sin(tick * 0.08)
    btn_w = int(230 * pulse_scale)
    btn_h = int(58  * pulse_scale)
    btn_rect = pygame.Rect(cx - btn_w // 2, 415, btn_w, btn_h)
    hovered  = btn_rect.collidepoint(mouse_pos)
    draw_button(surface, btn_rect, "▶  START GAME", f_big, hovered)

    # little hint below button
    hint = f_sm.render("Click the button or press Enter", True, (100, 100, 160))
    surface.blit(hint, (cx - hint.get_width() // 2, 483))

    return btn_rect

# ──────────────────────────────────────────────
#  COUNTDOWN SCREEN
# ──────────────────────────────────────────────

def draw_countdown_screen(surface, count_val, tick, level_index):
    surface.fill((20, 20, 50))

    f_huge = pygame.font.SysFont("Arial", 160, bold=True)
    f_big  = pygame.font.SysFont("Arial", 36,  bold=True)
    cx, cy = SCREEN_W // 2, SCREEN_H // 2

    pulse = 1.0 + 0.3 * (1.0 - min(1.0, (tick % 60) / 30))

    if count_val > 0:
        text   = str(count_val)
        colour = [GOLD, COIN_YELLOW, ORANGE_TEXT][count_val - 1]
    else:
        text   = "GO!"
        colour = (100, 255, 100)

    rendered = f_huge.render(text, True, colour)
    scaled   = pygame.transform.scale(
        rendered,
        (int(rendered.get_width() * pulse), int(rendered.get_height() * pulse))
    )
    surface.blit(scaled, (cx - scaled.get_width() // 2, cy - scaled.get_height() // 2))

    msg = f_big.render(f"Level {level_index + 1} — Get ready!", True, SILVER)
    surface.blit(msg, (cx - msg.get_width() // 2, cy + 130))

# ──────────────────────────────────────────────
#  LEVEL-COMPLETE CELEBRATION SCREEN
#  (shown between levels before the countdown)
# ──────────────────────────────────────────────

def draw_level_complete_screen(surface, level_index, particles):
    surface.fill((10, 40, 20))

    f_huge = pygame.font.SysFont("Arial", 80,  bold=True)
    f_big  = pygame.font.SysFont("Arial", 34,  bold=True)
    f_med  = pygame.font.SysFont("Arial", 22)

    cx = SCREEN_W // 2

    title = f_huge.render(f"Level {level_index} Clear!", True, GOLD)
    surface.blit(title, (cx - title.get_width() // 2, 130))

    next_lv = f_big.render(f"Get ready for Level {level_index + 1}...", True, CYAN)
    surface.blit(next_lv, (cx - next_lv.get_width() // 2, 240))

    hint = f_med.render("(Starting countdown soon)", True, SILVER)
    surface.blit(hint, (cx - hint.get_width() // 2, 300))

    update_and_draw_particles(surface, particles)

# ──────────────────────────────────────────────
#  GAME SCREEN
# ──────────────────────────────────────────────

def draw_game_screen(surface, state):
    lv        = state["level"]
    level_map = lv["level_map"]
    tick      = lv["anim_tick"]

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if level_map[row][col] == 0:
                draw_tile_bg(surface, col, row)
            else:
                draw_wall(surface, col, row)

    for cc, cr in lv["coins"]:
        draw_coin(surface, cc, cr, tick)

    for enemy in lv["enemies"]:
        draw_enemy(surface, enemy["col"], enemy["row"], tick)

    if lv["invincible"] == 0 or (lv["invincible"] // 5) % 2 == 0:
        draw_player(surface, lv["player_col"], lv["player_row"], tick)

    update_and_draw_particles(surface, lv["particles"])

    f = pygame.font.SysFont("Arial", 16)
    surface.blit(f.render(f"Level {state['level_index'] + 1}", True, (60, 60, 60)), (8, 6))

    draw_panel(surface, state["score"], int(state["elapsed_time"]),
               state["lives"], state["level_index"] + 1, len(lv["coins"]),
               paused=(state["scene"] == "paused"))

def draw_pause_overlay(surface):
    overlay = pygame.Surface((MAP_WIDTH, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    surface.blit(overlay, (0, 0))
    f_huge = pygame.font.SysFont("Arial", 80, bold=True)
    f_med  = pygame.font.SysFont("Arial", 24)
    cx     = MAP_WIDTH // 2
    txt    = f_huge.render("PAUSED", True, WHITE)
    surface.blit(txt, (cx - txt.get_width() // 2, SCREEN_H // 2 - 60))
    hint = f_med.render("Press P to resume", True, SILVER)
    surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_H // 2 + 50))

# ──────────────────────────────────────────────
#  WIN SCREEN  (with confetti!)
# ──────────────────────────────────────────────

def draw_win_screen(surface, state, mouse_pos):
    surface.fill((10, 30, 10))

    # Draw confetti behind everything
    update_and_draw_confetti(surface, state["confetti"])

    f_huge = pygame.font.SysFont("Arial", 72, bold=True)
    f_big  = pygame.font.SysFont("Arial", 32, bold=True)
    f_med  = pygame.font.SysFont("Arial", 22)

    cx, cy = SCREEN_W // 2, 75

    title = f_huge.render("YOU WIN!", True, GOLD)
    surface.blit(title, (cx - title.get_width() // 2, cy))
    cy += 90

    sc = f_big.render(f"Score:  {state['score']}", True, COIN_YELLOW)
    surface.blit(sc, (cx - sc.get_width() // 2, cy))
    cy += 48

    t = int(state["elapsed_time"])
    mins, secs = t // 60, t % 60
    tm = f_big.render(f"Time:  {mins:02d}:{secs:02d}", True, CYAN)
    surface.blit(tm, (cx - tm.get_width() // 2, cy))
    cy += 52

    if t <= FAST_TIME_LIMIT:
        star_count, msg = 3, "Blazing fast!  Perfect run!"
    elif t <= MEDIUM_TIME_LIMIT:
        star_count, msg = 2, "Nice work!  Keep practising!"
    else:
        star_count, msg = 1, "You made it!  Try for a faster time."

    for i in range(3):
        draw_star(surface, cx - 60 + i * 60, cy + 5, 24, filled=(i < star_count))
    cy += 70

    msg_s = f_med.render(msg, True, SILVER)
    surface.blit(msg_s, (cx - msg_s.get_width() // 2, cy))
    cy += 50

    btn_rect = pygame.Rect(cx - 120, cy, 240, 55)
    draw_button(surface, btn_rect, "▶  PLAY AGAIN", f_big, btn_rect.collidepoint(mouse_pos))

    return btn_rect

# ──────────────────────────────────────────────
#  GAME OVER SCREEN
# ──────────────────────────────────────────────

def draw_gameover_screen(surface, state, mouse_pos):
    surface.fill((40, 0, 0))
    f_huge = pygame.font.SysFont("Arial", 80, bold=True)
    f_big  = pygame.font.SysFont("Arial", 32, bold=True)
    f_med  = pygame.font.SysFont("Arial", 22)

    cx = SCREEN_W // 2
    title = f_huge.render("GAME OVER", True, (230, 60, 60))
    surface.blit(title, (cx - title.get_width() // 2, 100))

    sc = f_big.render(f"Final Score:  {state['score']}", True, GOLD)
    surface.blit(sc, (cx - sc.get_width() // 2, 210))

    t = int(state["elapsed_time"])
    tm = f_med.render(f"Time survived:  {t // 60:02d}:{t % 60:02d}", True, SILVER)
    surface.blit(tm, (cx - tm.get_width() // 2, 268))

    tip = f_med.render("Tip: ghosts are slowest on Level 1!", True, (200, 150, 150))
    surface.blit(tip, (cx - tip.get_width() // 2, 320))

    btn_rect = pygame.Rect(cx - 120, 400, 240, 55)
    hov = btn_rect.collidepoint(mouse_pos)
    col = BUTTON_RED_H if hov else BUTTON_RED
    pygame.draw.rect(surface, col,  btn_rect, border_radius=10)
    pygame.draw.rect(surface, WHITE, btn_rect, 2, border_radius=10)
    lbl = f_big.render("↩  TRY AGAIN", True, WHITE)
    surface.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2,
                       btn_rect.centery - lbl.get_height() // 2))
    return btn_rect

# ──────────────────────────────────────────────
#  LEVEL ADVANCE
# ──────────────────────────────────────────────

def advance_level(state):
    """All coins collected on current level."""
    completed_index = state["level_index"] + 1   # human-readable level just beaten
    state["level_index"] += 1

    if state["level_index"] >= MAX_LEVELS:
        # Final win!
        play_sfx(SFX_FINAL_WIN)
        state["scene"] = "win"
        # Spawn a huge confetti burst
        spawn_confetti_burst(state["confetti"], n=200)
    else:
        # Show celebration screen, then countdown to next level
        play_sfx(SFX_LEVEL_WIN)
        state["scene"]                = "level_complete"
        state["celebration_timer"]    = FPS * 2    # 2 seconds of celebration
        state["celebration_particles"] = []
        # Spawn particles for the celebration screen
        for _ in range(6):
            cx = random.randint(100, SCREEN_W - 100)
            cy = random.randint(50, SCREEN_H - 100)
            for _ in range(15):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                state["celebration_particles"].append({
                    "x": float(cx), "y": float(cy),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - 1,
                    "life": random.randint(40, 80), "max_life": 80,
                    "colour": random.choice([GOLD, COIN_YELLOW, CYAN, PINK, WHITE]),
                    "size": random.randint(4, 9),
                })
        # Pre-load the next level quietly in the background
        state["level"] = init_level(state["level_index"])

# ──────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────

def main():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Mini Pokémon Adventure")
    clock  = pygame.time.Clock()

    state            = init_game()
    countdown_frame  = 0
    countdown_number = 3
    global_tick      = 0   # never resets, used for start screen animation

    running = True
    while running:
        clock.tick(FPS)
        global_tick += 1
        mouse_pos = pygame.mouse.get_pos()

        # ── EVENTS ────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_p:
                    if state["scene"] == "playing":
                        state["scene"] = "paused"
                    elif state["scene"] == "paused":
                        state["scene"] = "playing"

                # Enter also starts the game from start screen
                if event.key == pygame.K_RETURN and state["scene"] == "start":
                    play_sfx(SFX_GO)
                    state["scene"]   = "countdown"
                    countdown_frame  = 0
                    countdown_number = 3

                if state["scene"] == "playing":
                    if event.key == pygame.K_UP:    try_move(state, 0,  -1)
                    elif event.key == pygame.K_DOWN: try_move(state, 0,   1)
                    elif event.key == pygame.K_LEFT: try_move(state, -1,  0)
                    elif event.key == pygame.K_RIGHT:try_move(state,  1,  0)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state["scene"] == "start":
                    btn = draw_start_screen(screen, mouse_pos, global_tick)
                    if btn.collidepoint(mouse_pos):
                        play_sfx(SFX_GO)
                        state["scene"]   = "countdown"
                        countdown_frame  = 0
                        countdown_number = 3

                elif state["scene"] == "win":
                    btn = draw_win_screen(screen, state, mouse_pos)
                    if btn.collidepoint(mouse_pos):
                        state = init_game()

                elif state["scene"] == "gameover":
                    btn = draw_gameover_screen(screen, state, mouse_pos)
                    if btn.collidepoint(mouse_pos):
                        state = init_game()

        # ── SCENE UPDATES ─────────────────────────────

        if state["scene"] == "countdown":
            countdown_frame += 1
            if countdown_frame >= FPS:
                countdown_frame = 0
                countdown_number -= 1
                if countdown_number < 0:
                    state["scene"]      = "playing"
                    if state["start_time"] is None:
                        state["start_time"] = time.time()
                    else:
                        # Resuming after level — adjust start_time so elapsed keeps accumulating
                        pass
                    countdown_number = 3

        elif state["scene"] == "level_complete":
            state["celebration_timer"] -= 1
            if state["celebration_timer"] <= 0:
                # Move to countdown for next level
                state["scene"]   = "countdown"
                countdown_frame  = 0
                countdown_number = 3

        elif state["scene"] == "playing":
            lv = state["level"]
            state["elapsed_time"] = time.time() - state["start_time"]
            lv["anim_tick"] += 1

            if lv["move_cooldown"] > 0:
                lv["move_cooldown"] -= 1
            if lv["invincible"] > 0:
                lv["invincible"] -= 1

            for enemy in lv["enemies"]:
                move_enemy(enemy, lv["level_map"],
                           lv["player_col"], lv["player_row"],
                           lv["slowness"])

            player_pos = (lv["player_col"], lv["player_row"])
            if player_pos in lv["coins"]:
                lv["coins"].remove(player_pos)
                state["score"] += 10
                play_sfx(SFX_COIN)
                spawn_coin_particles(lv["particles"], lv["player_col"], lv["player_row"])

            if lv["invincible"] == 0:
                for enemy in lv["enemies"]:
                    if enemy["col"] == lv["player_col"] and enemy["row"] == lv["player_row"]:
                        state["lives"] -= 1
                        play_sfx(SFX_HURT)
                        spawn_hurt_particles(lv["particles"], lv["player_col"], lv["player_row"])
                        lv["invincible"] = 90
                        if state["lives"] <= 0:
                            state["scene"] = "gameover"
                        break

            if len(lv["coins"]) == 0:
                advance_level(state)

        # ── DRAWING ───────────────────────────────────
        screen.fill(BLACK)

        if state["scene"] == "start":
            draw_start_screen(screen, mouse_pos, global_tick)

        elif state["scene"] == "countdown":
            draw_countdown_screen(screen, countdown_number, countdown_frame, state["level_index"])

        elif state["scene"] == "level_complete":
            draw_level_complete_screen(screen, state["level_index"],
                                       state["celebration_particles"])

        elif state["scene"] in ("playing", "paused"):
            draw_game_screen(screen, state)
            if state["scene"] == "paused":
                draw_pause_overlay(screen)

        elif state["scene"] == "win":
            draw_win_screen(screen, state, mouse_pos)

        elif state["scene"] == "gameover":
            draw_gameover_screen(screen, state, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
