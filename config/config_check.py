import os

from config.mme_rag_config import SENSE_VOICE_MODEL_PATH, SENSE_VOICE_VAD_MODEL_PATH, vis_m3_path, vis_cfg_path, \
    reranker_path, DOWNLOAD_MODEL_BY_MIRROR, FIRST_DOWNLOAD_TYPE

if DOWNLOAD_MODEL_BY_MIRROR:
    # 注意os.environ得在import huggingface库相关语句之前执行。
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import modelscope as ms
import huggingface_hub as hf
# https://huggingface.co/BAAI/bge-visualized/resolve/main/Visualized_m3.pth?download=true
from config.mme_rag_logger import logger



def is_non_empty_directory(path: str) -> bool:
    # 检查路径是否存在
    if not os.path.exists(path):
        return False
    # 检查路径是否为文件夹
    if not os.path.isdir(path):
        return False
    # 检查文件夹是否为空
    if not os.listdir(path):  # os.listdir(path) 返回文件夹中的所有文件和子文件夹列表
        return False
    return True


def download_model(model_path: str, model_name: str, file_name, download_type: str='hf'):
    logger.info(f'正在下载：{model_name}.....')
    if download_type == 'ms':
        ms.snapshot_download(model_name, local_dir=model_path)
    else:
        if file_name is None:
            hf.snapshot_download(model_name, local_dir=model_path)
        else:
            hf.hf_hub_download(repo_id=model_name, filename=file_name, local_dir=model_path)

def check_all_models(first_download_by_this: str=FIRST_DOWNLOAD_TYPE):
    # todo 需要加上个try -catch
    models = [
        {
            'path':SENSE_VOICE_MODEL_PATH,
            'ms': 'iic/SenseVoiceSmall',
            'hf': 'FunAudioLLM/SenseVoiceSmall',
            'file_name': None
        },
        {
            'path': SENSE_VOICE_VAD_MODEL_PATH,
            'ms': 'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
            'hf' : 'funasr/fsmn-vad',
            'file_name': None
        },
        {
            'path' : os.path.dirname(vis_m3_path),      # 必须
            'ms' : None,
            'hf' : 'BAAI/bge-visualized',
            'file_name': 'Visualized_m3.pth'
        },
        {
            'path' : vis_cfg_path,
            'ms': 'Xorbits/bge-m3',
            'hf': 'BAAI/bge-m3',
            'file_name': None
        },
        {
            'path': reranker_path,
            'ms': 'AI-ModelScope/bge-reranker-v2-m3',
            'hf': 'BAAI/bge-reranker-v2-m3',
            'file_name' : None
        }

    ]
    first_id, second_id = 'ms', 'hf'
    for model in models:
        if first_download_by_this == 'hf':
            first_id, second_id = second_id, first_id
        if not is_non_empty_directory(model['path']):       # 就是如果没有这个的话
            os.makedirs(model['path'],exist_ok=True)
            if model[first_id] is not None:
                download_model(model['path'], model[first_id], model['file_name'], download_type=first_id)
            else:       # 第一种选择里面没有这个模型的话
                download_model(model['path'], model[second_id], model['file_name'], download_type=second_id)
        else:
            print('=' * 20 + f'{model[first_id] if model[first_id] is not None else model[second_id]} 路径存在，但是请你确定他真的存在' + '=' * 20)

if __name__ == '__main__':
    # check_model_weights()
    file_path = '/mnt/e/ModelFiles/BAAI/Visualized-BGE2'
    if not is_non_empty_directory(file_path):
        print('新建文件夹')
        os.makedirs(file_path, exist_ok=True)
    hf.hf_hub_download(repo_id='BAAI/bge-visualized', filename='Visualized_m3.pth', local_dir=r'/mnt/e/ModelFiles/BAAI/Visualized-BGE2')