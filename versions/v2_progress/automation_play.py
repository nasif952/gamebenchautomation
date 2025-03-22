import pydirectinput
import pyautogui
import time
import json
import keyboard
import ctypes
import vgamepad as vg  # Virtual Xbox 360 Controller

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

# Initialize virtual Xbox 360 controller
gamepad = None
try:
    gamepad = vg.VX360Gamepad()
    print("Virtual Xbox 360 controller initialized successfully.")
except Exception as e:
    print(f"Failed to initialize virtual gamepad: {e}")
    print("Continuing without gamepad support (menu mode only).")

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
            if gamepad:
                gamepad.reset()  # Reset virtual gamepad state

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

        # In-game mode (Virtual Xbox 360 Controller via vgamepad)
        elif gamepad:  # Only process gamepad if virtual controller is available
            if action == "gamepad_axis":
                axis, value = event[1], event[2]
                # Convert recorded range (-32768 to 32767) to vgamepad float (-1.0 to 1.0)
                axis_value = value / 32768.0
                if axis == "ABS_X":
                    gamepad.left_joystick_float(x_value_float=axis_value, y_value_float=0.0)
                    print(f"Set LeftStickX to {axis_value:.2f} at {timestamp:.2f}s")
                elif axis == "ABS_Y":
                    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=-axis_value)  # Inverted
                    print(f"Set LeftStickY to {-axis_value:.2f} at {timestamp:.2f}s")
                elif axis == "ABS_RX":
                    gamepad.right_joystick_float(x_value_float=axis_value, y_value_float=0.0)
                    print(f"Set RightStickX to {axis_value:.2f} at {timestamp:.2f}s")
                elif axis == "ABS_RY":
                    gamepad.right_joystick_float(x_value_float=0.0, y_value_float=-axis_value)  # Inverted
                    print(f"Set RightStickY to {-axis_value:.2f} at {timestamp:.2f}s")
                gamepad.update()  # Apply changes
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
                    "BTN_WEST": vg.XUSB_BUTnON.XUSB_GAMEPAD_X,
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

print("Replay finished.")
if gamepad:
    gamepad.reset()
    gamepad.update()