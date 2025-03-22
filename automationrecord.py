from pynput import mouse, keyboard
import time
import json
import threading
from inputs import get_gamepad, UnpluggedError

# Storage for recorded events
events = []
start_time = time.time()
recording = True
last_click_time = 0
last_click_button = None
DOUBLE_CLICK_THRESHOLD = 0.3
last_mouse_pos = (0, 0)
in_game_mode = False
MOVE_THRESHOLD = 0.05  # Finer threshold for mouse

# Mouse polling function (menu mode)
def poll_mouse_position():
    global last_mouse_pos
    mouse_ctrl = mouse.Controller()
    last_x, last_y = mouse_ctrl.position
    events.append(("move_absolute", last_x, last_y, 0.0))  # Log initial position
    print(f"Initial position recorded at ({last_x}, {last_y}) at 0.00s")
    print("Mouse polling started (Windows/Menu mode)...")
    while recording:
        if not in_game_mode:  # Only poll mouse in menu mode
            loop_start = time.time()
            x, y = mouse_ctrl.position
            elapsed_time = loop_start - start_time
            dx, dy = x - last_x, y - last_y
            dist = (dx**2 + dy**2)**0.5
            if dist >= MOVE_THRESHOLD:
                events.append(("move_absolute", x, y, elapsed_time))
                print(f"Mouse moved to ({x}, {y}) at {elapsed_time:.2f}s")
                last_x, last_y = x, y
            last_mouse_pos = (x, y)
            elapsed_loop = time.time() - loop_start
            time.sleep(max(0, 0.005 - elapsed_loop))  # ~200 Hz
        else:
            time.sleep(0.005)  # Idle in gamepad mode

# Gamepad polling function (in-game mode)
def poll_gamepad():
    print("Gamepad polling ready (starts after 'n')...")
    while recording:
        if in_game_mode:
            try:
                gamepad_events = get_gamepad()
                elapsed_time = time.time() - start_time
                for event in gamepad_events:
                    event_type = event.ev_type
                    code = event.code
                    state = event.state

                    # Joystick movements (left and right sticks)
                    if event_type == "Absolute":
                        if code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY"]:
                            events.append(("gamepad_axis", code, state, elapsed_time))
                            print(f"Gamepad axis {code} moved to {state} at {elapsed_time:.2f}s")
                    # Buttons
                    elif event_type == "Key":
                        action = "gamepad_press" if state == 1 else "gamepad_release"
                        events.append((action, code, elapsed_time))
                        print(f"Gamepad {action} {code} at {elapsed_time:.2f}s")
            except UnpluggedError:
                print("Gamepad not detected! Please connect your controller.")
                time.sleep(1)  # Wait before retrying
        time.sleep(0.005)  # ~200 Hz polling

# Mouse listener (menu mode)
def on_click(x, y, button, pressed):
    global last_click_time, last_click_button
    elapsed_time = time.time() - start_time
    click_x, click_y = last_mouse_pos
    if pressed:
        time_since_last_click = elapsed_time - last_click_time
        if time_since_last_click < DOUBLE_CLICK_THRESHOLD and last_click_button == button:
            events.append(("double_click", click_x, click_y, str(button), elapsed_time))
            print(f"Double click at ({click_x}, {click_y}) with {button} at {elapsed_time:.2f}s")
        else:
            events.append(("click", click_x, click_y, str(button), True, elapsed_time))
            print(f"Click at ({click_x}, {click_y}) with {button} at {elapsed_time:.2f}s")
        last_click_time = elapsed_time
        last_click_button = button
    else:
        events.append(("click", click_x, click_y, str(button), False, elapsed_time))
        print(f"Release at ({click_x}, {click_y}) with {button} at {elapsed_time:.2f}s")

def on_scroll(x, y, dx, dy):
    elapsed_time = time.time() - start_time
    scroll_x, scroll_y = last_mouse_pos
    events.append(("scroll", scroll_x, scroll_y, dx, dy, elapsed_time))
    print(f"Scroll at ({scroll_x}, {scroll_y}) with dx={dx}, dy={dy} at {elapsed_time:.2f}s")

# Keyboard listener
def on_press(key):
    global in_game_mode
    elapsed_time = time.time() - start_time
    try:
        char = key.char
        events.append(("key_press", char, elapsed_time))
        print(f"Key pressed: {char} at {elapsed_time:.2f}s")
        if char == 'n' and not in_game_mode:
            in_game_mode = True
            print("Switched to in-game mode (gamepad input)")
        elif char == 'm':
            global recording
            recording = False
            print("'m' detected, stopping recording...")
            return False
    except AttributeError:
        events.append(("key_press", str(key), elapsed_time))
        print(f"Special key pressed: {key} at {elapsed_time:.2f}s")

def on_release(key):
    elapsed_time = time.time() - start_time
    try:
        char = key.char
        events.append(("key_release", char, elapsed_time))
        print(f"Key released: {char} at {elapsed_time:.2f}s")
    except AttributeError:
        events.append(("key_release", str(key), elapsed_time))
        print(f"Special key released: {key} at {elapsed_time:.2f}s")

# Start listeners and polling
print("Starting recording (Windows/Menu mode)...")
mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_poller = threading.Thread(target=poll_mouse_position)
gamepad_poller = threading.Thread(target=poll_gamepad)

mouse_listener.start()
keyboard_listener.start()
mouse_poller.start()
gamepad_poller.start()

print("Recording... Press 'n' to switch to in-game mode (gamepad), 'm' to stop.")
keyboard_listener.join()
mouse_listener.stop()
mouse_poller.join()
gamepad_poller.join()

print(f"Recording stopped. Captured {len(events)} events.")

try:
    with open("input_log.json", "w") as f:
        json.dump(events, f)
    print("Events saved to input_log.json")
except Exception as e:
    print(f"Error saving to input_log.json: {e}")