from lxml import etree
import cv2
import os, time
import numpy as np
import tensorflow as tf
from tensorflow.python.ops.gen_array_ops import empty
import win32gui
from PIL import ImageGrab
from models.research.object_detection.utils import ops as utils_ops


labels = {1: "ct_body", 2: "ct_head", 3: "t_body", 4: "t_head"}

def CreateXML(path, filename, image, bboxes):
    boxes = []
    for bbox in bboxes:
        boxes.append([bbox[0].astype(int), bbox[1].astype(int), bbox[2].astype(int), bbox[3].astype(int), bbox[4]])

    img_name = filename + ".jpg"
    cv2.imwrite(path + img_name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

    annotation = etree.Element("annotation")

    folder = etree.Element("folder")
    folder.text = path.split("\\")[-2]
    annotation.append(folder)

    filename_xml = etree.Element("filename")
    filename_xml.text = img_name
    annotation.append(filename_xml)

    path_xml = etree.Element("path")
    path_xml.text = path + img_name
    annotation.append(path_xml)

    source = etree.Element("source")
    annotation.append(source)

    database = etree.Element("database")
    database.text = "Unknown"
    source.append(database)

    size = etree.Element("size")
    annotation.append(size)

    width = etree.Element("width")
    height = etree.Element("height")
    depth = etree.Element("depth")

    width.text = str(image.shape[0])
    height.text = str(image.shape[1])
    depth.text = str(image.shape[2])

    size.append(width)
    size.append(height)
    size.append(depth)

    segmented = etree.Element("segmented")
    segmented.text = "0"
    annotation.append(segmented)

    for object in boxes:
        class_name = object[4]
        xmin_l = str(int(float(object[0])))
        ymin_l = str(int(float(object[1])))
        xmax_l = str(int(float(object[2])))
        ymax_l = str(int(float(object[3])))

        obj = etree.Element("object")
        annotation.append(obj)

        name = etree.Element("name")
        name.text = class_name
        obj.append(name)

        pose = etree.Element("pose")
        pose.text = "Unspecified"
        obj.append(pose)

        truncated = etree.Element("truncated")
        truncated.text = "0"
        obj.append(truncated)

        difficult = etree.Element("difficult")
        difficult.text = "0"
        obj.append(difficult)

        bndbox = etree.Element("bndbox")
        obj.append(bndbox)

        xmin = etree.Element("xmin")
        xmin.text = xmin_l
        bndbox.append(xmin)

        ymin = etree.Element("ymin")
        ymin.text = ymin_l
        bndbox.append(ymin)

        xmax = etree.Element("xmax")
        xmax.text = xmax_l
        bndbox.append(xmax)

        ymax = etree.Element("ymax")
        ymax.text = ymax_l
        bndbox.append(ymax)

    # write xml to file
    s = etree.tostring(annotation, pretty_print=True)
    with open(path + filename + ".xml", 'wb') as f:
        f.write(s)
        f.close()


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

        self.model = model

        self.current = 7000

        self.width = 600
        self.height = 600

        x, y, width, height = getGameWindow()

        self.x = x + (width / 2) - (self.width / 2)
        self.y = y + (height / 2) - (self.height / 2)

    def update(self):

        global lastOverlay, overlay
        x, y, x2, y2 = self.getOuterBox()
        img = ImageGrab.grab((x, y, x2, y2))
        img_array = np.array(img)


        output_dict = run_inference_for_single_image(self.model, img)

        # print(output_dict)
        boxes = output_dict['detection_boxes']
        classes = output_dict['detection_classes']
        scores = output_dict['detection_scores']

        used_classes = []
        bboxes = []


        for i in range(boxes.shape[0]):
            if scores[i] > 0.4:
                if classes[i] not in used_classes:
                    #used_classes.append(classes[i])
                    ymin, xmin, ymax, xmax = boxes[i]
                    xmin *= self.width
                    xmax *= self.width
                    ymin *= self.height
                    ymax *= self.height
                    bboxes.append([xmin, ymin, xmax, ymax, labels[classes[i]]])
        if len(bboxes) > 0:
            CreateXML(os.getcwd() + "\\training\\", "img" + str(self.current).zfill(6), img_array, bboxes)
            self.current += 1
            time.sleep(2)
    def getOuterBox(self):
        x, y, x2, y2 = self.x, self.y, self.x + self.width, self.y + self.height
        return (x, y, x2, y2)

output_directory = "inference_graph"
model = tf.saved_model.load(f'{output_directory}/saved_model')
detector = Detector(model)

while True:
    detector.update()