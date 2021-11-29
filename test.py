import io
import os
import numpy as np
import six
import time
import math
import glob

from six import BytesIO

import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

import tensorflow as tf
from models.research.object_detection.utils import ops as utils_ops
from models.research.object_detection.utils import label_map_util
from models.research.object_detection.utils import visualization_utils as vis_util


from PIL import ImageGrab
import win32api, win32con, win32gui
import pygame
from pynput import keyboard
import pydirectinput

# physical_devices = tf.config.experimental.list_physical_devices('GPU')
# assert len(physical_devices) > 0, "Not enough GPU hardware devices available"
# config = tf.config.experimental.set_memory_growth(physical_devices[0], True)



import ctypes

# C struct redefinitions 
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Actuals Functions
def MouseMoveTo(x, y):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(x, y, 0, 0x0001, 0, ctypes.pointer(extra))

    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))


def LeftClick():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

running = True
screenshot = False
aimbot = False
overlay = True
lastOverlay = True

labelmap_path = "training/label_map.txt"
output_directory = "inference_graph"
def load_image_into_numpy_array(path):
    img_data = tf.io.gfile.GFile(path, 'rb').read()
    image = Image.open(BytesIO(img_data))
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)

category_index = label_map_util.create_category_index_from_labelmap(labelmap_path, use_display_name=True)

tf.keras.backend.clear_session()
model = tf.saved_model.load(f'{output_directory}/saved_model')
def on_press(key):
    global running
    global aimbot
    global overlay
    global lastOverlay
    try:
        if (key.char == "`"):
            running = False
        elif (key.char == "l"):
            aimbot = not aimbot
        elif (key.char == "o"):
            lastOverlay = overlay
            overlay = not overlay
            
    except:
        pass
def on_release(key):
    global screenshot
    #print("Key pressed: {0}".format(key))
    try:
        if (key.char == "\\"):
            screenshot = True
    except:
        if (key == keyboard.Key.shift_r):
            detector.toggleShoot()
def moveWindow(x, y, width, height):
    win32gui.SetWindowPos(pygame.display.get_wm_info()["window"], -1, 0, 0, 0, 0, 0x0001)
def run_inference_for_single_image(model, image):
    image = np.asarray(image)
    # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
    input_tensor = tf.convert_to_tensor(image)
    # The model expects a batch of images, so add an axis with `tf.newaxis`.
    input_tensor = input_tensor[tf.newaxis,...]

    # Run inference
    model_fn = model.signatures['serving_default']
    output_dict = model_fn(input_tensor)

    # All outputs are batches tensors.
    # Convert to numpy arrays, and take index [0] to remove the batch dimension.
    # We're only interested in the first num_detections.
    num_detections = int(output_dict.pop('num_detections'))
    #print("DETECTIONS: ", num_detections)
    output_dict = {key:value[0, :num_detections].numpy() 
                    for key,value in output_dict.items()}
    output_dict['num_detections'] = num_detections

    # detection_classes should be ints.
    output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)

    # Handle models with masks:
    if 'detection_masks' in output_dict:
    # Reframe the the bbox mask to the image size.
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                output_dict['detection_masks'], output_dict['detection_boxes'],
                image.shape[0], image.shape[1])      
        detection_masks_reframed = tf.cast(detection_masks_reframed > 0,
                                        tf.uint8)
        output_dict['detection_masks_reframed'] = detection_masks_reframed.numpy()
    
    return output_dict

def getGameWindow():
    hwnd = win32gui.FindWindow(None, "Counter-Strike: Global Offensive")
    windowrect = win32gui.GetWindowRect(hwnd)
    x = windowrect[0] + 8
    y = windowrect[1]
    width = windowrect[2] - x
    height = windowrect[3] - y
    #print(x, y)
    return x, y, width, height

class Detector:
    def __init__(self, model):
        pygame.init()
        pygame.font.init()
        x, y, width, height = getGameWindow()

        self.model = model



        self.screenEnabled = False

        self.toggleScreen()
        
        
        self.transparent = (255, 0, 128)
        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.white = (255, 255, 255)

        self.overlay_font = pygame.font.SysFont(None, 20)

        if self.screenEnabled:
            hwnd = pygame.display.get_wm_info()["window"]
            win32api.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
            win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.transparent), 0, win32con.LWA_COLORKEY)


        self.line_width = 1

        self.outer_width = 400
        self.outer_height = 400

        self.outer_x, self.outer_y = 0, 0
        

        self.outerEnabled = True


        self.shoot = False

        self.keypress = False

    def toggleScreen(self):
        info = pygame.display.Info()
        if not self.screenEnabled:
            self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
            self.screenEnabled = True
        else:
            self.screen = pygame.display.set_mode((1, 1), pygame.NOFRAME)
            self.screenEnabled = False


    def toggleShoot(self):
        self.shoot = not self.shoot

    def drawBoxInOuter(self, x, y, width, height, text=None):
        if self.screenEnabled:
            pygame.draw.rect(self.screen, self.red, pygame.Rect((self.outer_x + x, self.outer_y + y, self.line_width, height)))
            pygame.draw.rect(self.screen, self.red, pygame.Rect((self.outer_x + x, self.outer_y + y, width, self.line_width)))

            pygame.draw.rect(self.screen, self.red, pygame.Rect((self.outer_x + x + width, self.outer_y + y, self.line_width, height)))
            pygame.draw.rect(self.screen, self.red, pygame.Rect((self.outer_x + x, self.outer_y + y + height, width, self.line_width)))

            if text is not None:
                self.screen.blit(text, (self.outer_x + x, self.outer_y + y))

    def update(self):

            x, y, width, height = getGameWindow()

            self.outer_x = x + (width / 2) - (self.outer_width / 2)
            self.outer_y = y + (height / 2) - (self.outer_height / 2)

            
            pygame.event.get()
            if self.screenEnabled:
                moveWindow(x, y, width, height)
                self.screen.fill(self.transparent)

                if self.outerEnabled:
                    pygame.draw.rect(self.screen, self.green, pygame.Rect((self.outer_x, self.outer_y, self.line_width, self.outer_height)))
                    pygame.draw.rect(self.screen, self.green, pygame.Rect((self.outer_x, self.outer_y, self.outer_width, self.line_width)))

                    pygame.draw.rect(self.screen, self.green, pygame.Rect((self.outer_x + self.outer_width, self.outer_y, self.line_width, self.outer_height)))
                    pygame.draw.rect(self.screen, self.green, pygame.Rect((self.outer_x, self.outer_y + self.outer_height, self.outer_width, self.line_width)))


            self.drawBoxes()
            if self.screenEnabled:
                pygame.display.update()

    def getOuter(self):
        x, y, x2, y2 = self.outer_x, self.outer_y, self.outer_x + self.outer_width, self.outer_y + self.outer_height
        return (x, y, x2, y2)
        

    def drawBoxes(self):
        global lastOverlay, overlay
        x, y, x2, y2 = self.getOuter()
        img = ImageGrab.grab((x, y, x2, y2))
        img_array = np.array(img)


        output_dict = run_inference_for_single_image(self.model, img)

        # print(output_dict)
        boxes = output_dict['detection_boxes']
        classes = output_dict['detection_classes']
        scores = output_dict['detection_scores']
        max_boxes = 100


        min_distance = 99999
        closest_x = 0
        closest_y = 0
        mouse_x, mouse_y = pydirectinput.position()
        for i in range(boxes.shape[0]):
            if i >= max_boxes:
                break
            if scores[i] > 0.4: #and (classes[i] == 2 or classes[i] == 4):
                ymin, xmin, ymax, xmax = boxes[i]

                # if classes[i] == 1 or classes[i] == 3:
                #     if self.outer_width * (xmax - xmin) < 70:
                #print(xmin * self.outer_width, ymin * self.outer_height, 
                    #xmax * self.outer_width - xmin * self.outer_width, ymax * self.outer_width - ymin * self.outer_height)

                local_text = self.overlay_font.render(str(classes[i]), False, self.white)
                
                self.drawBoxInOuter(xmin * self.outer_width, ymin * self.outer_height, 
                    xmax * self.outer_width - xmin * self.outer_width, ymax * self.outer_height - ymin * self.outer_height,
                    text=local_text)

                
                # pydirectinput.move(int((self.outer_x + xmin) - mouse_x), int((self.outer_y + ymin) - mouse_y))

                real_coord_x = (self.outer_x + (xmin + xmax)/2 * self.outer_width)
                real_coord_y = (self.outer_y + (ymin + ymax)/2 * self.outer_height)

        
                distance = math.sqrt(pow(mouse_x - real_coord_x, 2) + pow(mouse_x - real_coord_y, 2))
                if distance < min_distance:
                    min_distance = distance
                    closest_x = real_coord_x
                    closest_y = real_coord_y


        if aimbot and min_distance < 99999:
            MouseMoveTo(int(1.2*(closest_x - mouse_x)), int(1.2*(closest_y - mouse_y)))
            if abs(closest_x - mouse_x) < 20 and abs(closest_y - mouse_y) < 20:
                LeftClick()

            # if abs(closest_x - mouse_x) < 30 and abs(closest_y - mouse_y) < 30:
            #     LeftClick()


        if lastOverlay != overlay:
            self.toggleScreen()
            lastOverlay = overlay

    def takeScreenshot(self):
        x, y, x2, y2 = self.getOuter()
        img = ImageGrab.grab((x, y, x2, y2))
        img_array = np.array(img)


        output_dict = run_inference_for_single_image(self.model, img)


        vis_util.visualize_boxes_and_labels_on_image_array(
            img_array,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            category_index,
            instance_masks=output_dict.get('detection_masks_reframed', None),
            use_normalized_coordinates=True,
            line_thickness=8,
            min_score_thresh=0.8)

        Image.fromarray(img_array).show()


detector = Detector(model)



with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    #listener.join()


    while running:

        detector.update()

        
        #time.sleep(0.01)

        if screenshot:
            detector.takeScreenshot()
            screenshot = False
        if not running:
            pygame.display.quit()
            pygame.quit()
            quit()