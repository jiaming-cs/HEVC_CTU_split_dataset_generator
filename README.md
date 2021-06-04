# HEVC_CTU_split_dataset_generator

This repository provide tools to generate Coding Unit image files and their corresponding depths for HEVC intra-prediction. The dataset is useful for building CU depth prediction models. The work is based on [
HEVC-CU-depths-dataset](https://github.com/wolverinn/HEVC-CU-depths-dataset), but I made three modeifcations:  

* Add mutiple threads to speedup the processing time

* The code generates dataset for different Quantity Parameters (QPs)

* Provide a Linux version of HM TAppEncoder

## Usage

* Add yuv files inside the folder `yuv-file`, name it with format `<video_name>_<resolution>_<FPS>.yuv`. For example: `ShakeNDry_1920x1024_120.yuv`

* Install `ffmpeg` for frames extraction, and python dependencies such as opencv

* Run the dataset generation script, for example on windows:

```bash
python gen_dataset.py
```

The code is not tested after adding to the respsitory and not well documented. Feel free to open new issues if you need any help or explaination :)
