from pydantic import BaseModel, Field
from enum import Enum
import subprocess


# 存储视频文件类型
class FileType(Enum):
    # 音频
    WAV = 'wav'
    MP3 = 'mp3'
    # 视频
    MP4 = 'mp4'

# 检查ffmpeg是否存在
def is_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False


# 检查视频文件的音频和视频部分是否存在
def check_av_exist(video_path):
    command = ["ffmpeg", "-i", video_path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
    output, _ = process.communicate()
    audio_exists = "Audio:" in output
    video_exists = "Video:" in output

    return audio_exists, video_exists


if __name__ == "__main__":

    import config.mme_rag_config as cfg
    import os
    v_path = os.path.join(cfg.dataset_dir, '【aa.mp4')

    x,y = check_av_exist(v_path)

    print(f"音频是否存在 {str(x)} | 视频是否存在 {str(y)}")