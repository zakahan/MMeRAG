import os

PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))
dataset_dir = None  # 'this is a path for test'

# -------------------------------------------------
MODEL_PATH = os.getenv('MME_MODEL_PATH') if os.getenv('MME_MODEL_PATH') is not None else os.path.join(PROJECT_PATH, 'models')
SENSE_VOICE_MODEL_PATH = os.path.join(MODEL_PATH, 'iic', 'SenseVoiceSmall')
SENSE_VOICE_VAD_MODEL_PATH = os.path.join(MODEL_PATH, 'iic', 'speech_fsmn_vad_zh-cn-16k-common-pytorch')
vis_m3_path = os.path.join(MODEL_PATH, 'BAAI', 'Visualized-BGE', 'Visualized_m3.pth')
vis_cfg_path = os.path.join(MODEL_PATH, 'BAAI', 'bge-m3')
reranker_path = os.path.join(MODEL_PATH, 'BAAI', 'bge-reranker-v2-m3')

# -------------------------------------------------
KB_BASE_PATH = os.getenv('MME_KB_PATH') if os.getenv('MME_KB_PATH') is not None else os.path.join(PROJECT_PATH, 'kb')
KB_CONTENT_PATH = os.path.join(KB_BASE_PATH, 'content')
KB_RAW_PATH = os.path.join(KB_BASE_PATH, 'raw')
KB_TMP_PATH = os.path.join(KB_BASE_PATH, 'tmp')

ALLOWED_EXTENSIONS = ['.mp4']
# 上面两个全都改成wsl中的路径

# 加载模型相关 主要关联部分为config.config_check.py
CHECK_MODEL = True             # 是否检查模型加载情况，如果选择False就不需要每次都检查了
DOWNLOAD_MODEL_BY_MIRROR = True # 是否要配置hf-mirror
FIRST_DOWNLOAD_TYPE = 'ms'      # 优先从modelscope里下载

# 关于elastic search
CA_CERTS=os.path.join(PROJECT_PATH, 'http_ca.crt')    # "/mnt/c/MyScripts/Indie/MMeRAG/http_ca.crt"  # 替换为您的CA证书路径
ELASTIC_PASSWORD = os.getenv('ELASTIC_PASSWORD')

# 这些都是在配置默认值，实际上接口可以选
CHAT_API_KEY = os.getenv('CHAT_API_KEY')
CHAT_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
CHAT_MODEL_ID = 'glm-4-flash'
CHAT_LLM_TYPE = 'ChatAPILLM'


# kwargs
KWARGS_DIM: int = 1024
KWARGS_SIMILARITY_TYPE: str = 'l2_norm'
KWARGS_SPACE_SECOND: int = 10
KWARGS_HIS_THRESHOLD: float = 0.4
KWARGS_SAMPLE_PLAN:str = 'only_change'
KWARGS_EMBED_NAME = 'VBGEEmbedding'        # 配置的向量化方案



if __name__ == "__main__":
    print(os.path.dirname(os.path.dirname(__file__)))