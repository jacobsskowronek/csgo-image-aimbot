import win32gui
from PIL import ImageGrab
from pynput import keyboard
import os
import time




def getGameWindow():
    hwnd = win32gui.FindWindow(None, "Counter-Strike: Global Offensive")
    #hwnd = win32gui.FindWindow(None, "Rainbow Six")
    windowrect = win32gui.GetWindowRect(hwnd)
    x = windowrect[0] + 8
    y = windowrect[1]
    width = windowrect[2] - x
    height = windowrect[3] - y
    #print(x, y)
    return x, y, width, height

# def on_press(key):
#     global running
#     if (key.char == "="):
#         running = not running
            

def on_release(key):
    global running
    try:
        if (key.char == "="):
            running = not running
    except:
        pass


class Trainer:
    def __init__(self):
        x, y, width, height = getGameWindow()

        self.curr_img = 0
        self.image_path = "training/"
        #self.image_path = "training/"
        self.image_name = "img{0:0=4d}.jpg".format(self.curr_img)

        try:
            os.mkdir(self.image_path)
        except:
            print("Making of training directory failed")
        else:
            print("Successfully created training directory")

        self.outer_width = 600
        self.outer_height = 600


        self.box_x, self.box_y = 0, 0
        self.outer_x, self.outer_y = 0, 0


        x, y, width, height = getGameWindow()
        self.outer_x = x + (width / 2) - (self.outer_width / 2)
        self.outer_y = y + (height / 2) - (self.outer_height / 2)

    def getOuter(self):
        x, y, x2, y2 = self.outer_x, self.outer_y, self.outer_x + self.outer_width, self.outer_y + self.outer_height
        return (x, y, x2, y2)

    def takeScreenshot(self):
        x, y, x2, y2 = self.getOuter()
        img = ImageGrab.grab((x, y, x2, y2))
       
        img.save(self.image_path + self.image_name, "JPEG")

        self.curr_img += 1
        self.image_name = "img{0:0=4d}.jpg".format(self.curr_img)




    



trainer = Trainer()

running = True
interval = 3

time.sleep(5)

with keyboard.Listener(on_release=on_release) as listener:
    #listener.join()

    while True:
        while running:

            time.sleep(interval)

            trainer.takeScreenshot()
    

