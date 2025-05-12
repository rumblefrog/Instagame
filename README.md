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

## Scrpy example
Window DPI scaling, resolution can make it inaccurate. I downscaled it to work on 1920x1080 @ 100% scale.

```
scrcpy.exe --no-audio --window-width=436 --window-height=940 --window-borderless
```

## Usage
1. Ensure your phone screen is being projected to your PC using `scrcpy`.
2. Start a game using the red circle(🔴) emoji and die. Now there should be a `Play Again` button at the bottom.
3. Run the script:
```bash
Python main.py
```
>[!IMPORTANT]  
> **DO NOT** move your mouse or press any key key on your keyboard after you run the Python script. It should automatically play the game for you.
