from pynput import keyboard
import os
import time
import pyautogui
import pydirectinput

running = True







def on_release(key):
    global running
    try:
        if (key.char == "="):
            running = not running
    except:
        pass



running = True
ct = True
restart_interval = 3 * 60
kill_interval = 5

saved_restart_time = time.time()
saved_kill_time = time.time()
con = keyboard.Controller()
time.sleep(5)

with keyboard.Listener(on_release=on_release) as listener:
    #listener.join()

    while True:
        while running:

            now_time = time.time()

            if now_time - saved_restart_time >= restart_interval:
                saved_restart_time = time.time()
                # Press key
                if ct:
                    pydirectinput.press("b")
                    time.sleep(2)
                    pydirectinput.press("b")
                else:
                    pydirectinput.press("n")
                    time.sleep(2)
                    pydirectinput.press("n")
                # con.release("n")
            if now_time - saved_kill_time >= kill_interval:
                saved_kill_time = time.time()
                # Press key
                pydirectinput.press("m")
                # con.release("m")mm

            time.sleep(0.1)