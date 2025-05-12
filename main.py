"""
bot_min.py  –  simplest reliable Instagram brick‑breaker bot
  • holds left‑click continuously
  • pure analytic path solver (handles any number of side bounces)
  • constant‑latency lead (default 25 ms)

Requirements: opencv‑python mss numpy mouse keyboard pygetwindow
"""

import time, json, threading, sys, ctypes, math
from collections import deque
import numpy as np
import cv2, mss, mouse, keyboard as kb, pygetwindow as gw
from pygetwindow import Win32Window

# ─────────── config ─────────── #
with open("config.json") as f:
    CFG = json.load(f)

WIN_W, WIN_H   = CFG["window_width"], CFG["window_height"]
TITLE          = CFG["window_title"]

LEFT, RIGHT    = 19, WIN_W - 19
TOP            = 54
PADDLE_LINE    = WIN_H - 90 - 65          # centre of paddle
PADDLE_WIDTH   = 90                      # measure once, tweak here
BALL_R         = 20                       # px radius

# HSV thresholds for the red ball (two ranges because hue wraps)
HSV1_LO, HSV1_HI = (  0,120,120), (10,255,255)
HSV2_LO, HSV2_HI = (170,120,120), (180,255,255)

LATENCY_SEC    = 0.025                    # 25 ms lead; adjust for your PC
# ─────────────────────────────── #

frames = deque(maxlen=2)

# ——— window helpers ——— #
def get_game_window() -> Win32Window:
    for w in gw.getAllWindows():
        if TITLE in w.title:
            Win32Window(w._hWnd).activate()
            return Win32Window(w._hWnd)
    sys.exit("❌  Window not found – check TITLE in config.json")

# ——— vision helpers ——— #
kernel5 = np.ones((5,5), np.uint8)
def detect_ball(img):
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV1_LO, HSV1_HI) | cv2.inRange(hsv, HSV2_LO, HSV2_HI)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel5)
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    (x,y),_ = cv2.minEnclosingCircle(max(cnts, key=cv2.contourArea))
    return float(x), float(y)

# ——— maths ——— #
FIELD_W = RIGHT - LEFT
def reflect_x(x):
    """Mirror x into [LEFT,RIGHT] with elastic side‑walls."""
    d   = x - LEFT
    mod = d % (2*FIELD_W)
    return LEFT + (2*FIELD_W - mod if mod > FIELD_W else mod)

# ——— threads ——— #
def capture_loop(win):
    region = {"left":win.topleft.x, "top":win.topleft.y,
              "width":WIN_W, "height":WIN_H}
    with mss.mss() as sct:
        while not kb.is_pressed("space"):
            frames.appendleft(np.array(sct.grab(region))[:,:,:3])

def play_loop(win):
    prev = None                      # previous (x,y)
    while not kb.is_pressed("space"):

        if not frames:
            time.sleep(0.002)
            continue
        img  = frames.pop()
        ball = detect_ball(img)
        if not ball:
            continue
        bx, by = ball

        if prev is None:             # need two points to get velocity
            prev = np.array([bx, by])
            continue

        vx, vy = np.array([bx, by]) - prev
        prev   = np.array([bx, by])
        speed  = abs(vx) + abs(vy)
        if speed < 1:                # ignore micro‑movement frames
            continue

        # vertical distance still to travel until paddle centre
        if vy > 0:                   # already descending
            dy_total = PADDLE_LINE - by
        else:                        # still ascending first
            dy_total = (by - TOP) + (PADDLE_LINE - TOP)

        if vy == 0:
            continue                 # shouldn’t happen, but safety first

        # horizontal travel:  Δx = vx * (Δy / |vy|)
        dx = vx * dy_total / abs(vy)

        # add fixed latency lead (25 ms default)
        dx += vx * LATENCY_SEC / (abs(vy) / dy_total)

        raw_hit_x = bx + dx
        hit_x     = reflect_x(raw_hit_x)      # folds all side bounces

        # centre the paddle under hit_x
        paddle_left = int(hit_x - PADDLE_WIDTH / 2)
        paddle_left = max(LEFT, min(RIGHT - PADDLE_WIDTH, paddle_left))

        # guarantee LEFT button is down ☑︎
        if not mouse.is_pressed(button='left'):
            mouse.press()

        mouse.move(
            win.topleft.x + paddle_left + PADDLE_WIDTH // 2,
            win.topleft.y + WIN_H // 2,
            absolute=True,
        )


def main():
    win = get_game_window()

    # click once to start game, then hold paddle
    mouse.move(win.topleft.x+WIN_W//2, win.topleft.y+WIN_H-65)
    mouse.click()
    mouse.press()                          # hold left click entire session

    th_cap = threading.Thread(target=capture_loop, args=(win,), daemon=True)
    th_play= threading.Thread(target=play_loop,   args=(win,), daemon=True)
    th_cap.start(); th_play.start()
    th_cap.join();  th_play.join()

    mouse.release()                        # on exit (space)

if __name__ == "__main__":
    main()
