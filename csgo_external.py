import sys, os
 
import pymeow as pm
from requests import get
from PIL import ImageGrab
import time

from requests.api import head

class Offsets:
    pass
 
 
class Entity:
    def __init__(self, addr, mem):
        self.dormant = pm.read_int(mem, addr + Offsets.m_bDormant)
        self.team = pm.read_int(mem, addr + Offsets.m_iTeamNum)
        self.position = pm.read_vec3(mem, addr + Offsets.m_vecOrigin)
        self.spotted = pm.read_bool(mem, addr + Offsets.m_bSpotted)
        # self.spotted_mask = pm.read_int(mem, addr + Offsets.m_bSpottedByMask)
        self.bone_matrix = pm.read_uint(mem, addr + Offsets.m_dwBoneMatrix)
        self.head_position = {}
        self.position2d = None
        self.head_position2d = None
        self.lfoot_position2d = None
        self.rfoot_position2d = None
 
 
def fetch_offsets():
    # Credits to [url]https://github.com/frk1/hazedumper[/url]
    haze = get("https://raw.githubusercontent.com/frk1/hazedumper/master/csgo.json").json()
    [setattr(Offsets, k, v) for k, v in haze["signatures"].items()]
    [setattr(Offsets, k, v) for k, v in haze["netvars"].items()]

    # Offsets.dwViewMatrix = 0x4DB30B4
    # Offsets.dwEntityList = 0x4DC179C
    # Offsets.m_iTeamNum = 
    # Offsets.m_vecOrigin = 
    # Offsets.m_bSpotted = 

curr_img = 0
image_path = "training_demo/"
image_name = "img{0:0=4d}.jpg".format(curr_img)

try:
    os.mkdir(image_path)
except:
    print("Making of training directory failed")
else:
    print("Successfully created training directory")

def takeScreenshot(x, y, x2, y2):
    global curr_img
    global image_name
    img = ImageGrab.grab((x, y, x2, y2))
    
    img.save(image_path + image_name, "JPEG")

    curr_img += 1
    image_name = "img{0:0=4d}.jpg".format(curr_img)
 
 
def main():
    fetch_offsets()
    mem = pm.process_by_name("csgo.exe")
    client_module = mem["modules"]["client.dll"]["baseaddr"]
    overlay = pm.overlay_init()
 
    while pm.overlay_loop(overlay):
        pm.overlay_update(overlay)
        if pm.key_pressed(35):
            pm.overlay_close(overlay)
 
        view_matrix = pm.read_floats(mem, client_module + Offsets.dwViewMatrix, 16)
 
        # local_player_address = pm.read_int(mem, client_module + Offsets.dwLocalPlayer)
        # if not local_player_address:
        #     continue

        count = 0
 
        entity_addresses = pm.read_uints(mem, client_module + Offsets.dwEntityList, 128)[0::4]
        for entity_address in entity_addresses:
            # if entity_address and entity_address == local_player_address:
            #     continue
            
            try:
                entity = Entity(entity_address, mem)

                entity.head_position["x"] = pm.read_float(mem, entity.bone_matrix + (8 * 0x30) + 0x0c)
                entity.head_position["y"] = pm.read_float(mem, entity.bone_matrix + (8 * 0x30) + 0x1c)
                entity.head_position["z"] = pm.read_float(mem, entity.bone_matrix + (8 * 0x30) + 0x2c) + 8

                

                entity.position["z"] -= 5

                # print(entity.position["x"], entity.position["y"], entity.position["z"])

            except:
                continue
 
            if entity.dormant:
                continue

            count += 1
 
            try:
                entity.position2d = pm.wts_dx(overlay, view_matrix, entity.position)
                entity.head_position2d = pm.wts_dx(overlay, view_matrix, entity.head_position)

            except:
                continue

            #print(entity.bone_matrix)
            
            # print("Entity: ", hex(entity_address))

            # pm.line(
            #     overlay["midX"], 
            #     overlay["midY"], 
            #     entity.position2d["x"], 
            #     entity.position2d["y"], 
            #     1, 
            #     pm.rgb("cyan") if entity.team != 2 else pm.rgb("orange")
            # )
            # print(view_matrix)

            if entity.spotted and entity.position2d["x"] > 0 and entity.position2d["y"] > 0:
                y_distance = entity.head_position2d["y"] - entity.position2d["y"]
                ratio = 0.25

                x = entity.position2d["x"] - (ratio * y_distance)
                y = entity.position2d["y"]
                x2 = entity.position2d["x"] + (ratio * y_distance)
                y2 = entity.head_position2d["y"]
                w = x2 - x
                h = y2 - y

                print(x, 1080 - y2, w, h)
                # print(entity.head_position["x"])

                pm.line(
                    entity.position2d["x"] - (ratio * y_distance),
                    entity.position2d["y"], 
                    entity.position2d["x"] - (ratio * y_distance), 
                    entity.head_position2d["y"], 
                    1, 
                    pm.rgb("cyan") if entity.team != 2 else pm.rgb("orange")
                )
                pm.line(
                    entity.position2d["x"] + (ratio * y_distance),
                    entity.position2d["y"], 
                    entity.position2d["x"] + (ratio * y_distance), 
                    entity.head_position2d["y"], 
                    1, 
                    pm.rgb("cyan") if entity.team != 2 else pm.rgb("orange")
                )
                pm.line(
                    entity.position2d["x"] - (ratio * y_distance),
                    entity.position2d["y"], 
                    entity.position2d["x"] + (ratio * y_distance), 
                    entity.position2d["y"], 
                    1, 
                    pm.rgb("cyan") if entity.team != 2 else pm.rgb("orange")
                )
                pm.line(
                    entity.position2d["x"] - (ratio * y_distance),
                    entity.head_position2d["y"], 
                    entity.position2d["x"] + (ratio * y_distance), 
                    entity.head_position2d["y"], 
                    1, 
                    pm.rgb("cyan") if entity.team != 2 else pm.rgb("orange")
                )

                #takeScreenshot(x, y, x2, y2)

        # print(count)
 
 
if __name__ == "__main__":
    main()