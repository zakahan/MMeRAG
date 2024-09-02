from config import mme_rag_config as cfg
VERSION = '1.0.0'


args = {
    'num_candidates' : 100,
    'top_k':10,
    'api_key': cfg.CHAT_API_KEY,
    'model_id': cfg.CHAT_MODEL_ID
}

back_host = '127.0.0.1'
back_port = 8000
back_url = f'{back_host}:{str(back_port)}'

front_host = '0.0.0.0'
front_prot = 8501
