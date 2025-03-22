import pyautogui
import time

print("Move your mouse over the button, and wait for 5 seconds...")
time.sleep(5)  # Gives you wwtime to place the cursor
x, y = pyautogui.position()
print(f"Mouse Position: {x}, {y}")
#Mouse Position: 2470, 1263 --> last of us 1