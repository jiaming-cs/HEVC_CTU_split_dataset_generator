import os
import random
from PIL import Image
import pickle
import numpy as np
import random

class DataLoder():
    def __init__(self, data_list, frame_number = None , data_folder = "D:/DataSet/HEVC_CU/CU_64"):
        self.data_list = data_list
        self.frame_number = frame_number
        self.data_folder = data_folder
        assert(frame_number == None or len(frame_number) == len(data_list))

    def load(self, QP, random_select = True, p_64 = 1, p_32 = 0.5, p_16 = .3):
     
        x_data_64 = []
        y_data_64 = []
        x_data_32 = []
        y_data_32 = []
        x_data_16 = []
        y_data_16 = []
        for i, data in enumerate(self.data_list):
            img_path = os.path.join(self.data_folder, data, "img")
            total_frame = 0
            for file_name in os.listdir(img_path):
                if file_name.find(".png") != -1:
                    total_frame += 1
            for file_name in os.listdir(os.path.join(self.data_folder, data, str(QP))):
                if file_name.find(".pkl") != -1:
                    pkl_file = file_name
                    break
        
            with open(os.path.join(self.data_folder, data, str(QP), pkl_file), "rb") as f:
                data_dict = pickle.load(f)
                for frame in os.listdir(img_path): 
                    if frame.find(".png") == -1:
                        continue
                    frame_index = int(frame.split(".")[0]) - 1 
                    img = Image.open(os.path.join(img_path, frame))
                    img_array = np.array(img)
                    height, width, _ = img_array.shape
                    cu_per_row = width // 64
                    for x in range(height // 64):
                        for y in range(width // 64):
                            cu_index = x * cu_per_row + y
                            cu = img_array[x*64:x*64+64, y*64:y*64+64, :]
                            lb_ctu_64 = np.array(data_dict[frame_index][cu_index]).reshape((4, 4))
                            if lb_ctu_64.sum() == 0: # do not split
                                if random.random() < p_64:
                                    x_data_64.append(cu)
                                    y_data_64.append(0)
                                continue
                            else:
                                if lb_ctu_64.sum() == 16: # only split once 
                                    if random.random() < p_64:
                                        x_data_64.append(cu)
                                        y_data_64.append(1)
                                    continue
                                else:
                                    if random.random() < p_64:
                                        x_data_64.append(cu)
                                        y_data_64.append(2)
                                    for ctu_32_x in range(2):
                                        for ctu_32_y in range(2):
                                            lb_ctu_32 = lb_ctu_64[ctu_32_x*2:ctu_32_x*2+2, ctu_32_y*2:ctu_32_y*2+2]
                                            ctu_32 = cu[ctu_32_x*32:ctu_32_x*32+32, ctu_32_y*32:ctu_32_y*32+32]
                                            if lb_ctu_32.sum() == 4: # do not split
                                                if random.random() < p_32:
                                                    x_data_32.append(ctu_32)
                                                    y_data_32.append(0)
                                            else:
                                                if lb_ctu_32.sum() == 8: # no more split
                                                    if random.random() < p_32:
                                                        x_data_32.append(ctu_32)
                                                        y_data_32.append(1)
                                                    continue
                                                else:
                                                    if random.random() < p_32:
                                                        x_data_32.append(ctu_32)
                                                        y_data_32.append(2)
                                                    for ctu_16_x in range(2):
                                                        for ctu_16_y in range(2):
                                                            ctu_16 = ctu_32[ctu_16_x*16:ctu_16_x*16+16, ctu_16_y*16:ctu_16_y*16+16]
                                                            lb_ctu_16 = lb_ctu_32[ctu_16_x, ctu_16_y]
                                                            if lb_ctu_16 == 2:
                                                                if random.random() < p_16:
                                                                    x_data_16.append(ctu_16)
                                                                    y_data_16.append(0)
                                                            else:
                                                                if random.random() < p_16:
                                                                    x_data_16.append(ctu_16)
                                                                    y_data_16.append(1)
                    img.close()
                        
        return np.array(x_data_64), np.array(x_data_32), np.array(x_data_16), np.array(y_data_64), np.array(y_data_32), np.array(y_data_16)