import os
import pickle
import shutil
import threading
import time
import pickle

def gen_cfg(yuv_filename):
    DataName = yuv_filename.split('_')[0]
    FrameRate = yuv_filename.split('_')[2].strip(".yuv")
    SourceWidth = yuv_filename.split('_')[1].split('x')[0]
    SourceHeight = yuv_filename.split('_')[1].split('x')[1]
    with open( os.path.join(WORKSPACE_PATH, "config", "bitstream_{}.cfg".format(DataName)),'w') as f:
        f.write("InputFile : {}\n".format(os.path.join(YUV_FILE_PATH,yuv_filename)))
        f.write("InputBitDepth : 8\n")
        f.write("InputChromaFormat : 420\n")
        f.write("FrameRate : {}\n".format(FrameRate))
        f.write("FrameSkip : 0\n")
        f.write("SourceWidth : {}\n".format(SourceWidth))
        f.write("SourceHeight : {}\n".format(SourceHeight))
        f.write("FramesToBeEncoded : 5000\n")
        f.write("Level : 3.1")

def dump_data(data, qp, workspace_dir):
    data_dict = {}
    with open(os.path.join(workspace_dir, data, str(qp), "PartitionInfo_{data}_{qp}.txt".format(data=data, qp=qp)), "r") as f:
        line = f.readline()
        while line != '':
            if line.find("frame")!=-1:
                frame_indx = int(line.strip("\n").split(":")[1]) - 1
                data_dict[frame_indx] = {}
            if line.find("ctu")!=-1:
                ctu_index = int(line.strip("\n").split(":")[1])
                #data_dict[qp][frame_indx][ctu_index] = []
                lb = []
                for i in range(16):
                    line = f.readline()
                    if i % 4 == 0:
                        depths = line.strip().strip("\n").split(" ")
                        for j in range(0, 16, 4):
                            lb.append(int(depths[j]))
                data_dict[frame_indx][ctu_index] = lb.copy()
            line = f.readline() 
    pkl_file_name = "{}_{}_{}.pkl".format(data, qp, frame_indx)
    f_pkl = open(os.path.join(workspace_dir, data, str(qp), pkl_file_name), 'ab')
    pickle.dump(data_dict, f_pkl)
    f_pkl.close()



class EncodingThread (threading.Thread):
    def __init__(self, work_space_dir, data_name, QP, encoder = "TAppEncoder_64_linux"):
        threading.Thread.__init__(self)
        self.work_space_dir = work_space_dir
        self.data_name = data_name
        self.encoder = encoder
        self.QP = QP

    def run(self):
        
        
        thread_work_path = os.path.join(self.work_space_dir, self.data_name, str(self.QP))
        if not os.path.exists(thread_work_path):
            os.system("mkdir " + thread_work_path)
        shutil.copy(os.path.join(self.work_space_dir, 'bin', self.encoder), os.path.join(thread_work_path, self.encoder))
        encoding_cmd = "{thread_path}/{encoder} -c {workspace_path}/config/{encoder_config} -c {workspace_path}/config/bitstream_{data_name}.cfg".format(thread_path = thread_work_path, encoder = self.encoder, workspace_path = WORKSPACE_PATH, encoder_config = "encoder_intra_main_64.cfg", data_name = self.data_name)
        os.system(encoding_cmd) 
        ctu_partition_info_file = "PartitionInfo_{}_{}.txt".format(self.data_name, self.QP)
        ctu_partition_info_file = os.path.join(thread_work_path, ctu_partition_info_file)
        os.rename(os.path.join(thread_work_path, "PartitionInfo.txt"), ctu_partition_info_file)
        os.remove(os.path.join(thread_work_path, self.encoder))
        dump_data(self.data_name, self.QP, self.work_space_dir) 
        

def change_QP(QP, data_name, config_file = "encoder_intra_main_64.cfg"):
    data = ""
    with open(os.path.join(WORKSPACE_PATH, "config", config_file), "r+") as f:
        for line in f.readlines():
            if line.find("QP                            :") == 0:
                line = "QP                            : {}\n".format(QP)
            if line.find("BitstreamFile                 :") == 0:
                line = "BitstreamFile                 : {}/str{}_{}.bin\n".format(TEMP_PATH, data_name, str(QP))
            if line.find("ReconFile                     :") == 0:
                line = "ReconFile                     : {}/rec{}_{}.yuv\n".format(TEMP_PATH, data_name, str(QP))    
            data += line

    with open(os.path.join(WORKSPACE_PATH, "config", config_file), "r+") as f:
        f.writelines(data)
    
    
if __name__ == "__main__":
    # this script needs to be in the same directory of the encoder.exe: WORKSPACE_PATH, config file must be in the config folder of the WORKSPACE
    WORKSPACE_PATH = os.getcwd()
    TEMP_PATH = os.path.join(WORKSPACE_PATH, "temp_bin_yuv")
    if not os.path.exists(TEMP_PATH):
        os.mkdir(TEMP_PATH)
    YUV_FILE_PATH = os.path.join(WORKSPACE_PATH, "yuv-file")
    QP_list = [22, 27, 32, 37]
    lock = threading.Lock()
    for i,yuv_filename in enumerate(os.listdir(YUV_FILE_PATH)):  
        data_name = yuv_filename.split("_")[0]
        data_size = yuv_filename.split("_")[1]
        data_rate = yuv_filename.split("_")[2].strip(".yuv")
        
        dataset_path = os.path.join(WORKSPACE_PATH, data_name)
        img_path = os.path.join(WORKSPACE_PATH, dataset_path, "img")
        gen_cfg(yuv_filename) # 生成运行HEVC编码器需要的配置文件，包括帧率，宽高等参数，参数从文件名中读取
        if not os.path.exists(img_path):
            os.system("mkdir " + dataset_path)
            os.system("mkdir " + img_path)
        for QP in QP_list:
            change_QP(QP, data_name)
            thread = EncodingThread(WORKSPACE_PATH, data_name, QP)
            thread.start()
            time.sleep(60)
        gen_frames_cmd = "~/ffmpeg/ffmpeg -video_size {size} -pixel_format yuv420p -i {yuv_file_path} {image_folder}/%d.png".format(size = data_size, yuv_file_path = os.path.join(WORKSPACE_PATH, "yuv-file", yuv_filename), image_folder = img_path)
        os.system(gen_frames_cmd)
        
            
        
            


 
    
        
