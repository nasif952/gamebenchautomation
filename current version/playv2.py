import pydirectinput
import pyautogui
import time
import json
import keyboard
import ctypes
import vgamepad as vg  # Virtual Xbox 360 Controller

# Set DPI awareness for accurate mouse positioning across monitors
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

# Minimize delay in pydirectinput actions
pydirectinput.PAUSE = 0.005

# Load recorded events from JSON file
try:
    with open("input_log.json", "r") as f:
        events = json.load(f)
    print(f"Loaded {len(events)} events from input_log.json")
except FileNotFoundError:
    print("Error: input_log.json not found!")
    exit(1)
except json.JSONDecodeError:
    print("Error: input_log.json is corrupted or invalid!")
    exit(1)

# Sort events by timestamp (last element in each event tuple)
events.sort(key=lambda e: e[-1])

# Initialize virtual gamepad
gamepad = None
try:
    gamepad = vg.VX360Gamepad()
    print("Virtual Xbox 360 controller initialized successfully.")
except Exception as e:
    print(f"Failed to initialize virtual gamepad: {e}")
    print("Continuing without gamepad support (menu mode only).")

# Initialize gamepad axis states
left_x = 0.0
left_y = 0.0
right_x = 0.0
right_y = 0.0

# Get screen resolution for reference
screen_width, screen_height = pyautogui.size()
print(f"Screen resolution: {screen_width}x{screen_height}")

# Wait for user to press 'n' to begin replay
print("Waiting for 'n' to start replay...")
keyboard.wait('n')

# Correct initial mouse position based on first recorded move
first_absolute_event = next((e for e in events if e[0] == "move_absolute"), None)
if first_absolute_event:
    recorded_x, recorded_y = first_absolute_event[1], first_absolute_event[2]
    pydirectinput.moveTo(recorded_x, recorded_y)
    time.sleep(0.5)  # Allow time for movement
    actual_x, actual_y = pyautogui.position()
    correction_x = recorded_x - actual_x
    correction_y = recorded_y - actual_y
    print(f"Initial correction: ({correction_x}, {correction_y})")
    if abs(correction_x) > 5 or abs(correction_y) > 5:
        pydirectinput.moveTo(recorded_x, recorded_y)
        time.sleep(0.2)  # Settle position
else:
    correction_x, correction_y = 0, 0

# Begin replaying events
print("Replaying inputs...")
replay_start_time = time.time()
in_game_mode = False

for event in events:
    action = event[0]
    timestamp = event[-1]
    elapsed_replay_time = time.time() - replay_start_time
    sleep_duration = max(0, timestamp - elapsed_replay_time)
    if sleep_duration > 0:
        time.sleep(sleep_duration)

    try:
        # Handle mouse events only in menu mode
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
                pyautogui.scroll(dy)  # Vertical scroll
                if dx != 0:
                    pyautogui.hscroll(dx)  # Horizontal scroll
                print(f"Scrolled by ({dx}, {dy}) at ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")

        # Handle keyboard events in both modes
        if action == "key_press":
            key = event[1].replace("Key.", "").lower()
            pydirectinput.keyDown(key)
            print(f"Pressed key {key} at {timestamp:.2f}s")
            # Switch to in-game mode when 'n' is pressed
            if key == 'n' and not in_game_mode:
                in_game_mode = True
                print("Switched to in-game mode (gamepad replay)")
                if gamepad:
                    gamepad.reset()
                    left_x = 0.0
                    left_y = 0.0
                    right_x = 0.0
                    right_y = 0.0
                    gamepad.update()
        elif action == "key_release":
            key = event[1].replace("Key.", "").lower()
            pydirectinput.keyUp(key)
            print(f"Released key {key} at {timestamp:.2f}s")

        # Handle gamepad events in in-game mode
        if in_game_mode and gamepad:
            if action == "gamepad_axis":
                axis, value = event[1], event[2]
                axis_value = float(value) / 32767.0  # Convert to -1.0 to 1.0
                if axis == "ABS_X":
                    left_x = axis_value
                elif axis == "ABS_Y":
                    left_y = axis_value
                elif axis == "ABS_RX":
                    right_x = axis_value
                elif axis == "ABS_RY":
                    right_y = axis_value
                if axis in ["ABS_X", "ABS_Y"]:
                    gamepad.left_joystick_float(x_value_float=left_x, y_value_float=left_y)
                    print(f"Set LeftStick {axis} to {axis_value:.2f} at {timestamp:.2f}s")
                elif axis in ["ABS_RX", "ABS_RY"]:
                    gamepad.right_joystick_float(x_value_float=right_x, y_value_float=right_y)
                    print(f"Set RightStick {axis} to {axis_value:.2f} at {timestamp:.2f}s")
                gamepad.update()
            elif action == "gamepad_press":
                button = event[1]
                button_map = {
                    "BTN_SOUTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    "BTN_EAST": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    "BTN_NORTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                    "BTN_WEST": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    "BTN_TL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    "BTN_TR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    "BTN_SELECT": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    "BTN_START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                    "BTN_THUMBL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                    "BTN_THUMBR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB
                }
                if button in button_map:
                    gamepad.press_button(button=button_map[button])
                    gamepad.update()
                    print(f"Pressed {button} at {timestamp:.2f}s")
            elif action == "gamepad_release":
                button = event[1]
                button_map = {
                    "BTN_SOUTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    "BTN_EAST": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    "BTN_NORTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                    "BTN_WEST": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    "BTN_TL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    "BTN_TR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    "BTN_SELECT": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    "BTN_START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                    "BTN_THUMBL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                    "BTN_THUMBR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB
                }
                if button in button_map:
                    gamepad.release_button(button=button_map[button])
                    gamepad.update()
                    print(f"Released {button} at {timestamp:.2f}s")

    except Exception as e:
        print(f"Error during replay of event {event}: {e}")
        continue

# Cleanup after replay
print("Replay finished.")
if gamepad:
    gamepad.reset()
    gamepad.update()

    