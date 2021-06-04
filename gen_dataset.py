import os
from PIL import Image
import math
import pickle
import shutil
import threading


def gen_cfg(yuv_filename):
    DataName = yuv_filename.split('_')[0]
    FrameRate = yuv_filename.split('_')[2].strip(".yuv")
    SourceWidth = yuv_filename.split('_')[1].split('x')[0]
    SourceHeight = yuv_filename.split('_')[1].split('x')[1]
    with open('.\\config\\bitstream_{}.cfg'.format(DataName),'w') as f:
        f.write("InputFile : {}\\{}\n".format(YUV_FILE_PATH,yuv_filename))
        f.write("InputBitDepth : 8\n")
        f.write("InputChromaFormat : 420\n")
        f.write("FrameRate : {}\n".format(FrameRate))
        f.write("FrameSkip : 0\n")
        f.write("SourceWidth : {}\n".format(SourceWidth))
        f.write("SourceHeight : {}\n".format(SourceHeight))
        f.write("FramesToBeEncoded : 5000\n")
        f.write("Level : 3.1")

def dump_ctu_file(ctu_partition_info_file):
    # 将抽取到的帧的所有ctu分割信息保存到pickle：{"frame_number_1":{"ctu_number_1":[...];"ctu_number_2":[...]};"frame_number_2":...}
    video_dict = {}
    line_count = 0
    with open(ctu_partition_info_file,'r') as f:
        for i,line in enumerate(f):
            if "frame" in line:
                current_frame = int(line.split(':')[1].strip())
                video_dict[current_frame] = {}
            elif "ctu" in line:
                ctu_number = int(line.split(':')[1].strip())
                line_count = 0
                video_dict[current_frame][ctu_number] = []
            else:
                
                if line_count % 4 == 0:
                    line_depths = line.strip().split(' ')
                    for index in range(0, len(line_depths), 4):
                        video_dict[current_frame][ctu_number].append(int(index))
                line_count += 1
    pkl_file_name = "{}.pkl".format(DATASET_NAME)
    f_pkl = open(os.path.join(DATASET_PATH, pkl_file_name), 'ab')
    pickle.dump(video_dict, f_pkl)
    f_pkl.close()

def crop_image_to_ctu(ctu_partition_info_file):
    frames = len(os.listdir(os.path.join(WORKSPACE_PATH, "temp-frames"))) # 当前视频一共有多少帧
    dump_ctu_file(ctu_partition_info_file)
    for image_file in os.listdir(os.path.join(WORKSPACE_PATH, "temp-frames")):
        frame_number = int(image_file.split('.')[0])
        img = Image.open(os.path.join(os.path.join(WORKSPACE_PATH, "temp-frames"),image_file))
        img_width, img_height = img.size
        ctu_number_per_img = math.ceil(img_width / 64) * math.ceil(img_height / 64)
        img.close()
        img_name = "{}_{}_.jpg".format(str(frame_number),str(ctu_number_per_img))
        shutil.copy(os.path.join(WORKSPACE_PATH, "temp-frames",image_file), os.path.join(IMG_PATH, img_name))
        os.remove(os.path.join(os.path.join(WORKSPACE_PATH, "temp-frames"),image_file)) # 裁剪过后的帧就删掉

class EncodingThread (threading.Thread):
    def __init__(self, work_space_dir, data_name, encoding_cmd, gen_frames_cmd, lock, encoder = "TAppEncoder_64.exe"):
        threading.Thread.__init__(self)
        self.work_space_dir = work_space_dir
        self.data_name = data_name
        self.encoding_cmd = encoding_cmd
        self.gen_frames_cmd = gen_frames_cmd
        self.lock = lock
        self.encoder = encoder

    def run(self):
        shutil.copy(os.path.join(self.work_space_dir, 'bin', self.encoder), os.path.join(self.work_space_dir, self.data_name, self.encoder))
        os.system(self.encoding_cmd) 
        ctu_partition_info_file = "Partitioninfo_{}.txt".format(self.data_name)
        ctu_partition_info_file = os.path.join(self.work_space_dir, self.data_name, ctu_partition_info_file)
        os.rename(os.path.join(self.work_space_dir, self.data_name, "Partitioninfo.txt"), ctu_partition_info_file)
        self.lock.acquire()
        os.system(self.gen_frames_cmd)
        print("processing yuv file: {}".format(yuv_filename))
        crop_image_to_ctu(ctu_partition_info_file) 
        self.lock.release()
    
if __name__ == "__main__":
    # this script needs to be in the same directory of the encoder.exe: WORKSPACE_PATH, config file must be in the config folder of the WORKSPACE
    WORKSPACE_PATH = os.getcwd()
    YUV_FILE_PATH = os.path.join(WORKSPACE_PATH, "yuv-file")
    data_info = []
    for i, yuv_filename in enumerate(os.listdir(YUV_FILE_PATH)):
        DATASET_NAME = yuv_filename.split("_")[0]
        DATASET_PATH = os.path.join(WORKSPACE_PATH, DATASET_NAME)
        IMG_PATH = os.path.join(WORKSPACE_PATH, DATASET_NAME, "img")

        if not os.path.exists(IMG_PATH):
            os.system("mkdir " + DATASET_PATH)
            os.system("mkdir " + IMG_PATH)

        #CtuInfo_FILENAME = "PartitionInfo_{}.txt".format(DATASET_NAME)
        #data_info.append(CtuInfo_FILENAME)
        encoding_cmd = "{}\\{}\\TAppEncoder_64.exe -c {}\\config\\encoder_intra_main_64.cfg -c {}\\config\\bitstream_{}.cfg".format(WORKSPACE_PATH, DATASET_NAME, WORKSPACE_PATH, WORKSPACE_PATH, DATASET_NAME)
        gen_cfg(yuv_filename) # 生成运行HEVC编码器需要的配置文件，包括帧率，宽高等参数，参数从文件名中读取
        #print (encoding_cmd)
        gen_frames_cmd = "ffmpeg -video_size {} -r {} -pixel_format yuv420p -i {}\\{} {}\\temp-frames\\%d.jpg".format(yuv_filename.split('_')[1],yuv_filename.split('_')[2].strip(".yuv"),YUV_FILE_PATH,yuv_filename,WORKSPACE_PATH)
        lock = threading.Lock()
        thread = EncodingThread(WORKSPACE_PATH, DATASET_NAME, encoding_cmd, gen_frames_cmd, lock)
        thread.start()
        


 
    
        