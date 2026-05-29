"""
Cozy Garden Adventure
=====================
A cozy pixel-art cottagecore game — like Pac-Man redesigned as a
tiny Sprout Valley farm game. Collect all the strawberries before
the cute gatito creatures find you!

Requirements:
    pip install pygame numpy

Run:
    python cozy_garden_adventure.py

Controls:
    Arrow keys  — Move player (pixel cat!)
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
#  SPRITE IMAGE PATHS
#  Put the game file in the same folder as these,
#  or adjust the paths below if needed.
# ──────────────────────────────────────────────

import os

_HERE = os.path.dirname(os.path.abspath(__file__))

SPRITE_PATHS = {
    "cat_closed": os.path.join(_HERE, "pixel_cat.jpeg"),       # idle / closed mouth
    "cat_open":   os.path.join(_HERE, "_.jpeg"),               # chomping / moving
    "gatito":     os.path.join(_HERE, "____Gatito_pixel____.jpeg"),  # enemy
}

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

# ── Cozy pastel palette (inspired by Sprout Valley) ──
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0)
CREAM        = (255, 248, 235)
SOFT_PINK    = (255, 192, 203)
DUSTY_ROSE   = (220, 160, 170)
BLUSH        = (255, 210, 220)
WARM_GREEN   = (140, 195, 100)
SOFT_GREEN   = (180, 220, 140)
PASTEL_GREEN = (210, 240, 180)
DARK_GREEN   = (90,  140, 70)
HEDGE_GREEN  = (100, 155, 80)
HEDGE_DARK   = (70,  110, 55)
HEDGE_LIGHT  = (130, 185, 100)
MUTED_BROWN  = (165, 120, 80)
WARM_BROWN   = (190, 145, 100)
LIGHT_BROWN  = (220, 185, 145)
PANEL_CREAM  = (245, 235, 215)
PANEL_WARM   = (230, 215, 190)
PANEL_BORDER = (190, 165, 130)
BERRY_RED    = (220, 80,  90)
BERRY_SHINE  = (245, 130, 140)
BERRY_DARK   = (170, 50,  60)
BERRY_LEAF   = (80,  160, 70)
GOLD         = (220, 175, 60)
SOFT_GOLD    = (240, 205, 100)
ORANGE_WARM  = (230, 150, 60)
LAVENDER     = (195, 175, 230)
SOFT_TEAL    = (140, 205, 195)
HEART_RED    = (220, 90,  90)
STAR_GOLD    = (235, 195, 50)
STAR_GREY    = (185, 175, 160)
PATH_LIGHT   = (230, 215, 185)
PATH_MID     = (215, 198, 165)
BUTTON_SAGE  = (130, 175, 110)
BUTTON_HOVER = (155, 205, 130)
BUTTON_RED   = (200, 110, 110)
BUTTON_RED_H = (225, 140, 140)
FLOWER_PINK  = (240, 180, 200)
FLOWER_YELL  = (240, 220, 100)
MUSHROOM_CAP = (210, 110, 100)
MUSHROOM_STE = (235, 215, 195)

# ──────────────────────────────────────────────
#  LOAD & PREP SPRITES
#  Called once after display is created. White backgrounds
#  are made transparent via colorkey. Falls back gracefully
#  if an image file is missing.
# ──────────────────────────────────────────────

_SPRITE_CACHE = {}

def _load_sprite(key, size):
    """Load a sprite image, scale it, and apply white-bg transparency."""
    path = SPRITE_PATHS.get(key, "")
    if not os.path.exists(path):
        return None
    img = pygame.image.load(path).convert()
    img.set_colorkey((255, 255, 255))   # white background → transparent
    img = pygame.transform.scale(img, size)
    return img

def load_all_sprites():
    """Call this once after pygame.display.set_mode() is ready."""
    sprite_size = (TILE_SIZE - 6, TILE_SIZE - 6)   # fits neatly inside a tile
    _SPRITE_CACHE["cat_closed"] = _load_sprite("cat_closed", sprite_size)
    _SPRITE_CACHE["cat_open"]   = _load_sprite("cat_open",   sprite_size)
    _SPRITE_CACHE["gatito"]     = _load_sprite("gatito",     sprite_size)

# ── Per-level settings (unchanged from original) ──
LEVEL_SETTINGS = [
    {"enemies": 1, "enemy_slowness": 55, "coins": 6},
    {"enemies": 1, "enemy_slowness": 40, "coins": 7},
    {"enemies": 2, "enemy_slowness": 28, "coins": 8},
]

TOTAL_LIVES       = 3
MAX_LEVELS        = 3
FAST_TIME_LIMIT   = 30
MEDIUM_TIME_LIMIT = 60

# ──────────────────────────────────────────────
#  SOUND (unchanged)
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
    SFX_COIN      = generate_sound(880,  120, 0.35, "sine")
    SFX_BUMP      = generate_sound(180,   80, 0.20, "square")
    SFX_HURT      = generate_sound(200,  300, 0.30, "square")
    SFX_GO        = generate_sound(520,  180, 0.30, "sine")
    SFX_LEVEL_WIN = generate_jingle(
        [(523, 120), (659, 120), (784, 120), (1047, 300)], 660, 0.38)
    SFX_FINAL_WIN = generate_jingle(
        [(523, 100), (659, 100), (784, 100), (1047, 150),
         (784,  80), (1047,  80), (1319, 400)], 1010, 0.38)
    SOUNDS_OK = True
except Exception:
    SOUNDS_OK = False

def play_sfx(sfx):
    if SOUNDS_OK:
        try:
            sfx.play()
        except Exception:
            pass

# ──────────────────────────────────────────────
#  LEVEL MAPS  (0=path, 1=hedge/wall)
# ──────────────────────────────────────────────

LEVEL_MAPS = [
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

# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

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

# ──────────────────────────────────────────────
#  SPRITE DRAWING — cozy pixel-art style
# ──────────────────────────────────────────────

def draw_tile_bg(surface, col, row, tick=0):
    """Grassy path tile — soft checkerboard with tiny variation."""
    x, y = tile_to_pixel(col, row)
    base = PASTEL_GREEN if (col + row) % 2 == 0 else SOFT_GREEN
    pygame.draw.rect(surface, base, (x, y, TILE_SIZE, TILE_SIZE))
    # tiny grass tuft details to add texture
    rng = random.Random(col * 100 + row * 7 + 13)
    for _ in range(3):
        tx = x + rng.randint(4, TILE_SIZE - 8)
        ty = y + rng.randint(4, TILE_SIZE - 8)
        col_shade = (
            min(255, base[0] - 20),
            min(255, base[1] - 15),
            base[2]
        )
        pygame.draw.line(surface, col_shade, (tx, ty), (tx, ty - 4), 1)

def draw_stone_path(surface, col, row):
    """Stone path for walkable tiles bordering walls — cozy cobblestone."""
    x, y = tile_to_pixel(col, row)
    pygame.draw.rect(surface, PATH_MID, (x, y, TILE_SIZE, TILE_SIZE))
    # draw a couple of rounded stone shapes
    rng = random.Random(col * 53 + row * 31)
    stones = [
        (x + 5,  y + 5,  22, 18),
        (x + 30, y + 8,  18, 15),
        (x + 8,  y + 30, 20, 16),
        (x + 32, y + 32, 16, 14),
    ]
    for i, (sx, sy, sw, sh) in enumerate(stones):
        shade = PATH_LIGHT if i % 2 == 0 else PATH_MID
        pygame.draw.ellipse(surface, shade, (sx, sy, sw, sh))
        pygame.draw.ellipse(surface, PANEL_BORDER, (sx, sy, sw, sh), 1)

def draw_hedge(surface, col, row):
    """Hedge/bush wall tile — looks like a rounded leafy bush."""
    x, y = tile_to_pixel(col, row)
    # base fill
    pygame.draw.rect(surface, HEDGE_GREEN, (x, y, TILE_SIZE, TILE_SIZE))
    # draw layered bush circles for a leafy look
    rng = random.Random(col * 17 + row * 43)
    bumps = [
        (x + 6,  y + 12, 20),
        (x + 18, y + 6,  22),
        (x + 32, y + 10, 20),
        (x + 44, y + 15, 16),
        (x + 10, y + 28, 18),
        (x + 36, y + 26, 20),
    ]
    for bx, by, br in bumps:
        pygame.draw.circle(surface, HEDGE_GREEN, (bx, by), br)
        # highlight top of each bump
        pygame.draw.circle(surface, HEDGE_LIGHT, (bx - 3, by - 4), br // 3)
    # dark outline to give shape
    pygame.draw.rect(surface, HEDGE_DARK, (x, y, TILE_SIZE, TILE_SIZE), 2)
    # tiny flowers scattered on hedges
    rng2 = random.Random(col * 7 + row * 11)
    if rng2.random() > 0.55:
        fx = x + rng2.randint(10, TILE_SIZE - 14)
        fy = y + rng2.randint(8, TILE_SIZE - 14)
        fc = rng2.choice([FLOWER_PINK, FLOWER_YELL, WHITE])
        pygame.draw.circle(surface, fc, (fx, fy), 4)
        pygame.draw.circle(surface, GOLD, (fx, fy), 2)

def draw_player(surface, col, row, anim_tick, is_moving):
    """
    Blits the real pixel cat sprite from the uploaded images.
    Closed-mouth = idle frame, open-mouth = chomping frame (alternates
    every 6 ticks while moving). Falls back to a plain circle if the
    image files aren't found next to the script.
    """
    cx, cy = pixel_center(col, row)

    # pick frame: open mouth while moving (every other 6-tick window)
    use_open = is_moving and (anim_tick // 6) % 2 == 0
    key      = "cat_open" if use_open else "cat_closed"
    sprite   = _SPRITE_CACHE.get(key)

    if sprite:
        rect = sprite.get_rect(center=(cx, cy))
        surface.blit(sprite, rect)
    else:
        # fallback shape if image files are missing
        pygame.draw.circle(surface, CREAM,       (cx, cy), TILE_SIZE // 2 - 6)
        pygame.draw.circle(surface, MUTED_BROWN, (cx, cy), TILE_SIZE // 2 - 6, 2)


def draw_strawberry(surface, col, row, anim_tick):
    """Cute pixel strawberry collectible with a gentle spin bob."""
    cx, cy = pixel_center(col, row)
    bob = int(math.sin(anim_tick * 0.06 + col * 0.9 + row * 1.3) * 3)
    cy += bob

    # berry body — red teardrop shape built from circles + rect
    pygame.draw.circle(surface, BERRY_RED,  (cx, cy + 4), 11)
    pygame.draw.rect(surface,  BERRY_RED,   (cx - 8, cy - 2, 16, 10))
    pygame.draw.circle(surface, BERRY_RED,  (cx - 5, cy - 2), 7)
    pygame.draw.circle(surface, BERRY_RED,  (cx + 5, cy - 2), 7)
    # outline
    pygame.draw.circle(surface, BERRY_DARK, (cx, cy + 4), 11, 2)
    pygame.draw.circle(surface, BERRY_DARK, (cx - 5, cy - 2), 7, 2)
    pygame.draw.circle(surface, BERRY_DARK, (cx + 5, cy - 2), 7, 2)
    # shine dot
    pygame.draw.circle(surface, BERRY_SHINE, (cx - 4, cy - 2), 3)
    # seed dots
    for sdx, sdy in [(-3, 4), (3, 4), (0, 9), (-5, 8), (5, 8)]:
        pygame.draw.circle(surface, BERRY_DARK, (cx + sdx, cy + sdy), 1)
    # leaf / stem on top
    pygame.draw.line(surface, BERRY_LEAF, (cx, cy - 10), (cx, cy - 16), 2)
    pygame.draw.ellipse(surface, BERRY_LEAF, (cx - 6, cy - 16, 7, 5))
    pygame.draw.ellipse(surface, BERRY_LEAF, (cx,     cy - 15, 7, 5))


def draw_gatito(surface, col, row, anim_tick):
    """
    Blits the real gatito sprite (cute pink creature with green leaf hair).
    Bobs gently up and down. Falls back to a lavender circle if image missing.
    """
    cx, cy = pixel_center(col, row)
    bob    = int(math.sin(anim_tick * 0.07) * 4)

    sprite = _SPRITE_CACHE.get("gatito")
    if sprite:
        rect = sprite.get_rect(center=(cx, cy + bob))
        surface.blit(sprite, rect)
    else:
        # fallback shape
        pygame.draw.circle(surface, LAVENDER,    (cx, cy + bob), TILE_SIZE // 2 - 6)
        pygame.draw.circle(surface, MUTED_BROWN, (cx, cy + bob), TILE_SIZE // 2 - 6, 2)


def draw_heart(surface, x, y, filled=True):
    c = HEART_RED if filled else (185, 165, 155)
    pygame.draw.circle(surface, c, (x + 5,  y + 5), 5)
    pygame.draw.circle(surface, c, (x + 15, y + 5), 5)
    pygame.draw.polygon(surface, c, [(x, y + 7), (x + 10, y + 20), (x + 20, y + 7)])


def draw_star(surface, cx, cy, r, filled):
    colour = STAR_GOLD if filled else STAR_GREY
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        dist  = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(angle) * dist, cy + math.sin(angle) * dist))
    pygame.draw.polygon(surface, colour, pts)
    pygame.draw.polygon(surface, MUTED_BROWN, pts, 1)


def draw_cozy_button(surface, rect, text, font, hovered):
    """Rounded pastel sage button — friendly and soft."""
    colour = BUTTON_HOVER if hovered else BUTTON_SAGE
    # shadow
    shadow = rect.move(3, 3)
    pygame.draw.rect(surface, HEDGE_DARK, shadow, border_radius=12)
    # main button
    pygame.draw.rect(surface, colour, rect, border_radius=12)
    pygame.draw.rect(surface, WHITE,   rect, 2, border_radius=12)
    lbl = font.render(text, True, WHITE)
    surface.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                       rect.centery - lbl.get_height() // 2))


def draw_panel(surface, score, timer_secs, lives, level, coins_left, paused):
    """Cozy wooden side panel with cream/warm tones."""
    panel_rect = pygame.Rect(MAP_WIDTH, 0, PANEL_WIDTH, SCREEN_H)
    pygame.draw.rect(surface, PANEL_CREAM, panel_rect)
    # left border — like a wooden plank edge
    pygame.draw.rect(surface, PANEL_BORDER, (MAP_WIDTH, 0, 5, SCREEN_H))
    pygame.draw.rect(surface, WARM_BROWN,   (MAP_WIDTH + 2, 0, 2, SCREEN_H))

    f_title = pygame.font.SysFont("Georgia", 18, bold=True)
    f_big   = pygame.font.SysFont("Georgia", 20, bold=True)
    f_med   = pygame.font.SysFont("Georgia", 16)
    f_small = pygame.font.SysFont("Georgia", 13)

    px, py = MAP_WIDTH + 18, 14

    # title
    for txt in ["Cozy Garden", "Adventure"]:
        surf = f_title.render(txt, True, WARM_BROWN)
        surface.blit(surf, (MAP_WIDTH + PANEL_WIDTH // 2 - surf.get_width() // 2, py))
        py += 22
    py += 6

    # divider (little vine line)
    pygame.draw.line(surface, PANEL_BORDER,
                     (MAP_WIDTH + 14, py), (MAP_WIDTH + PANEL_WIDTH - 14, py), 2)
    py += 12

    # Level
    lv_surf = f_med.render(f"Garden {level} of {MAX_LEVELS}", True, DARK_GREEN)
    surface.blit(lv_surf, (px, py)); py += 30

    # Score
    surface.blit(f_med.render("Score", True, MUTED_BROWN), (px, py))
    surface.blit(f_big.render(str(score), True, WARM_BROWN), (px, py + 18))
    py += 50

    # Time
    mins, secs = timer_secs // 60, timer_secs % 60
    surface.blit(f_med.render("Time", True, MUTED_BROWN), (px, py))
    surface.blit(f_big.render(f"{mins:02d}:{secs:02d}", True, ORANGE_WARM), (px, py + 18))
    py += 50

    # Berries left
    surface.blit(f_med.render("Berries left", True, MUTED_BROWN), (px, py))
    surface.blit(f_big.render(str(coins_left), True, BERRY_RED), (px, py + 18))
    py += 50

    # Lives
    surface.blit(f_med.render("Lives", True, MUTED_BROWN), (px, py)); py += 20
    for i in range(TOTAL_LIVES):
        draw_heart(surface, px + i * 28, py, filled=(i < lives))
    py += 32

    pygame.draw.line(surface, PANEL_BORDER,
                     (MAP_WIDTH + 14, py), (MAP_WIDTH + PANEL_WIDTH - 14, py), 2)
    py += 12

    surface.blit(f_small.render("Controls:", True, MUTED_BROWN), (px, py)); py += 16
    for line in ["↑↓←→  Walk", "P     Pause", "ESC   Quit"]:
        surface.blit(f_small.render(line, True, (150, 120, 90)), (px, py))
        py += 14

    if paused:
        py += 8
        surface.blit(f_big.render("PAUSED ~", True, DUSTY_ROSE), (px, py))

# ──────────────────────────────────────────────
#  DECORATION — tiny flowers & mushrooms on edges
# ──────────────────────────────────────────────

# Pre-bake some edge decorations so they don't shuffle each frame
_decoration_rng = random.Random(42)
_decorations = []
for _dc in range(GRID_COLS):
    for _dr in range(GRID_ROWS):
        if _decoration_rng.random() < 0.18:
            _decorations.append({
                "col": _dc, "row": _dr,
                "type": _decoration_rng.choice(["flower", "mushroom", "clover"]),
                "ox": _decoration_rng.randint(-14, 14),
                "oy": _decoration_rng.randint(-14, 14),
                "color": _decoration_rng.choice([FLOWER_PINK, FLOWER_YELL, WHITE, SOFT_TEAL]),
            })

def draw_tile_decorations(surface, level_map, tick):
    """Draw tiny flowers, mushrooms on open path tiles."""
    for d in _decorations:
        col, row = d["col"], d["row"]
        if col >= GRID_COLS or row >= GRID_ROWS:
            continue
        if level_map[row][col] != 0:
            continue
        cx, cy = pixel_center(col, row)
        x = cx + d["ox"]
        y = cy + d["oy"]
        if d["type"] == "flower":
            # 4 petals + center
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                px = x + int(math.cos(rad) * 4)
                py = y + int(math.sin(rad) * 4)
                pygame.draw.circle(surface, d["color"], (px, py), 3)
            pygame.draw.circle(surface, SOFT_GOLD, (x, y), 2)
        elif d["type"] == "mushroom":
            # stem
            pygame.draw.rect(surface, MUSHROOM_STE, (x - 2, y, 4, 5))
            # cap
            pygame.draw.ellipse(surface, MUSHROOM_CAP, (x - 5, y - 5, 10, 7))
            pygame.draw.circle(surface, WHITE, (x - 2, y - 3), 1)
            pygame.draw.circle(surface, WHITE, (x + 1, y - 2), 1)
        elif d["type"] == "clover":
            for angle in [0, 120, 240]:
                rad = math.radians(angle)
                lx = x + int(math.cos(rad) * 3)
                ly = y + int(math.sin(rad) * 3)
                pygame.draw.circle(surface, WARM_GREEN, (lx, ly), 3)

# ──────────────────────────────────────────────
#  PARTICLES
# ──────────────────────────────────────────────

def spawn_berry_particles(particles, col, row):
    cx, cy = pixel_center(col, row)
    # sparkle burst in warm pink/red tones
    for _ in range(14):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.5)
        particles.append({
            "x": float(cx), "y": float(cy),
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(20, 38),
            "max_life": 38,
            "colour": random.choice([BERRY_RED, BERRY_SHINE, SOFT_PINK, SOFT_GOLD, WHITE]),
            "size": random.randint(3, 7),
        })

def spawn_hurt_particles(particles, col, row):
    cx, cy = pixel_center(col, row)
    for _ in range(10):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 3)
        particles.append({
            "x": float(cx), "y": float(cy),
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(15, 30),
            "max_life": 30,
            "colour": random.choice([HEART_RED, DUSTY_ROSE, ORANGE_WARM]),
            "size": random.randint(4, 8),
        })

def spawn_confetti_burst(confetti_list, n=160):
    # pastel confetti for the win screen
    colours = [
        SOFT_PINK, BERRY_SHINE, SOFT_GOLD, WARM_GREEN, LAVENDER,
        BLUSH, SOFT_TEAL, FLOWER_YELL, CREAM,
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
            "colour": random.choice(colours),
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
        c["vy"]  += 0.10
        c["vx"]  *= 0.995
        c["rot"] += c["rot_v"]
        c["life"] -= 1
        if c["life"] <= 0 or c["y"] > SCREEN_H + 20:
            continue
        alpha = min(1.0, c["life"] / 40)
        cx2, cy2 = c["x"], c["y"]
        hw, hh = c["w"] / 2, c["h"] / 2
        angle  = math.radians(c["rot"])
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        pts = []
        for rx, ry in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
            pts.append((
                cx2 + rx * cos_a - ry * sin_a,
                cy2 + rx * sin_a + ry * cos_a,
            ))
        r, g, b = c["colour"]
        faded = (int(r * alpha), int(g * alpha), int(b * alpha))
        pygame.draw.polygon(surface, faded, pts)
        alive.append(c)
    confetti_list[:] = alive

# ──────────────────────────────────────────────
#  ENEMY LOGIC (unchanged)
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
#  GAME / LEVEL INIT (unchanged logic)
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
        "is_moving"    : False,  # new — tracks whether player moved this tick
    }

def init_game():
    return {
        "scene"                : "start",
        "score"                : 0,
        "lives"                : TOTAL_LIVES,
        "level_index"          : 0,
        "start_time"           : None,
        "elapsed_time"         : 0,
        "level"                : init_level(0),
        "celebration_timer"    : 0,
        "celebration_particles": [],
        "confetti"             : [],
        "confetti_done"        : False,
    }

# ──────────────────────────────────────────────
#  MOVEMENT (unchanged)
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
    lv["player_col"]   = nc
    lv["player_row"]   = nr
    lv["move_cooldown"] = 8
    lv["is_moving"]    = True
    return True

# ──────────────────────────────────────────────
#  START SCREEN — cozy cottagecore style
# ──────────────────────────────────────────────

# pre-bake floating leaf/petal positions
_start_petals = []
_petal_rng    = random.Random(77)
for _i in range(18):
    _start_petals.append({
        "x"    : _petal_rng.uniform(0, SCREEN_W),
        "y"    : _petal_rng.uniform(0, SCREEN_H),
        "r"    : _petal_rng.randint(10, 36),
        "speed": _petal_rng.uniform(0.2, 0.7),
        "phase": _petal_rng.uniform(0, math.pi * 2),
        "col"  : _petal_rng.choice([
            (220, 200, 235), (240, 210, 220), (210, 235, 210),
            (240, 235, 200), (210, 230, 240), (230, 215, 240),
        ]),
    })

def draw_start_screen(surface, mouse_pos, tick):
    """Animated cozy start screen — soft pastel, floating petals, pixel cat preview."""
    # background — warm sage green
    surface.fill((195, 225, 175))

    # soft vignette / gradient overlay
    for i in range(6):
        alpha = 30 - i * 4
        ring  = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(ring, (160, 200, 140, alpha),
                         (i * 15, i * 15, SCREEN_W - i * 30, SCREEN_H - i * 30))
        surface.blit(ring, (0, 0))

    # floating petals / orbs
    for petal in _start_petals:
        oy  = petal["y"] + math.sin(tick * 0.008 * petal["speed"] + petal["phase"]) * 20
        ox  = petal["x"] + math.cos(tick * 0.005 * petal["speed"] + petal["phase"]) * 8
        r   = petal["r"]
        col = petal["col"]
        pygame.draw.circle(surface, col, (int(ox), int(oy)), r)
        # inner highlight
        pygame.draw.circle(surface, (255, 255, 255), (int(ox) - r // 4, int(oy) - r // 4), r // 3)

    cx = SCREEN_W // 2
    f_huge  = pygame.font.SysFont("Georgia", 52, bold=True)
    f_big   = pygame.font.SysFont("Georgia", 26, bold=True)
    f_med   = pygame.font.SysFont("Georgia", 17)
    f_small = pygame.font.SysFont("Georgia", 14)

    # title card — creamy panel behind text
    title_rect = pygame.Rect(cx - 220, 60, 440, 110)
    pygame.draw.rect(surface, CREAM, title_rect, border_radius=16)
    pygame.draw.rect(surface, PANEL_BORDER, title_rect, 3, border_radius=16)

    t1_y = 70  + int(math.sin(tick * 0.04) * 2)
    t2_y = 120 + int(math.sin(tick * 0.04 + 0.9) * 2)
    t1 = f_huge.render("Cozy Garden", True, WARM_BROWN)
    t2 = f_big.render("Adventure  🌿", True, DARK_GREEN)
    surface.blit(t1, (cx - t1.get_width() // 2, t1_y))
    surface.blit(t2, (cx - t2.get_width() // 2, t2_y))

    # little vine divider
    pygame.draw.line(surface, PANEL_BORDER, (cx - 180, 188), (cx + 180, 188), 2)
    for lx in range(cx - 178, cx + 178, 18):
        pygame.draw.circle(surface, WARM_GREEN, (lx, 188), 3)

    # instructions
    instrs = [
        ("Collect all the strawberries before the gatitos find you!", MUTED_BROWN),
        ("3 cozy gardens — each a little more winding!",              DARK_GREEN),
        ("You have 3 lives. Touched by a gatito = ouch!",            BERRY_RED),
    ]
    for i, (line, col) in enumerate(instrs):
        s = f_med.render(line, True, col)
        surface.blit(s, (cx - s.get_width() // 2, 200 + i * 24))

    # sprite preview row
    preview_y = 310
    items = [("You (cat)", "player"), ("Berry", "berry"), ("Gatito", "gatito"), ("Hedge", "hedge")]
    total_w = len(items) * 115
    sx = cx - total_w // 2 + 30

    preview_bg = pygame.Rect(cx - total_w // 2 - 10, preview_y - 30, total_w + 20, 90)
    pygame.draw.rect(surface, CREAM, preview_bg, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, preview_bg, 2, border_radius=12)

    for label, kind in items:
        pcx, pcy = sx, preview_y + 4
        preview_size = 44  # same size used in-game

        if kind == "player":
            # use the real cat sprite if loaded, else fallback circle
            spr = _SPRITE_CACHE.get("cat_closed")
            if spr:
                mini = pygame.transform.scale(spr, (preview_size, preview_size))
                surface.blit(mini, (pcx - preview_size // 2, pcy - preview_size // 2))
            else:
                pygame.draw.circle(surface, CREAM, (pcx, pcy), 18)
        elif kind == "berry":
            pygame.draw.circle(surface, BERRY_RED,   (pcx, pcy + 3), 10)
            pygame.draw.circle(surface, BERRY_DARK,  (pcx, pcy + 3), 10, 2)
            pygame.draw.circle(surface, BERRY_SHINE, (pcx - 3, pcy), 3)
            pygame.draw.line(surface, BERRY_LEAF, (pcx, pcy - 8), (pcx, pcy - 13), 2)
        elif kind == "gatito":
            spr = _SPRITE_CACHE.get("gatito")
            if spr:
                mini = pygame.transform.scale(spr, (preview_size, preview_size))
                surface.blit(mini, (pcx - preview_size // 2, pcy - preview_size // 2))
            else:
                pygame.draw.circle(surface, LAVENDER, (pcx, pcy), 16)
        elif kind == "hedge":
            pygame.draw.rect(surface, HEDGE_GREEN, (pcx - 14, pcy - 14, 28, 28), border_radius=4)
            pygame.draw.circle(surface, HEDGE_LIGHT, (pcx - 5, pcy - 5), 8)
            pygame.draw.circle(surface, HEDGE_LIGHT, (pcx + 6, pcy - 3), 7)
            pygame.draw.rect(surface, HEDGE_DARK, (pcx - 14, pcy - 14, 28, 28), 2, border_radius=4)

        lbl = f_small.render(label, True, MUTED_BROWN)
        surface.blit(lbl, (pcx - lbl.get_width() // 2, preview_y + 26))
        sx += 115

    # pulsing START button
    pulse = 1.0 + 0.04 * math.sin(tick * 0.08)
    btn_w = int(240 * pulse)
    btn_h = int(56  * pulse)
    btn_rect = pygame.Rect(cx - btn_w // 2, 415, btn_w, btn_h)
    hovered  = btn_rect.collidepoint(mouse_pos)
    draw_cozy_button(surface, btn_rect, "▶  Start Adventure", f_big, hovered)

    hint = f_small.render("Click or press Enter to begin", True, MUTED_BROWN)
    surface.blit(hint, (cx - hint.get_width() // 2, 484))

    return btn_rect

# ──────────────────────────────────────────────
#  COUNTDOWN SCREEN
# ──────────────────────────────────────────────

def draw_countdown_screen(surface, count_val, tick, level_index):
    surface.fill((215, 235, 195))  # warm sage

    f_huge = pygame.font.SysFont("Georgia", 160, bold=True)
    f_big  = pygame.font.SysFont("Georgia", 32,  bold=True)
    f_med  = pygame.font.SysFont("Georgia", 22)
    cx, cy = SCREEN_W // 2, SCREEN_H // 2

    # soft cream card
    card = pygame.Rect(cx - 150, cy - 130, 300, 260)
    pygame.draw.rect(surface, CREAM, card, border_radius=20)
    pygame.draw.rect(surface, PANEL_BORDER, card, 3, border_radius=20)

    pulse = 1.0 + 0.3 * (1.0 - min(1.0, (tick % 60) / 30))

    if count_val > 0:
        text   = str(count_val)
        colour = [WARM_BROWN, DARK_GREEN, BERRY_RED][count_val - 1]
    else:
        text   = "Go!"
        colour = WARM_GREEN

    rendered = f_huge.render(text, True, colour)
    scaled   = pygame.transform.scale(
        rendered,
        (int(rendered.get_width() * pulse), int(rendered.get_height() * pulse))
    )
    surface.blit(scaled, (cx - scaled.get_width() // 2, cy - scaled.get_height() // 2 - 20))

    garden_names = ["The Meadow", "The Orchard", "The Spiral Garden"]
    name = garden_names[level_index] if level_index < len(garden_names) else f"Garden {level_index+1}"
    msg = f_med.render(f"{name}  —  Get ready!", True, MUTED_BROWN)
    surface.blit(msg, (cx - msg.get_width() // 2, cy + 115))

# ──────────────────────────────────────────────
#  LEVEL-COMPLETE SCREEN
# ──────────────────────────────────────────────

def draw_level_complete_screen(surface, level_index, particles):
    surface.fill((200, 230, 180))

    f_huge = pygame.font.SysFont("Georgia", 72, bold=True)
    f_big  = pygame.font.SysFont("Georgia", 30, bold=True)
    f_med  = pygame.font.SysFont("Georgia", 20)
    cx     = SCREEN_W // 2

    card = pygame.Rect(cx - 260, 100, 520, 260)
    pygame.draw.rect(surface, CREAM, card, border_radius=20)
    pygame.draw.rect(surface, PANEL_BORDER, card, 3, border_radius=20)

    title = f_huge.render(f"Garden {level_index} Clear!", True, WARM_BROWN)
    surface.blit(title, (cx - title.get_width() // 2, 128))

    sub = f_big.render(f"Next up: Garden {level_index + 1}...", True, DARK_GREEN)
    surface.blit(sub, (cx - sub.get_width() // 2, 218))

    hint = f_med.render("(Starting soon)", True, MUTED_BROWN)
    surface.blit(hint, (cx - hint.get_width() // 2, 268))

    update_and_draw_particles(surface, particles)

# ──────────────────────────────────────────────
#  GAME SCREEN
# ──────────────────────────────────────────────

def draw_game_screen(surface, state):
    lv        = state["level"]
    level_map = lv["level_map"]
    tick      = lv["anim_tick"]

    # draw all tiles
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if level_map[row][col] == 0:
                draw_tile_bg(surface, col, row, tick)
            else:
                draw_hedge(surface, col, row)

    # draw path stones only on tiles adjacent to hedges (looks natural)
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if level_map[row][col] == 0:
                # check if any neighbour is a wall
                neighbours = [(col-1,row),(col+1,row),(col,row-1),(col,row+1)]
                near_wall  = any(
                    0 <= nc < GRID_COLS and 0 <= nr < GRID_ROWS and level_map[nr][nc] == 1
                    for nc, nr in neighbours
                )
                if near_wall:
                    draw_stone_path(surface, col, row)

    # decorative flowers/mushrooms on open tiles
    draw_tile_decorations(surface, level_map, tick)

    # berries (collectibles)
    for cc, cr in lv["coins"]:
        draw_strawberry(surface, cc, cr, tick)

    # enemies (cute gatitos)
    for enemy in lv["enemies"]:
        draw_gatito(surface, enemy["col"], enemy["row"], tick)

    # player — blink when invincible
    if lv["invincible"] == 0 or (lv["invincible"] // 5) % 2 == 0:
        draw_player(surface, lv["player_col"], lv["player_row"], tick, lv["is_moving"])

    # particles
    update_and_draw_particles(surface, lv["particles"])

    # side panel
    draw_panel(surface, state["score"], int(state["elapsed_time"]),
               state["lives"], state["level_index"] + 1, len(lv["coins"]),
               paused=(state["scene"] == "paused"))


def draw_pause_overlay(surface):
    overlay = pygame.Surface((MAP_WIDTH, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((200, 220, 180, 140))
    surface.blit(overlay, (0, 0))

    f_huge = pygame.font.SysFont("Georgia", 72, bold=True)
    f_med  = pygame.font.SysFont("Georgia", 22)
    cx     = MAP_WIDTH // 2

    card = pygame.Rect(cx - 160, SCREEN_H // 2 - 80, 320, 160)
    pygame.draw.rect(surface, CREAM, card, border_radius=16)
    pygame.draw.rect(surface, PANEL_BORDER, card, 3, border_radius=16)

    txt = f_huge.render("Paused ~", True, WARM_BROWN)
    surface.blit(txt, (cx - txt.get_width() // 2, SCREEN_H // 2 - 65))
    hint = f_med.render("Press P to resume", True, MUTED_BROWN)
    surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_H // 2 + 40))

# ──────────────────────────────────────────────
#  WIN SCREEN
# ──────────────────────────────────────────────

def draw_win_screen(surface, state, mouse_pos):
    surface.fill((195, 230, 175))

    update_and_draw_confetti(surface, state["confetti"])

    f_huge = pygame.font.SysFont("Georgia", 66, bold=True)
    f_big  = pygame.font.SysFont("Georgia", 28, bold=True)
    f_med  = pygame.font.SysFont("Georgia", 20)
    cx, cy = SCREEN_W // 2, 60

    card = pygame.Rect(cx - 270, cy, 540, 380)
    pygame.draw.rect(surface, CREAM, card, border_radius=20)
    pygame.draw.rect(surface, PANEL_BORDER, card, 3, border_radius=20)
    cy += 20

    title = f_huge.render("You did it! 🌸", True, WARM_BROWN)
    surface.blit(title, (cx - title.get_width() // 2, cy)); cy += 78

    sc = f_big.render(f"Score:  {state['score']}", True, ORANGE_WARM)
    surface.blit(sc, (cx - sc.get_width() // 2, cy)); cy += 44

    t = int(state["elapsed_time"])
    mins, secs = t // 60, t % 60
    tm = f_big.render(f"Time:  {mins:02d}:{secs:02d}", True, DARK_GREEN)
    surface.blit(tm, (cx - tm.get_width() // 2, cy)); cy += 46

    if t <= FAST_TIME_LIMIT:
        star_count, msg = 3, "Blazing fast! Perfect cozy run!"
    elif t <= MEDIUM_TIME_LIMIT:
        star_count, msg = 2, "Lovely work! Keep practising!"
    else:
        star_count, msg = 1, "You made it! Try for a faster time!"

    for i in range(3):
        draw_star(surface, cx - 55 + i * 55, cy + 4, 22, filled=(i < star_count))
    cy += 62

    msg_s = f_med.render(msg, True, MUTED_BROWN)
    surface.blit(msg_s, (cx - msg_s.get_width() // 2, cy)); cy += 40

    btn_rect = pygame.Rect(cx - 130, cy, 260, 52)
    draw_cozy_button(surface, btn_rect, "▶  Play Again", f_big, btn_rect.collidepoint(mouse_pos))

    return btn_rect

# ──────────────────────────────────────────────
#  GAME OVER SCREEN
# ──────────────────────────────────────────────

def draw_gameover_screen(surface, state, mouse_pos):
    surface.fill((220, 190, 190))  # soft dusty pink instead of dark red

    f_huge = pygame.font.SysFont("Georgia", 72, bold=True)
    f_big  = pygame.font.SysFont("Georgia", 28, bold=True)
    f_med  = pygame.font.SysFont("Georgia", 19)
    cx     = SCREEN_W // 2

    card = pygame.Rect(cx - 260, 80, 520, 350)
    pygame.draw.rect(surface, CREAM, card, border_radius=20)
    pygame.draw.rect(surface, DUSTY_ROSE, card, 3, border_radius=20)

    title = f_huge.render("Oh no! 😿", True, DUSTY_ROSE)
    surface.blit(title, (cx - title.get_width() // 2, 104))

    sc = f_big.render(f"Final score:  {state['score']}", True, WARM_BROWN)
    surface.blit(sc, (cx - sc.get_width() // 2, 198))

    t = int(state["elapsed_time"])
    tm = f_med.render(f"Time survived:  {t // 60:02d}:{t % 60:02d}", True, MUTED_BROWN)
    surface.blit(tm, (cx - tm.get_width() // 2, 248))

    tip = f_med.render("Tip: gatitos move slowest in Garden 1!", True, MUTED_BROWN)
    surface.blit(tip, (cx - tip.get_width() // 2, 290))

    btn_rect = pygame.Rect(cx - 130, 350, 260, 52)
    hov = btn_rect.collidepoint(mouse_pos)
    col = BUTTON_RED_H if hov else BUTTON_RED
    shadow = btn_rect.move(3, 3)
    pygame.draw.rect(surface, DUSTY_ROSE, shadow, border_radius=12)
    pygame.draw.rect(surface, col,   btn_rect, border_radius=12)
    pygame.draw.rect(surface, WHITE, btn_rect, 2, border_radius=12)
    lbl = f_big.render("↩  Try Again", True, WHITE)
    surface.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2,
                       btn_rect.centery - lbl.get_height() // 2))
    return btn_rect

# ──────────────────────────────────────────────
#  LEVEL ADVANCE (unchanged)
# ──────────────────────────────────────────────

def advance_level(state):
    state["level_index"] += 1
    if state["level_index"] >= MAX_LEVELS:
        play_sfx(SFX_FINAL_WIN)
        state["scene"] = "win"
        spawn_confetti_burst(state["confetti"], n=200)
    else:
        play_sfx(SFX_LEVEL_WIN)
        state["scene"]             = "level_complete"
        state["celebration_timer"] = FPS * 2
        state["celebration_particles"] = []
        for _ in range(6):
            pcx = random.randint(100, SCREEN_W - 100)
            pcy = random.randint(50,  SCREEN_H - 100)
            for _ in range(15):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                state["celebration_particles"].append({
                    "x": float(pcx), "y": float(pcy),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - 1,
                    "life": random.randint(40, 80), "max_life": 80,
                    "colour": random.choice([SOFT_PINK, BERRY_SHINE, SOFT_GOLD, LAVENDER, WHITE]),
                    "size": random.randint(4, 9),
                })
        state["level"] = init_level(state["level_index"])

# ──────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────

def main():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Cozy Garden Adventure")
    load_all_sprites()   # load real cat + gatito images now that display exists
    clock  = pygame.time.Clock()

    state            = init_game()
    countdown_frame  = 0
    countdown_number = 3
    global_tick      = 0

    running = True
    while running:
        clock.tick(FPS)
        global_tick += 1
        mouse_pos = pygame.mouse.get_pos()

        # ── EVENTS ──────────────────────────────────
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

                if event.key == pygame.K_RETURN and state["scene"] == "start":
                    play_sfx(SFX_GO)
                    state["scene"]   = "countdown"
                    countdown_frame  = 0
                    countdown_number = 3

                if state["scene"] == "playing":
                    if event.key == pygame.K_UP:     try_move(state, 0,  -1)
                    elif event.key == pygame.K_DOWN:  try_move(state, 0,   1)
                    elif event.key == pygame.K_LEFT:  try_move(state, -1,  0)
                    elif event.key == pygame.K_RIGHT: try_move(state,  1,  0)

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

        # ── SCENE UPDATES ────────────────────────────

        if state["scene"] == "countdown":
            countdown_frame += 1
            if countdown_frame >= FPS:
                countdown_frame = 0
                countdown_number -= 1
                if countdown_number < 0:
                    state["scene"] = "playing"
                    if state["start_time"] is None:
                        state["start_time"] = time.time()
                    countdown_number = 3

        elif state["scene"] == "level_complete":
            state["celebration_timer"] -= 1
            if state["celebration_timer"] <= 0:
                state["scene"]   = "countdown"
                countdown_frame  = 0
                countdown_number = 3

        elif state["scene"] == "playing":
            lv = state["level"]
            state["elapsed_time"] = time.time() - state["start_time"]
            lv["anim_tick"] += 1

            # reset is_moving each frame — only stays True in the frame a move happened
            lv["is_moving"] = False

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
                spawn_berry_particles(lv["particles"], lv["player_col"], lv["player_row"])

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

        # ── DRAWING ──────────────────────────────────
        screen.fill(SOFT_GREEN)   # fallback bg (mostly hidden)

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
