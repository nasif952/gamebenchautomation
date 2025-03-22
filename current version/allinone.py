import pyautogui
import time
import psutil
import subprocess
import os

# Step 1: Launch the game
game_path = "H:/games/The Last of Us - Part I/tlou-i-l.exe"  # Replace with your game's path
subprocess.Popen(game_path)
time.sleep(5)  # Wait for the game to load

# Step 2: Navigate the menu (example coordinates)
# pyautogui.doubleClick(x=2470, y=1263)   # Click "Start" button (adjust coordinates) //2470, 1263
pyautogui.doubleClick(x=2470, y=1263)  # Click "Play" (adjust coordinates) //299, 504 --> 256, 676 -->398, 712-->1797, 863
time.sleep(12)

pyautogui.press('w', presses=10, interval=0.1) 
time.sleep(5)
pyautogui.click(x=252,y=497)  # Click "Play" (adjust coordinates) //299, 504 --> 256, 676 -->398, 712-->1797, 863
time.sleep(6)
pyautogui.click(x=252,y=497)  # Click "Play" (adjust coordinates) //299, 504 --> 256, 676 -->398, 712-->1797, 863
time.sleep(6)
# Additional click sequences
pyautogui.click(x=299, y=504)
time.sleep(7)

pyautogui.click(x=256, y=676)
time.sleep(3)

pyautogui.click(x=398, y=712)
time.sleep(3)

pyautogui.click(x=1797, y=863)
time.sleep(10)

# Step 3: Simulate the walkthrough
pyautogui.press('w', presses=100, interval=1)  # Move forward for 1 second
pyautogui.click(x=900, y=500)  # Shoot or interactww
pyautogui.press('s', presses=5, interval=0.1)  # Move backward

# Step 4: Collect performance data (example: CPU usage)
def log_performance():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory_usage}%")
    # Save to a file
    with open("benchmark_log.txt", "a") as f:
        f.write(f"CPU: {cpu_usage}%, Memory: {memory_usage}%\n")

# Run performance logging during the walkthrough
for _ in range(5):  # Log for 5 seconds
    log_performance()
    time.sleep(1)

# Step 5: Close the game
for proc in psutil.process_iter():
    if "tlou-i-l.exe" in proc.name():  # Replace with your game's process name
        proc.kill()
print("Game closed.")