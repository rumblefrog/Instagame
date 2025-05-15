"""
bot_stable.py – no-twitch Instagram brick-breaker bot
  • median-of-5 landing predictor
  • 35 px freeze zone near paddle
  • small constant lead (12 ms)
  press <Space> to stop
"""

import time, json, threading, sys
from collections import deque
import numpy as np
import cv2, mss, mouse, keyboard as kb, pygetwindow as gw
from pygetwindow import Win32Window

# ────────── user knobs ────────── #
with open("config.json") as f:
    CFG = json.load(f)

WIN_W, WIN_H = CFG["window_width"], CFG["window_height"]
TITLE        = CFG["window_title"]

LEFT, RIGHT  = 19, WIN_W - 19
TOP          = 54
PADDLE_LINE  = WIN_H - 70              # paddle centre y
PADDLE_W     = 90                      # paddle width (px)
BALL_R       = 20                      # ball radius (px)

LEAD_SEC     = 0.012                  # 12 ms; set 0 for no lead
FREEZE_DIST  = 35                     # stop updating when ball < 35 px above paddle
PRED_BUF     = 5                      # median over last N predicted hit X’s
# ───────────────────────────────── #

frames = deque(maxlen=2)              # screenshot queue
hits   = deque(maxlen=PRED_BUF)       # recent predicted hit_x

kernel  = np.ones((5, 5), np.uint8)
FIELD_W = RIGHT - LEFT

def game_window() -> Win32Window:
    for w in gw.getAllWindows():
        if TITLE in w.title:
            Win32Window(w._hWnd).activate()
            return Win32Window(w._hWnd)
    sys.exit("❌  Game window not found")

def reflect_x(x: float) -> float:
    """Elastic reflection inside LEFT–RIGHT."""
    d = x - LEFT
    mod = d % (2 * FIELD_W)
    return LEFT + (2 * FIELD_W - mod if mod > FIELD_W else mod)

def detect_ball(img):
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = (cv2.inRange(hsv,(0,120,120),(10,255,255)) |
            cv2.inRange(hsv,(170,120,120),(180,255,255)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    (x,y),_ = cv2.minEnclosingCircle(max(cnts, key=cv2.contourArea))
    return float(x), float(y)

def capture(win):
    region = {"left":win.topleft.x, "top":win.topleft.y,
              "width":WIN_W, "height":WIN_H}
    with mss.mss() as sct:
        while not kb.is_pressed("space"):
            frames.appendleft(np.array(sct.grab(region))[:,:,:3])

def play(win):
    prev = None
    while not kb.is_pressed("space"):

        if not frames:
            time.sleep(0.002); continue
        img = frames.pop()
        ball = detect_ball(img)
        if not ball: continue
        bx, by = ball

        # ------------- velocity -------------
        if prev is None:
            prev = np.array([bx, by]); continue
        vx, vy = np.array([bx, by]) - prev
        prev   = np.array([bx, by])
        if abs(vx)+abs(vy) < 1:       # ignore static frames
            continue

        # vertical distance still to travel
        dy = (PADDLE_LINE - by) if vy > 0 else (by - TOP) + (PADDLE_LINE - TOP)
        if vy == 0: continue

        # arrival time and constant lead
        t_hit = dy / abs(vy)
        lead  = vx * LEAD_SEC

        # analytic landing x
        hit_x = reflect_x(bx + vx * t_hit + lead)

        # median-of-5 smoothing
        hits.append(hit_x)
        if len(hits) < PRED_BUF:
            continue                  # warm-up
        smooth_x = float(np.median(hits))

        # freeze when ball is close
        if PADDLE_LINE - by < FREEZE_DIST:
            target_x = smooth_x       # but stop updating buffer further
            hits.clear()
        else:
            target_x = smooth_x

        # paddle left-edge coordinate
        paddle_left = int(target_x - PADDLE_W/2)
        paddle_left = max(LEFT, min(RIGHT-PADDLE_W, paddle_left))

        # ensure click held
        if not mouse.is_pressed('left'):
            mouse.press('left')

        # move cursor once (no dead-zone needed, jitter already filtered)
        mouse.move(win.topleft.x + paddle_left + PADDLE_W//2,
                   win.topleft.y + WIN_H//2,
                   absolute=True)

def main():
    win = game_window()

    # one click to start & hold paddle
    mouse.move(win.topleft.x+WIN_W//2, win.topleft.y+WIN_H-65)
    mouse.click(); mouse.press('left')

    threading.Thread(target=capture, args=(win,), daemon=True).start()
    threading.Thread(target=play,    args=(win,), daemon=True).start()

    while not kb.is_pressed("space"):
        time.sleep(0.1)

    mouse.release('left')

if __name__ == "__main__":
    main()
