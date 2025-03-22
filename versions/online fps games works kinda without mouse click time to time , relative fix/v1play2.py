import pydirectinput
import pyautogui
import time
import json
import keyboard
import ctypes

# Set DPI awareness
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

# Configure pydirectinput
pydirectinput.PAUSE = 0.005  # Reduced for smoother input

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

# Get screen resolution
screen_width, screen_height = pyautogui.size()
center_x, center_y = screen_width // 2, screen_height // 2

print(f"Screen resolution: {screen_width}x{screen_height}")
print("Waiting for 'n' to start replay...")

# Wait for 'n' to be pressed
keyboard.wait('n')

# Initial position correction (pre-in-game only)
first_absolute_event = next((e for e in events if e[0] == "move_absolute"), None)
correction_x = 0
correction_y = 0
if first_absolute_event:
    recorded_x, recorded_y = first_absolute_event[1], first_absolute_event[2]
    pydirectinput.moveTo(recorded_x, recorded_y)
    time.sleep(0.5)  # Ensure position sets
    actual_x, actual_y = pyautogui.position()
    correction_x = recorded_x - actual_x
    correction_y = recorded_y - actual_y
    print(f"Recorded initial position: ({recorded_x}, {recorded_y})")
    print(f"Actual initial position: ({actual_x}, {actual_y})")
    print(f"Applying correction: ({correction_x}, {correction_y})")
    if abs(correction_x) > 5 or abs(correction_y) > 5:
        print("Correction applied due to position mismatch.")
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
        # Handle mode switch to in-game
        if action == "key_press" and event[1] == "n" and not in_game_mode:
            in_game_mode = True
            # No center reset - rely on game's internal state
            print("Switched to in-game mode, using game’s current camera position")
            time.sleep(0.1)

        # Mouse movements
        elif action == "move_relative" and in_game_mode:
            dx, dy = event[1], event[2]
            # Test inversion (uncomment one if needed)
            pydirectinput.moveRel(dx, dy, relative=True)  # Default
            # pydirectinput.moveRel(-dx, dy)  # Invert x-axis
            # pydirectinput.moveRel(dx, -dy)  # Invert y-axis
            # pydirectinput.moveRel(-dx, -dy)  # Invert both
            current_x, current_y = pyautogui.position()  # Debug position
            print(f"Relative move by ({dx}, {dy}) at {timestamp:.2f}s, now at ({current_x}, {current_y})")
            time.sleep(0.002)  # Smoother transitions
        elif action == "move_absolute" and not in_game_mode:
            x = event[1] + correction_x
            y = event[2] + correction_y
            pydirectinput.moveTo(x, y)
            print(f"Absolute move to corrected ({x}, {y}) at {timestamp:.2f}s")

        # Mouse clicks
        elif action == "click":
            x, y, button_str, pressed = event[1], event[2], event[3], event[4]
            button = "left" if "left" in button_str.lower() else "right"
            if not in_game_mode:
                corrected_x = x + correction_x
                corrected_y = y + correction_y
                pydirectinput.moveTo(corrected_x, corrected_y)
            if pressed:
                pydirectinput.mouseDown(button=button)
                print(f"Pressed {button} at corrected ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")
            else:
                pydirectinput.mouseUp(button=button)
                print(f"Released {button} at corrected ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")
        elif action == "double_click":
            x, y, button_str = event[1], event[2], event[3]
            button = "left" if "left" in button_str.lower() else "right"
            if not in_game_mode:
                corrected_x = x + correction_x
                corrected_y = y + correction_y
                pydirectinput.moveTo(corrected_x, corrected_y)
            pydirectinput.doubleClick(button=button)
            print(f"Double clicked {button} at corrected ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")

        # Scroll (disabled in-game)
        elif action == "scroll" and not in_game_mode:
            x, y, dx, dy = event[1], event[2], event[3], event[4]
            corrected_x = x + correction_x
            corrected_y = y + correction_y
            pydirectinput.moveTo(corrected_x, corrected_y)
            if dy != 0:
                pyautogui.scroll(dy)
            print(f"Scrolled by ({dx}, {dy}) at corrected ({corrected_x}, {corrected_y}) at {timestamp:.2f}s")

        # Keyboard actions
        elif action == "key_press":
            key = event[1].replace("Key.", "").lower()
            pydirectinput.keyDown(key)
            print(f"Pressed key {key} at {timestamp:.2f}s")
        elif action == "key_release":
            key = event[1].replace("Key.", "").lower()
            pydirectinput.keyUp(key)
            print(f"Released key {key} at {timestamp:.2f}s")

    except Exception as e:
        print(f"Error during replay of event {event}: {e}")
        continue

print("Replay finished.")