import pyautogui
import time
import json
import keyboard
import ctypes

# Set DPI awareness to match recording environment
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

# Configure pyautogui
pyautogui.PAUSE = 0.01  # Small pause for input reliability

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

# Calculate correction based on initial position
first_absolute_event = next((e for e in events if e[0] == "move_absolute"), None)
correction_x = 0
correction_y = 0
if first_absolute_event:
    recorded_x, recorded_y = first_absolute_event[1], first_absolute_event[2]
    recorded_x = max(0, min(recorded_x, screen_width - 1))  # Clamp to screen
    recorded_y = max(0, min(recorded_y, screen_height - 1))
    pyautogui.moveTo(recorded_x, recorded_y, duration=0.1)  # Smooth move
    time.sleep(0.5)  # Ensure position sets
    actual_x, actual_y = pyautogui.position()
    correction_x = recorded_x - actual_x  # Positive if replay is left
    correction_y = recorded_y - actual_y
    print(f"Recorded initial position: ({recorded_x}, {recorded_y})")
    print(f"Actual initial position after move: ({actual_x}, {actual_y})")
    print(f"Calculated correction: ({correction_x}, {correction_y})")
    if abs(correction_x) > 5 or abs(correction_y) > 5:
        print("Mismatch detected. Reapplying initial position...")
        pyautogui.moveTo(recorded_x, recorded_y, duration=0.1)
        time.sleep(0.2)
        new_x, new_y = pyautogui.position()
        print(f"Position after reapply: ({new_x}, {new_y})")

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
            pyautogui.moveTo(center_x, center_y, duration=0.1)
            print(f"Switched to in-game mode, reset to ({center_x}, {center_y})")
            time.sleep(0.1)

        # Mouse movements
        elif action == "move_relative" and in_game_mode:
            dx, dy = event[1], event[2]
            pyautogui.moveRel(dx, dy, duration=0.01)
            print(f"Relative move by ({dx}, {dy}) at {timestamp:.2f}s")
        elif action == "move_absolute" and not in_game_mode:
            x = max(0, min(event[1] + correction_x, screen_width - 1))
            y = max(0, min(event[2] + correction_y, screen_height - 1))
            pyautogui.moveTo(x, y, duration=0.1)
            actual_x, actual_y = pyautogui.position()
            print(f"Absolute move to corrected ({x}, {y}), actual: ({actual_x}, {actual_y}) at {timestamp:.2f}s")

        # Mouse clicks
        elif action == "click":
            x, y, button_str, pressed = event[1], event[2], event[3], event[4]
            button = "left" if "left" in button_str.lower() else "right"
            if not in_game_mode:
                corrected_x = max(0, min(x + correction_x, screen_width - 1))
                corrected_y = max(0, min(y + correction_y, screen_height - 1))
                pyautogui.moveTo(corrected_x, corrected_y, duration=0.1)
                actual_x, actual_y = pyautogui.position()
                if pressed:
                    pyautogui.mouseDown(button=button)
                    print(f"Pressed {button} at corrected ({corrected_x}, {corrected_y}), actual: ({actual_x}, {actual_y}) at {timestamp:.2f}s")
                else:
                    pyautogui.mouseUp(button=button)
                    print(f"Released {button} at corrected ({corrected_x}, {corrected_y}), actual: ({actual_x}, {actual_y}) at {timestamp:.2f}s")
        elif action == "double_click":
            x, y, button_str = event[1], event[2], event[3]
            button = "left" if "left" in button_str.lower() else "right"
            if not in_game_mode:
                corrected_x = max(0, min(x + correction_x, screen_width - 1))
                corrected_y = max(0, min(y + correction_y, screen_height - 1))
                pyautogui.moveTo(corrected_x, corrected_y, duration=0.1)
                pyautogui.doubleClick(button=button)
                actual_x, actual_y = pyautogui.position()
                print(f"Double clicked {button} at corrected ({corrected_x}, {corrected_y}), actual: ({actual_x}, {actual_y}) at {timestamp:.2f}s")

        # Scroll (disabled in-game)
        elif action == "scroll" and not in_game_mode:
            x, y, dx, dy = event[1], event[2], event[3], event[4]
            corrected_x = max(0, min(x + correction_x, screen_width - 1))
            corrected_y = max(0, min(y + correction_y, screen_height - 1))
            pyautogui.moveTo(corrected_x, corrected_y, duration=0.1)
            if dy != 0:
                pyautogui.scroll(dy)
            actual_x, actual_y = pyautogui.position()
            print(f"Scrolled by ({dx}, {dy}) at corrected ({corrected_x}, {corrected_y}), actual: ({actual_x}, {actual_y}) at {timestamp:.2f}s")

        # Keyboard actions
        elif action == "key_press":
            key = event[1].replace("Key.", "").lower()
            pyautogui.keyDown(key)
            print(f"Pressed key {key} at {timestamp:.2f}s")
        elif action == "key_release":
            key = event[1].replace("Key.", "").lower()
            pyautogui.keyUp(key)
            print(f"Released key {key} at {timestamp:.2f}s")

    except Exception as e:
        print(f"Error during replay of event {event}: {e}")
        continue
    
print("Replay finished.")