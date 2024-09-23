import os
import cv2
import uuid
import torch
import time
import shutil
from typing import List ,Dict, Tuple
from loader.audio_parser.sense_voice_parser import SVParser
from loader.video_parser.visualized_parser import VisualizedParser
from loader import wrench as wh
from config.mme_rag_config import SENSE_VOICE_MODEL_PATH, SENSE_VOICE_VAD_MODEL_PATH, KB_BASE_PATH
from config.mme_rag_config import KWARGS_SPACE_SECOND, KWARGS_HIS_THRESHOLD, KWARGS_SAMPLE_PLAN, KWARGS_EMBED_NAME
from rag.chunk import Chunk, ChunkType
from rag.embed import create_embeddings, Embeddings
from config.mme_rag_logger import logger


class MMeLoader:
    """
    这个方案的基本逻辑是一个混合搜索，
    也就是音频和视频画面作为两个部分进行搜索，
    先分开切片，存储成两个向量库，然后搜索的时候分别对两个部分做检索，最后再合并
    文本描述部分
    """

    def __init__(self, **kwargs) -> None:
        # 从kwargs中获得
        device = kwargs.get('device', 'cuda:0' if torch.cuda.is_available() else 'cpu')
        model = kwargs.get('model_path', SENSE_VOICE_MODEL_PATH)
        vad_model = kwargs.get('vad_model', SENSE_VOICE_VAD_MODEL_PATH)
        space_second = kwargs.get('space_second', KWARGS_SPACE_SECOND)
        his_threshold = kwargs.get('his_threshold', KWARGS_HIS_THRESHOLD)
        sample_plan = kwargs.get('sample_plan', KWARGS_SAMPLE_PLAN)
        embed_name = kwargs.get('embed_name', KWARGS_EMBED_NAME)
        embedding_instance = kwargs.get('embedding_instance', None)     # 用来捕获embedding实例，如果没有，后续会创造
        # 检查环境完备性
        if not wh.is_ffmpeg_installed():
            raise Exception('this loader need ffmpeg, please install it to start the project.')
        # 音频解析器
        self.audio_parser = SVParser(model=model, vad_model=vad_model, device=device)
        # 视频解析器（图像）
        self.video_parser = VisualizedParser(
            space_second=space_second, his_threshold=his_threshold, sample_plan=sample_plan
        )

        # 各种路径 就一个大的数据库了，懒得分了
        self.kb_content_path = os.path.join(KB_BASE_PATH, 'content')
        self.kb_raw_path = os.path.join(KB_BASE_PATH, 'raw')
        self.kb_tmp_path = os.path.join(KB_BASE_PATH, 'tmp')

        # 检测三个路径是否存在，不存在就创建,用os
        directories = [self.kb_content_path, self.kb_raw_path, self.kb_tmp_path]
        for directory in directories:
            if not os.path.exists(directory):
                print(f"路径{directory} 不存在， 现已创建。")
                os.makedirs(directory)

        # 配置embedding
        if embedding_instance is None:
            # 若为空 则创建
            self.embedding = create_embeddings(embed_name, device=device)
        else:
            self.embedding = embedding_instance

        logger.info('MMe-Loader 初始化完成')
        pass

    def get_embedding(self) -> Embeddings:
        return self.embedding

    def parser(self, file_path: str, source_id: str) -> Dict[str, List]:

        # 设置存储路径
        load_tmp_dir = os.path.join(self.kb_tmp_path, source_id)
        if not os.path.exists(load_tmp_dir):
            os.makedirs(load_tmp_dir)

        # 加载器
        # 先判断是否存在音频和视频画面
        wh.is_ffmpeg_installed()
        a_ex, v_ex = wh.check_av_exist(file_path)
        # 加载视频
        cap = cv2.VideoCapture(file_path)
        # 检查是否成功打开视频文件
        if not cap.isOpened():
            print("Error opening video_parser file")
            raise Exception("Error opening video_parser file")
        # -------------------------------------
        s1 = time.time()
        # 视频切分，保存为多张图片
        img_list = []
        if v_ex:
            # 对视频做切分，提取几张图片
            shot_list = self.video_parser.video_shot(file_path, load_tmp_dir)

            for i, shot_dic in enumerate(shot_list):
                text = self.video_parser.ocr(image_path=shot_dic['save_path'])
                img_list.append(
                    {
                        'start_time' : str(shot_dic['shot_time']),
                        'image_path' : str(shot_dic['save_path']),
                        'text': text
                    }
                )
            pass

        s2 = time.time()

        # ------------------------------------------------
        # 音频
        # 接受结果
        asr_list = []
        if a_ex:
            # 对音频切分，然后提取音频到临时文件及
            clip_list = self.audio_parser.audio_split(file_path, load_tmp_dir)

            for i, clip_dic in enumerate(clip_list):
                text = self.audio_parser.asr(input_audio=clip_dic['save_path'], language='auto')
                asr_list.append(
                    {
                        'start_time': str(clip_list[i]['start_time']),
                        'end_time': str(clip_list[i]['end_time']),
                        'text': text
                    }
                )

        s3 = time.time()

        result = {
            'AUDIO': asr_list,
            'VIDEO': img_list
        }
        # print('*' * 100)
        logger.info(f" 视频推理检索耗时: {str(s2-s1)} 秒")
        logger.info(f" 音频推理检索耗时: {str(s3-s2)} 秒")
        # print('*'*100)

        return result

    def clear_tmp_file(self, source_id: str):
        load_tmp_dir = os.path.join(self.kb_tmp_path, source_id)
        if not os.path.exists(load_tmp_dir):
            raise Exception('you cant clear an empty dir.')
        else:
            shutil.rmtree(load_tmp_dir)

    def load(self, file_path: str, source_id : str = None) -> Tuple[List[Chunk], List[List[float]]]:   # 一个是路径，另一个是embed，加载之后返回chunk和embeddings
        if source_id is None:
            source_id = str(uuid.uuid4())
        # 结果集合 chunk以及embed
        chunks = []
        embeds = []

        # 解析文档
        parser_dict = self.parser(file_path=file_path, source_id=source_id)
        s1 = time.time()

        # 对音频处理
        audio_list = parser_dict['AUDIO']
        for audio_item in audio_list:
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    chunk_type=ChunkType.AUDIO,
                    text=audio_item['text'],
                    time=audio_item['start_time'],
                    source_id=source_id,
                    source_type=file_path.split('.')[-1],
                    source_path=file_path       # 这个一定是来自于raw目录的
                )
            )
            embeds.append(
                self.embedding.embed_chunk(
                    text=audio_item['text'],
                    image=None,
                )
            )

        # 对图片做出处理
        video_list = parser_dict['VIDEO']
        for video_item in video_list:
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    chunk_type=ChunkType.VIDEO,
                    text=video_item['text'],
                    time=video_item['start_time'],
                    source_id=source_id,
                    source_type=file_path.split('.')[-1],
                    source_path=file_path
                )
            )
            embeds.append(
                self.embedding.embed_chunk(
                    text=video_item['text'],
                    image=video_item['image_path']
                )
            )
        s2 = time.time()
        logger.info(f" 向量化耗时: {str(s2 - s1)} 秒")

        self.clear_tmp_file(source_id=source_id)
        return chunks, embeds





if __name__ == "__main__":
    import config.mme_rag_config as cfg
    mme = MMeLoader()
    path = os.path.join(cfg.dataset_dir,'bb.mp4')
    #
    res = mme.load(path)

