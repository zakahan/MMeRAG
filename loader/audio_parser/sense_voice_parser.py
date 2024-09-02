
import os
from pydub import AudioSegment
from typing import Tuple, Dict, List, Union
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

from config.mme_rag_config import SENSE_VOICE_MODEL_PATH, SENSE_VOICE_VAD_MODEL_PATH


class SVParser:
    def __init__(self,
                 model: str = SENSE_VOICE_MODEL_PATH,
                 vad_model: str = SENSE_VOICE_VAD_MODEL_PATH,
                 use_itn: bool = True,
                 device: str = 'cpu'
                 ) -> None:

        self.model = AutoModel(model=model,
                               vad_model=vad_model,
                               vad_kwargs={"max_single_segment_time": 30000},
                               # trust_remote_code=True,
                               use_itn=use_itn,
                               device=device,  #,"cuda:0",
                               disable_update=True
                               )

        self.vad_model = AutoModel(
            model = vad_model,
            device=device,
            disable_update=True
        )


        pass

    def asr(self, input_audio: str, language: str = 'auto') -> str:
        # 解析音频,转为文字
        res = self.model.generate(
            input=input_audio,
            cache={},
            language=language,  # "zn", "en", "yue", "ja", "ko", "nospeech"
            use_itn=True,
            batch_size_s=60,
            # merge_vad=True,  # 是否将 vad 模型切割的短音频碎片合成，合并后长度为merge_length_s，单位为秒s。
            # merge_length_s=15,    # 这俩开启之后会报错
        )
        text = rich_transcription_postprocess(res[0]["text"])
        return text

    def vad_detect(self, input_audio: str) -> List[List]:
        res = self.vad_model.generate(input_audio)
        # the output as  [[beg1, end1], [beg2, end2], .., [begN, endN]]
        # 详情见 https://github.com/modelscope/FunASR/blob/main/examples/industrial_data_pretraining/fsmn_vad_streaming/demo.py
        return res[0]['value']

    def get_timestamps(self, input_audio,  threshold_second: Union[float, int]):
        # 用于合并vad_detect之后的时间戳，直接输出使用的时间戳切的太碎了，开始的位置可能还行，结尾吃音了
        vad_timestamps = self.vad_detect(input_audio)  # vad检测timestamps
        if len(vad_timestamps) == 0:
            raise Exception('本段音频没有任何声音')

        duration = vad_timestamps[-1][1]                # 最后一位
        timestamps = []
        start_timestamps = [0]
        for item in vad_timestamps:
            start_timestamps.append(item[0])

        start = 0
        for i in range(0, len(start_timestamps)):
            if start_timestamps[i] - start < threshold_second * 1000:
                continue         # i 推至下一个
            else:
                timestamps.append([start, start_timestamps[i]])
                start = start_timestamps[i]
        # 肯定有一个收尾的
        if len(timestamps) > 0:
            timestamps.append([start, duration])
        # print(timestamps)
        return timestamps


    def audio_split(self, input_audio: str, save_dir: str):     # 这个做的并不好，audio_split这个事情应该交给parser来，这个属于细节，
        res_list = []
        # 加载音频文件
        input_format = input_audio.split('.')[-1]
        audio = AudioSegment.from_file(input_audio, format=input_format)
        # 获取时间戳
        timestamps = self.get_timestamps(input_audio, threshold_second=10)

        # 遍历时间戳并切割音频，输出到文件夹
        for i, (beg, end) in enumerate(timestamps):
            # 切割音频片段
            clip = audio[beg:end]
            # 保存音频片段到文件
            save_path = os.path.join(save_dir, f"clip_{i}.wav")
            res_list.append(
                {
                    'start_time': beg,
                    'end_time': end,
                    'save_path': save_path
                })
            clip.export(save_path, format="wav")

        return res_list  # 返回这个，来确定文件位置

if __name__ == "__main__":
    # path = r"E:\ModelFiles\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch\example\vad_example.wav"
    # import os
    # import config.mme_rag_config as cfg
    # path = os.path.join(cfg.dataset_dir, "【中文字幕】YOASOBI不插电演唱会Acoustic Session小型现场たぶん & あの夢をなぞって【蓝光】@姐夫日剧字幕组.mp4")
    # sv_parser = SVParser()
    # # sv_parser.audio_split(path)
    # # print(x)
    print('hello world')