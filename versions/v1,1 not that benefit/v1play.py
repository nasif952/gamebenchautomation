from pynput import mouse, keyboard
import time
import json

# Initialize controllers
mouse_ctrl = mouse.Controller()
keyboard_ctrl = keyboard.Controller()

# Load recorded events
with open("input_log.json", "r") as f:
    events = json.load(f)

print("Replaying inputs...")
replay_start_time = time.time()

# Replay events
for i, event in enumerate(events):
    action = event[0]
    timestamp = event[-1]
    elapsed_replay_time = time.time() - replay_start_time
    sleep_duration = max(0, timestamp - elapsed_replay_time)
    if sleep_duration > 0:
        time.sleep(sleep_duration)
    
    if action == "move_relative":
        dx, dy = event[1], event[2]
        mouse_ctrl.move(dx, dy)  # Use relative movement for gameplay
        print(f"Replayed relative move by ({dx}, {dy}) at {timestamp:.2f}s")
    elif action == "move_absolute":
        x, y = event[1], event[2]
        mouse_ctrl.position = (x, y)  # Use absolute for menus
        print(f"Replayed absolute move to ({x}, {y}) at {timestamp:.2f}s")
    elif action == "click":
        x, y, button_str, pressed = event[1], event[2], event[3], event[4]
        button = mouse.Button.left if "left" in button_str else mouse.Button.right
        mouse_ctrl.position = (x, y)
        if pressed:
            mouse_ctrl.press(button)
            print(f"Pressed {button_str} at ({x}, {y}) at {timestamp:.2f}s")
        else:
            mouse_ctrl.release(button)
            print(f"Released {button_str} at ({x}, {y}) at {timestamp:.2f}s")
    elif action == "double_click":
        x, y, button_str = event[1], event[2], event[3]
        button = mouse.Button.left if "left" in button_str else mouse.Button.right
        mouse_ctrl.position = (x, y)
        mouse_ctrl.click(button, 2)
        print(f"Double clicked {button_str} at ({x}, {y}) at {timestamp:.2f}s")
    elif action == "scroll":
        x, y, dx, dy = event[1], event[2], event[3], event[4]
        mouse_ctrl.position = (x, y)
        mouse_ctrl.scroll(dx, dy)
        print(f"Scrolled by ({dx}, {dy}) at ({x}, {y}) at {timestamp:.2f}s")
    elif action == "key_press":
        key = event[1]
        try:
            keyboard_ctrl.press(key)
            print(f"Pressed key {key} at {timestamp:.2f}s")
        except ValueError:
            keyboard_ctrl.press(getattr(keyboard.Key, key.split(".")[1]))
            print(f"Pressed special key {key} at {timestamp:.2f}s")
    elif action == "key_release":
        key = event[1]
        try:
            keyboard_ctrl.release(key)
            print(f"Released key {key} at {timestamp:.2f}s")
        except ValueError:
            keyboard_ctrl.release(getattr(keyboard.Key, key.split(".")[1]))
            print(f"Released special key {key} at {timestamp:.2f}s")

print("Replay finished.")