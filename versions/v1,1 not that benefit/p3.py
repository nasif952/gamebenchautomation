import pyautogui
import time

# Move to game start button and click (replace X, Y with actual coordinates)
x, y = 2470, 1263  # Change this to your game’s "Start" button coordinates
pyautogui.moveTo(x, y, duration=1)  
pyautogui.click()

print("Benchmark started!")
