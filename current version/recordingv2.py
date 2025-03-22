from pynput import mouse, keyboard
import time
import json
import threading
from inputs import get_gamepad, UnpluggedError

# Storage for recorded events and press states
events = []
start_time = time.time()
recording = True
last_click_time = 0
last_click_button = None
DOUBLE_CLICK_THRESHOLD = 0.3
last_mouse_pos = (0, 0)
in_game_mode = False
MOVE_THRESHOLD = 0.05  # Finer threshold for mouse
pressed_keys = {}  # Track key press start times
pressed_gamepad_buttons = {}  # Track gamepad button press start times
pressed_gamepad_axes = {}  # Track gamepad axis press states

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

                    if event_type == "Absolute":
                        if code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY"]:
                            events.append(("gamepad_axis", code, state, elapsed_time))
                            print(f"Gamepad axis {code} set to {state} at {elapsed_time:.2f}s")
                    elif event_type == "Key":
                        if state == 1:  # Pressed
                            if code not in pressed_gamepad_buttons:
                                pressed_gamepad_buttons[code] = elapsed_time
                                events.append(("gamepad_press", code, elapsed_time))
                                print(f"Gamepad button {code} pressed at {elapsed_time:.2f}s")
                        elif state == 0 and code in pressed_gamepad_buttons:  # Released
                            duration = elapsed_time - pressed_gamepad_buttons[code]
                            events.append(("gamepad_release", code, duration, elapsed_time))
                            print(f"Gamepad button {code} released after {duration:.2f}s at {elapsed_time:.2f}s")
                            del pressed_gamepad_buttons[code]

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
    global in_game_mode, recording
    elapsed_time = time.time() - start_time
    try:
        char = key.char
        if char not in pressed_keys:  # Only log press if not already pressed
            pressed_keys[char] = elapsed_time
            events.append(("key_press", char, elapsed_time))
            print(f"Key pressed: {char} at {elapsed_time:.2f}s")
        if char == 'n' and not in_game_mode:
            in_game_mode = True
            print("Switched to in-game mode (gamepad input)")
        elif char == 'm':
            recording = False
            print("'m' detected, stopping recording...")
            return False
    except AttributeError:
        key_str = str(key)
        if key_str not in pressed_keys:
            pressed_keys[key_str] = elapsed_time
            events.append(("key_press", key_str, elapsed_time))
            print(f"Special key pressed: {key} at {elapsed_time:.2f}s")

def on_release(key):
    elapsed_time = time.time() - start_time
    try:
        char = key.char
        if char in pressed_keys:
            duration = elapsed_time - pressed_keys[char]
            events.append(("key_release", char, duration, elapsed_time))
            print(f"Key released: {char} after {duration:.2f}s at {elapsed_time:.2f}s")
            del pressed_keys[char]
    except AttributeError:
        key_str = str(key)
        if key_str in pressed_keys:
            duration = elapsed_time - pressed_keys[key_str]
            events.append(("key_release", key_str, duration, elapsed_time))
            print(f"Special key released: {key} after {duration:.2f}s at {elapsed_time:.2f}s")

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

# Log any remaining pressed keys or gamepad inputs on stop
elapsed_time = time.time() - start_time
for key, press_time in list(pressed_keys.items()):
    duration = elapsed_time - press_time
    events.append(("key_release", key, duration, elapsed_time))
    print(f"Key {key} released after {duration:.2f}s at end of recording")
for code, press_time in list(pressed_gamepad_buttons.items()):
    duration = elapsed_time - press_time
    events.append(("gamepad_release", code, duration, elapsed_time))
    print(f"Gamepad button {code} released after {duration:.2f}s at end of recording")
for code, press_time in list(pressed_gamepad_axes.items()):
    duration = elapsed_time - press_time
    events.append(("gamepad_axis_release", code, duration, elapsed_time))
    print(f"Gamepad axis {code} released after {duration:.2f}s at end of recording")

print(f"Recording stopped. Captured {len(events)} events.")

try:
    with open("input_log.json", "w") as f:
        json.dump(events, f)
    print("Events saved to input_log.json")
except Exception as e:
    print(f"Error saving to input_log.json: {e}")