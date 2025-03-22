import ctypes
from ctypes import wintypes
import time
import json
import threading
from pynput import mouse, keyboard
import comtypes
from comtypes import CLSCTX_ALL

# Define DirectInput GUIDs
GUID_SysMouse = comtypes.GUID("{6F1D2B60-D5A0-11CF-BFC7-444553540000}")
IID_IDirectInput8W = comtypes.GUID("{BF798031-483A-4DA2-AA99-5D64ED369700}")  # Unicode version
DIRECTINPUT_VERSION = 0x0800
DISCL_FOREGROUND = 0x00000001
DISCL_NONEXCLUSIVE = 0x00000002

# Storage for recorded events
events = []
start_time = time.time()
recording = True
last_click_time = 0
last_click_button = None
DOUBLE_CLICK_THRESHOLD = 0.3
last_mouse_pos = (0, 0)
in_game_mode = False

# Setup DirectInput
def setup_direct_input():
    dinput = ctypes.windll.dinput8

    # Define DirectInput8Create function
    DirectInput8Create = ctypes.WINFUNCTYPE(
        wintypes.HRESULT,  # Return type
        wintypes.HINSTANCE,  # hInstance
        wintypes.DWORD,  # dwVersion
        ctypes.POINTER(comtypes.GUID),  # riidltf
        ctypes.POINTER(ctypes.POINTER(comtypes.IUnknown)),  # ppvOut
        wintypes.LPVOID  # pUnkOuter (NULL)
    )(("DirectInput8Create", dinput))

    # Create DirectInput8 interface
    dinput_obj = ctypes.POINTER(comtypes.IUnknown)()
    h_instance = ctypes.windll.kernel32.GetModuleHandleW(None)

    hr = DirectInput8Create(
        h_instance,
        DIRECTINPUT_VERSION,
        ctypes.byref(IID_IDirectInput8W),
        ctypes.byref(dinput_obj),
        None
    )

    if hr != 0:
        raise RuntimeError(f"Failed to create DirectInput8: HRESULT {hr}")

    return dinput_obj

# Mouse listener (clicks & scrolls)
def on_click(x, y, button, pressed):
    global last_click_time, last_click_button
    elapsed_time = time.time() - start_time
    if pressed:
        time_since_last_click = elapsed_time - last_click_time
        if time_since_last_click < DOUBLE_CLICK_THRESHOLD and last_click_button == button:
            events.append(("double_click", x, y, str(button), elapsed_time))
            print(f"Double click with {button} at {elapsed_time:.2f}s")
        else:
            events.append(("click", x, y, str(button), True, elapsed_time))
            print(f"Click with {button} at {elapsed_time:.2f}s")
        last_click_time = elapsed_time
        last_click_button = button
    else:
        events.append(("click", x, y, str(button), False, elapsed_time))
        print(f"Release with {button} at {elapsed_time:.2f}s")

def on_scroll(x, y, dx, dy):
    elapsed_time = time.time() - start_time
    events.append(("scroll", x, y, dx, dy, elapsed_time))
    print(f"Scroll with dx={dx}, dy={dy} at {elapsed_time:.2f}s")

# Keyboard listener
def on_press(key):
    global in_game_mode, recording
    elapsed_time = time.time() - start_time
    try:
        char = key.char
        events.append(("key_press", char, elapsed_time))
        print(f"Key pressed: {char} at {elapsed_time:.2f}s")
        if char == 'n' and not in_game_mode:
            in_game_mode = True
            print("Switched to in-game mode")
        elif char == 'm':
            recording = False
            print("Stopping recording...")
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

# Start everything
print("Starting recording... Press 'n' for in-game mode, 'm' to stop.")
mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

mouse_listener.start()
keyboard_listener.start()
keyboard_listener.join()
mouse_listener.stop()

# Save events
print(f"Recording stopped. Captured {len(events)} evemnts.")
try:
    with open("input_log.json", "w") as f:
        json.dump(events, f)
    print("Events saved to input_log.json")
except Exception as e:
    print(f"Error saving to input_log.json: {e}")
