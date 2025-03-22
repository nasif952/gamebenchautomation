import pydirectinput
import pyautogui
import time
import json
import keyboard
import ctypes
import pygame  # Use pygame for gamepad simulation

# Set DPI awareness
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

# Configure pydirectinput
pydirectinput.PAUSE = 0.005

# Load recorded events
try:
    with open("input_log.json", "r") as f:
        events = json.load(f)
except FileNotFoundError:
    print("Error: input_log.json not found!")
    exit(1)
except json.JSONDecodeError:
    print("Error: input_log.json is corrupted or invalid!")
    exit(1)

# Initialize pygame for gamepad support
pygame.init()
pygame.joystick.init()

# Check for Xbox 360 Controller (XInput Gamepad)
gamepad = None
if pygame.joystick.get_count() > 0:
    gamepad = pygame.joystick.Joystick(0)
    gamepad.init()
    print(f"Found gamepad: {gamepad.get_name()}")
else:
    print("No gamepad detected. Continuing without gamepad support (menu mode only).")

# Get screen resolution
screen_width, screen_height = pyautogui.size()
print(f"Screen resolution: {screen_width}x{screen_height}")
print("Waiting for 'n' to start replay...")

# Wait for 'n' to be pressed
keyboard.wait('n')

# Initial position correction (menu mode only)
first_absolute_event = next((e for e in events if e[0] == "move_absolute"), None)
if first_absolute_event:
    recorded_x, recorded_y = first_absolute_event[1], first_absolute_event[2]
    pydirectinput.moveTo(recorded_x, recorded_y)
    time.sleep(0.5)
    actual_x, actual_y = pyautogui.position()
    correction_x = recorded_x - actual_x
    correction_y = recorded_y - actual_y
    print(f"Initial correction: ({correction_x}, {correction_y})")
    if abs(correction_x) > 5 or abs(correction_y) > 5:
        pydirectinput.moveTo(recorded_x, recorded_y)
        time.sleep(0.2)

print("Replaying inputs...")
replay_start_time = time.time()
in_game_mode = False

# Gamepad axis and button mappings for pygame
axis_map = {
    "ABS_X": 0,  # Left Stick X
    "ABS_Y": 1,  # Left Stick Y
    "ABS_RX": 2,  # Right Stick X
    "ABS_RY": 3,  # Right Stick Y
}

button_map = {
    "BTN_SOUTH": 0,  # A button
    "BTN_EAST": 1,   # B button
    "BTN_NORTH": 3,  # Y button
    "BTN_WEST": 2,   # X button
    "BTN_TL": 4,     # Left Bumper
    "BTN_TR": 5,     # Right Bumper
    "BTN_START": 7,  # Start button
    "BTN_SELECT": 6, # Back button
    "BTN_THUMBL": 8, # Left Stick Click
    "BTN_THUMBR": 9  # Right Stick Click
}

for event in events:
    action = event[0]
    timestamp = event[-1]
    elapsed_replay_time = time.time() - replay_start_time
    
    # Timing synchronization
    sleep_duration = max(0, timestamp - elapsed_replay_time)
    if sleep_duration > 0:
        time.sleep(sleep_duration)

    try:
        # Switch to in-game mode on 'n' press
        if action == "key_press" and event[1] == "n" and not in_game_mode:
            in_game_mode = True
            print("Switched to in-game mode (gamepad replay)")

        # Menu mode (mouse/keyboard)
        if not in_game_mode:
            if action == "move_absolute":
                x = event[1] + correction_x
                y = event[2] + correction_y
                pydirectinput.moveTo(x, y)
                print(f"Move to ({x}, {y}) at {timestamp:.2f}s")
            elif action == "click":
                x, y, button_str, pressed = event[1], event[2], event[3], event[4]
                button = "left" if "left" in button_str.lower() else "right"
                corrected_x = x + correction_x
                corrected_y = y + correction_y
                pydirectinput.moveTo(corrected_x, corrected_y)
                if pressed:
                    pydirectinput.mouseDown(button=button)
                    print(f"Pressed {button} at ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")
                else:
                    pydirectinput.mouseUp(button=button)
                    print(f"Released {button} at ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")
            elif action == "double_click":
                x, y, button_str = event[1], event[2], event[3]
                button = "left" if "left" in button_str.lower() else "right"
                corrected_x = x + correction_x
                corrected_y = y + correction_y
                pydirectinput.moveTo(corrected_x, corrected_y)
                pydirectinput.doubleClick(button=button)
                print(f"Double clicked {button} at ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")
            elif action == "scroll":
                x, y, dx, dy = event[1], event[2], event[3], event[4]
                corrected_x = x + correction_x
                corrected_y = y + correction_y
                pydirectinput.moveTo(corrected_x, corrected_y)
                pyautogui.scroll(dy)
                print(f"Scrolled by ({dx}, {dy}) at ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")
            elif action == "key_press":
                key = event[1].replace("Key.", "").lower()
                pydirectinput.keyDown(key)
                print(f"Pressed key {key} at {timestamp:.2f}s")
            elif action == "key_release":
                key = event[1].replace("Key.", "").lower()
                pydirectinput.keyUp(key)
                print(f"Released key {key} at {timestamp:.2f}s")

        # In-game mode (gamepad simulation)
        elif gamepad:  # Only process gamepad if Xbox controller is available
            if action == "gamepad_axis":
                axis, value = event[1], event[2]
                if axis in axis_map:
                    axis_id = axis_map[axis]
                    normalized_value = value / 32767.0  # Normalize to [-1.0, 1.0]
                    gamepad.set_axis(axis_id, normalized_value)
                    print(f"Set {axis} to {normalized_value} at {timestamp:.2f}s")
            elif action == "gamepad_press":
                button = event[1]
                if button in button_map:
                    button_id = button_map[button]
                    gamepad.set_button(button_id, 1)
                    print(f"Pressed {button} at {timestamp:.2f}s")
            elif action == "gamepad_release":
                button = event[1]
                if button in button_map:
                    button_id = button_map[button]
                    gamepad.set_button(button_id, 0)
                    print(f"Released {button} at {timestamp:.2f}s")

    except Exception as e:
        print(f"Error during replay of event {event}: {e}")
        continue

print("Replay finished.")