import psutil
import wmi
import time

def get_system_stats():
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # RAM Usage
    ram_info = psutil.virtual_memory()
    ram_used = ram_info.used / (1024**3)  # Convert bytes to GB
    ram_total = ram_info.total / (1024**3)
    
    # GPU Usage (WMI for Windows)
    w = wmi.WMI()
    gpu_info = w.Win32_VideoController()[0]
    gpu_name = gpu_info.Name
    gpu_vram = int(gpu_info.AdapterRAM) / (1024**3)  # Convert bytes to GB

    return cpu_percent, ram_used, ram_total, gpu_name, gpu_vram

# Start monitoring for 30 seconds
for i in range(30):
    cpu, ram_used, ram_total, gpu, gpu_vram = get_system_stats()
    print(f"CPU: {cpu}%, RAM: {ram_used:.2f}/{ram_total:.2f} GB, GPU: {gpu} ({gpu_vram:.2f} GB)")
    time.sleep(1)  # Log every second
