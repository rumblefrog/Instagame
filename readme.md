# Mouse Script for Instagram Emoji Pong Game

This Python script can automatically play the Instagram mini-game "Emoji Pong" on a PC using software that can project your phone to the PC. 

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
1. Clone the repository
2. Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
```json
{
    "window_title": "RMX",
    "window_width": 436,
    "window_height": 974
}
```

## Usage
1. Ensure your phone screen is being projected to your PC using scrcpy.
2. Run the script:
