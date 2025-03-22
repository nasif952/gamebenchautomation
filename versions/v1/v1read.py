from pynput import mouse, keyboard
import time
import json
import threading

# Storage for recorded events
events = []
start_time = time.time()
recording = True
last_click_time = 0
last_click_button = None
DOUBLE_CLICK_THRESHOLD = 0.3  # 300ms threshold for double-click detection
current_mouse_pos = (0, 0)  # Shared variable for latest mouse position

# Mouse polling function for smooth movement and position tracking
def poll_mouse_position():
    global current_mouse_pos
    mouse_ctrl = mouse.Controller()
    last_x, last_y = mouse_ctrl.position
    print("Mouse polling started...")
    while recording:
        x, y = mouse_ctrl.position
        elapsed_time = time.time() - start_time
        if (x, y) != (last_x, last_y):
            events.append(("move", x, y, elapsed_time))
            print(f"Mouse moved to ({x}, {y}) at {elapsed_time:.2f}s")
            last_x, last_y = x, y
        current_mouse_pos = (x, y)  # Update current position
        time.sleep(0.01)  # 10ms polling

# Mouse listener for clicks and scrolls
def on_click(x, y, button, pressed):
    global last_click_time, last_click_button
    elapsed_time = time.time() - start_time
    # Use the last known position from polling instead of x, y from on_click
    click_x, click_y = current_mouse_pos
    if pressed:
        time_since_last_click = elapsed_time - last_click_time
        if (time_since_last_click < DOUBLE_CLICK_THRESHOLD and 
            last_click_button == button):
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
    scroll_x, scroll_y = current_mouse_pos  # Use polled position
    events.append(("scroll", scroll_x, scroll_y, dx, dy, elapsed_time))
    print(f"Scroll at ({scroll_x}, {scroll_y}) with dx={dx}, dy={dy} at {elapsed_time:.2f}s")

# Keyboard listener
def on_press(key):
    elapsed_time = time.time() - start_time
    try:
        events.append(("key_press", key.char, elapsed_time))
        print(f"Key pressed: {key.char} at {elapsed_time:.2f}s")
    except AttributeError:
        events.append(("key_press", str(key), elapsed_time))
        print(f"Special key pressed: {key} at {elapsed_time:.2f}s")

def on_release(key):
    elapsed_time = time.time() - start_time
    try:
        events.append(("key_release", key.char, elapsed_time))
        print(f"Key released: {key.char} at {elapsed_time:.2f}s")
    except AttributeError:
        events.append(("key_release", str(key), elapsed_time))
        print(f"Special key released: {key} at {elapsed_time:.2f}s")
    if key == keyboard.Key.esc:
        global recording
        recording = False
        print("ESC detected, stopping recording...")
        return False

# Start listeners and polling
print("Starting recording...")
mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_poller = threading.Thread(target=poll_mouse_position)

mouse_listener.start()
keyboard_listener.start()
mouse_poller.start()

print("Recording... Press ESC to stop.")
keyboard_listener.join()
mouse_listener.stop()
mouse_poller.join()

print(f"Recording stopped. Captured {len(events)} events.")

# Save recorded events to a file
try:
    with open("input_log.json", "w") as f:
        json.dump(events, f)
    print("Events saved to input_log.json")
except Exception as e:
    print(f"Error saving to input_log.json: {e}")