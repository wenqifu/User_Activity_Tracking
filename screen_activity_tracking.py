import time
import csv
import tkinter as tk
from threading import Thread, Lock
from pynput import mouse, keyboard
import os
import sys
from datetime import datetime

# Define the expiration date (year, month, day)
expiration_date = datetime(2024, 12, 20)

def check_expiration():
    current_date = datetime.utcnow()
    if current_date > expiration_date:
        tk.messagebox.showinfo("Expired", "This application has expired.")
        sys.exit()

# Global variables to store tracking data
total_pixels_moved = 0.0
total_clicks = 0
total_keys = 0
start_time = None
running = True

# Variables to keep track of previous mouse position
prev_x = None
prev_y = None

# Lock for thread-safe operations
events_lock = Lock()
events = []

def on_move(x, y):
    global total_pixels_moved, prev_x, prev_y, start_time
    if not running:
        return False

    current_time = time.time() - start_time
    if prev_x is not None and prev_y is not None:
        dx = x - prev_x
        dy = y - prev_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        total_pixels_moved += distance
        with events_lock:
            events.append({'time': current_time, 'type': 'move', 'distance': distance})
    prev_x = x
    prev_y = y

def on_click(x, y, button, pressed):
    global total_clicks, start_time
    if not running:
        return False

    if pressed:
        total_clicks += 1
        current_time = time.time() - start_time
        with events_lock:
            events.append({'time': current_time, 'type': 'click'})

def on_press(key):
    global total_keys, start_time
    if not running:
        return False

    current_time = time.time() - start_time
    total_keys += 1
    with events_lock:
        events.append({'time': current_time, 'type': 'key'})

def start_mouse_listener():
    with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
        listener.join()

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def save_data_periodically():
    while running:
        time.sleep(5)
        with events_lock:
            sorted_events = sorted(events, key=lambda e: e['time'])
            if sorted_events:
                last_time = sorted_events[-1]['time']
                writer.writerow({
                    'time': last_time,
                    'total_keys': total_keys,
                    'total_clicks': total_clicks,
                    'total_distance': total_pixels_moved
                })
                csvfile.flush()  # Ensure data is written to file

def start_gui():
    root = tk.Tk()
    root.title("Mouse and Keyboard Tracker")
    root.geometry("200x100")
    root.resizable(False, False)

    def stop_tracking():
        global running
        running = False
        root.destroy()

    stop_button = tk.Button(root, text="Stop tracking", command=stop_tracking)
    stop_button.pack(expand=True)

    root.mainloop()

if __name__ == '__main__':
    check_expiration()
    script_dir = os.path.dirname(os.path.abspath(__file__)) if not getattr(sys, 'frozen', False) else os.path.dirname(sys.executable)
    summary_file = os.path.join(script_dir, 'summary.csv')

    start_time = time.time()

    with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['time', 'total_keys', 'total_clicks', 'total_distance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Start the threads for mouse, keyboard listeners and periodic saving
        mouse_thread = Thread(target=start_mouse_listener)
        mouse_thread.start()
        keyboard_thread = Thread(target=start_keyboard_listener)
        keyboard_thread.start()
        save_thread = Thread(target=save_data_periodically)
        save_thread.start()

        start_gui()

        mouse_thread.join()
        keyboard_thread.join()
        save_thread.join()

    print("Tracking completed.")
