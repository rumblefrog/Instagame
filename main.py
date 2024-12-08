import pygetwindow as gw
from pygetwindow import Win32Window
import mouse
from mouse import LEFT
import keyboard as kb
import time
import mss
import numpy as np
import math
import ctypes
import threading
import sys
import json
from collections import deque

que = deque()

with open('config.json') as file:
    config = json.load(file)

window_title = config['window_title']
window_width = config['window_width']
window_height = config['window_height']

ball_width = 40
platform_height = 65


left_boundary = 19
right_boundary = window_width - 19
top_boundary = 54
bottom_boundary = window_height - 90

HWND_TOP = 0
SWP_NOSENDCHANGING = 0x0400

# Set window position
def set_window_pos(window_handle, x, y, width, height):
    ret = ctypes.windll.user32.SetWindowPos(
        window_handle,
        HWND_TOP,
        x,
        y,
        width,
        height,
        SWP_NOSENDCHANGING
    )
    return ret

def init():
    all_windows = gw.getAllWindows()
    for w in all_windows:
        if window_title in w.title:
            break
    
    if window_title not in w.title:
        print('No Instagram window found')
        return None
    

    window = Win32Window(w._hWnd)
    window.activate()

    print(window.size)
    time.sleep(0.2)

    mouse.move(
        x=window.topleft.x + window_width // 2,
        y=window.topleft.y + window_height - 65,
    )
    mouse.press(LEFT)
    time.sleep(0.2)
    mouse.release(LEFT)

    time.sleep(0.2)

    mouse.press(LEFT)


    return window

def rgb_ansi_text(text, r, g, b):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def get_screenshot(window):
    while True:
        if kb.is_pressed('space'):
            return

        region = {
            "top": window.topleft.y,
            "left": window.topleft.x,
            "width": window_width,
            "height": window_height
        }

        with mss.mss() as sct:
            screenshot = sct.grab(region)
            screenshot = np.array(screenshot)[:, :, :3]

        que.appendleft(screenshot)

# Calculate the reflected point of the ball
# From reflected coordinate to original coordinate
def forward_wall(walls, x, y):
    for wall in walls:
        if wall == 'L':
            x = 2 * left_boundary - x
        elif wall == 'R':
            x = 2 * right_boundary - x
        elif wall == 'T':
            y = 2 * top_boundary - y
    return x, y
# From original coordinate to reflected coordinate
def reverse_wall(walls, x, y):
    for wall in walls[::-1]:
        if wall == 'L':
            x = 2 * left_boundary - x
        elif wall == 'R':
            x = 2 * right_boundary - x
        elif wall == 'T':
            y = 2 * top_boundary - y
    return x, y

def predict(window):
    prev_dir = 'up'
    prev = [float('inf'), float('inf')]
    sequence = []
    reflected = []
    walls = []
    prev_reflected = []
    prev_prev_reflected = []
    prev_time = time.time()

    target = np.array([255, 83, 53])
    target = np.array([53, 83, 255])

    times = []

    # Main loop
    while True:
        if kb.is_pressed('space'):
            return
        
        if len(que) == 0:
            time.sleep(0.005)
            continue
        else:
            screenshot = que.pop()

        # Get the coordinates of the ball
        diff = screenshot - target
        squared_diff = np.sum(diff ** 2, axis=-1)
        mask = squared_diff < 20

        image_y, image_x = np.where(mask)

        if len(image_x) < 50 or len(image_y) < 50:
            # print('No ball found')
            continue

        image_x.sort()
        image_y.sort()

        image_x = image_x[2:-2]
        image_y = image_y[2:-2]

        x_max = image_x[-1]
        x_min = image_x[0]
        y_max = image_y[-1]
        y_min = image_y[0]

        if x_max - x_min > 42 or y_max - y_min > 42 or x_max - x_min < 30 or y_max - y_min < 30:
            continue

        if len(image_x) > 0 and len(image_y) > 0:
            ball_x = (x_max + x_min) // 2
            ball_y = (y_max + y_min) // 2
        else:
            ball_x, ball_y = [window_width // 2, window_height // 2]

        if abs(ball_x - prev[0]) < 5 and abs(ball_y - prev[1]) < 5:
            continue


        # Calculate the reflected coordinate of the ball
        if ball_y > prev[1] or (ball_y == prev[1] and prev_dir == 'up'):
            prev_dir = 'down'
        else:
            if prev_dir == 'down':
                # print()
                x = reflected[-1][0]
                while x < left_boundary or x > right_boundary:
                    if x < left_boundary:
                        x = 2 * left_boundary - x
                    elif x > right_boundary:
                        x = 2 * right_boundary - x
                y = reflected[-1][1]
                y = 2 * top_boundary - y
                y = 2 * bottom_boundary - y
                offset = [x - reflected[-1][0], y - reflected[-1][1]]
                prev_prev_reflected = [[x + offset[0], y + offset[1]] for x, y in (prev_reflected + reflected)[:-1]]
                prev_reflected = [[x + offset[0], y + offset[1]] for x, y in (reflected)[:-1]]
                if len(prev_reflected) > 100:
                    prev_reflected = prev_reflected[-50:]
                if len(prev_prev_reflected) > 100:
                    prev_prev_reflected = prev_prev_reflected[-50:]
                sequence = []
                reflected = []
                walls = []
            prev_dir = 'up'
        
        sequence.append([ball_x, ball_y])

        if len(sequence) > 3:
            if m != 0:
                reflected_y = sequence[-1][1] if 'T' not in walls else 2 * top_boundary - sequence[-1][1]
                predicted_x = m * (reflected_y) + b

                predicted_x, _ = forward_wall(walls, predicted_x, 0)
                # print(predicted_x)
                if predicted_x < left_boundary and sequence[-1][0] - predicted_x > ball_width:
                   walls.append('L')
                if predicted_x > right_boundary and predicted_x - sequence[-1][0] > ball_width:
                    walls.append('R')

            if sequence[-3][0] > sequence[-2][0] and sequence[-2][0] <= sequence[-1][0]:
                walls.append('L')
            if sequence[-3][0] < sequence[-2][0] and sequence[-2][0] >= sequence[-1][0]:
                walls.append('R')
            
            if len(walls) > 1 and walls[-1] == walls[-2]:
                walls.pop()

            if m != 0:
                reflected_x, _ = reverse_wall(walls, sequence[-1][0], 0)
                predicted_y = (reflected_x - b) / m

                if predicted_y < top_boundary:
                    if 'T' not in walls:
                        walls.append('T')
            
            if sequence[-3][1] > sequence[-2][1] and sequence[-2][1] <= sequence[-1][1]:
                if 'T' not in walls:
                    walls.append('T')
            
            if len(walls) > 1 and walls[-1] == walls[-2]:
                walls.pop()
            
            reflected_x, reflected_y = reverse_wall(walls, sequence[-1][0], sequence[-1][1])
            reflected.append([reflected_x, reflected_y])
        else:
            reflected.append([ball_x, ball_y])

        prev = [ball_x, ball_y]

        
        # Predict the next position of the ball using linear regression
        if len(reflected) > 2:
            if len(prev_reflected) > 2:
                if reflected[-1][0] > reflected[0][0] and prev_reflected[-1][0] < prev_reflected[0][0]:
                    prev_reflected = [[2 * reflected[0][0] - x, y] for x, y in prev_reflected]
                    prev_prev_reflected = [[2 * reflected[0][0] - x, y] for x, y in prev_prev_reflected]
                elif reflected[-1][0] < reflected[0][0] and prev_reflected[-1][0] > prev_reflected[0][0]:
                    prev_reflected = [[2 * reflected[0][0] - x, y] for x, y in prev_reflected]
                    prev_prev_reflected = [[2 * reflected[0][0] - x, y] for x, y in prev_prev_reflected]
            
                X = np.array([y for _, y in (prev_reflected + reflected)])
                y = np.array([x for x, _ in (prev_reflected + reflected)])
            else:
                X = np.array([y for _, y in (reflected)])
                y = np.array([x for x, _ in (reflected)])

            m, b = np.polyfit(X, y, 1)

            predicted_x = m * (2 * top_boundary - bottom_boundary) + b


            while predicted_x < left_boundary or predicted_x > right_boundary:
                if predicted_x < left_boundary:
                    predicted_x = 2 * left_boundary - predicted_x
                elif predicted_x > right_boundary:
                    predicted_x = 2 * right_boundary - predicted_x

            predicted_x = max(left_boundary, min(right_boundary, predicted_x))

            x = window.topleft.x + predicted_x
            y = window.topleft.y + window_height // 2
            x = min(max(x, window.topleft.x), window.topleft.x + window_width)

            if not math.isnan(x):
                mouse.move(x, y, absolute=True)
        else:
            m, b = 0, 0

        # Output the information
        line = ''

        col = 150
        for j in range(col):
            x = window_width * j // col
            y = ball_y
            if x < x_min or x > x_max:
                color1 = screenshot[window_height * 3 // 4, window_width * 1 // 4]
                color2 = screenshot[window_height * 3 // 4, window_width * 2 // 4]
                color3 = screenshot[window_height * 3 // 4, window_width * 3 // 4]

                mid_b = sorted((color1[0], color2[0], color3[0]))[1]
                mid_g = sorted((color1[1], color2[1], color3[1]))[1]
                mid_r = sorted((color1[2], color2[2], color3[2]))[1]

                color = [mid_b, mid_g, mid_r]
            else:
                color = target
            color = [color[2], color[1], color[0]]
            line += rgb_ansi_text('█', *color)


        times.append(time.time() - prev_time)
        prev_time = time.time()
        if len(times) > 60:
            times.pop(0)

        print(line, end = ' ')
        print("(%3d, %3d)" % (ball_x, ball_y), end = ' ')
        print(f'fps: {round(len(times) / sum(times))}', end = ' ')
        print(f'walls: {', '.join(wall for wall in walls)}', end = ' ')
        print()
        sys.stdout.flush()


def main(window):
    # Create producer and consumer threads
    producer_thread = threading.Thread(target=lambda: get_screenshot(window))
    consumer_thread = threading.Thread(target=lambda: predict(window))

    # Start the threads
    producer_thread.start()
    consumer_thread.start()

    # Wait for the threads to finish
    producer_thread.join()
    consumer_thread.join()

    mouse.release(LEFT)


if __name__ == "__main__":
    window = init()
    if window is not None:
        main(window)