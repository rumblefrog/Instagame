# Python Script for Instagram Emoji Pong Game

This Python script can automatically play the Instagram mini-game "Emoji Pong" on a PC using [scrcpy](https://github.com/Genymobile/scrcpy), a software that project your phone to the PC.

> [!IMPORTANT]  
> It only works on `Windows` PC and `Android` phone. No other combination works. `Scrcpy` is for `Android`, and this script uses Windows API to get the information of the projected window.
## Dependencies

The required Python packages are listed in the `requirements.txt` file:

```txt
keyboard==0.13.5
mouse==0.7.1
mss==10.0.0
numpy==2.1.3
PyGetWindow==0.0.9
```

## Installation
1. Install [scrcpy](https://github.com/Genymobile/scrcpy)
1. Clone the repository
2. Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Ensure the `config.json` file is correctly set up. Here is an example configuration:

```json
{
    "window_title": "RMX",
    "window_width": 436,
    "window_height": 974
}
```
Replace the `window_title` field with the title of `scrcpy` window and set the width and hieght of the window.


## Usage
1. Ensure your phone screen is being projected to your PC using `scrcpy`.
2. Start a game using the red circle(🔴) emoji and die. Now there should be a `Play Again` button at the bottom.
3. Run the script:
```bash
Python main.py
```
>[!IMPORTANT]  
> **DO NOT** move your mouse or press any key key on your keyboard after you run the Python script. It should automatically play the game for you.
   
## How does it work?
### Screenshots
The script continuously captures screenshots and analyzes their colors to determine the ball's position. A higher frame rate provides more data, which enhances the accuracy of the calculations and leads to better scores. However, capturing a screenshot takes significantly longer than the subsequent calculations and is the script's bottleneck. Depending on your hardware, the script can capture around 40 to 50 screenshots per second. On average, it can get to 100 points, and it once got 150. After that, the ball is too fast that the script only has less than 10 frames to predict the next position, which is definitely not enough and it eventually dies.
### Linear Regression
Taking reflections into account, the ball's path can be modeled as a straight line. However, due to resolution and other factors, the positions obtained from the screenshots do not align perfectly along a straight line. To address this, the script applies linear regression to fit a straight line to the path and predict the position where the ball will hit the platform.