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

# Start time for replay
replay_start_time = time.time()

# Replay events
for i, event in enumerate(events):
    action = event[0]
    timestamp = event[-1]  # Original recorded timestamp
    
    # Synchronize timing with real-time playback
    elapsed_replay_time = time.time() - replay_start_time
    sleep_duration = max(0, timestamp - elapsed_replay_time)
    if sleep_duration > 0:
        time.sleep(sleep_duration)
    
    # Handle mouse actions
    if action == "move":
        x, y = event[1], event[2]
        mouse_ctrl.position = (x, y)
    elif action == "click":
        x, y, button_str, pressed = event[1], event[2], event[3], event[4]
        button = mouse.Button.left if "left" in button_str else mouse.Button.right
        mouse_ctrl.position = (x, y)
        if pressed:
            mouse_ctrl.press(button)
        else:
            mouse_ctrl.release(button)
    elif action == "double_click":
        x, y, button_str = event[1], event[2], event[3]
        button = mouse.Button.left if "left" in button_str else mouse.Button.right
        mouse_ctrl.position = (x, y)
        mouse_ctrl.click(button, 2)  # Perform a double click
    elif action == "scroll":
        x, y, dx, dy = event[1], event[2], event[3], event[4]
        mouse_ctrl.position = (x, y)
        mouse_ctrl.scroll(dx, dy)
    
    # Handle keyboard actions
    elif action == "key_press":
        key = event[1]
        try:
            keyboard_ctrl.press(key)
        except ValueError:
            keyboard_ctrl.press(getattr(keyboard.Key, key.split(".")[1]))
    elif action == "key_release":
        key = event[1]
        try:
            keyboard_ctrl.release(key)
        except ValueError:
            keyboard_ctrl.release(getattr(keyboard.Key, key.split(".")[1]))

print("Replay finished.")