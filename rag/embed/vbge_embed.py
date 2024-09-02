import torch
from third_party.FlagEmbedding.visual.modeling import Visualized_BGE
from rag.embed.base_embedding import Embeddings
from typing import List, Union

from config.mme_rag_config import vis_cfg_path, vis_m3_path


class VBGEEmbeddings(Embeddings):
    def __init__(self, device: str = 'cuda:0'):
        self.device = torch.device(device)  #
        self.d = 1024
        model_weight_path = vis_m3_path
        model_config_location = vis_cfg_path
        # 初始化模型并指定设备
        self._model = Visualized_BGE(model_name_bge="BAAI/bge-m3",
                                     model_weight=model_weight_path,
                                     model_config_location=model_config_location
                                     ).to(self.device)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        self._model.eval()
        with torch.no_grad():
            for text in texts:
                emb = self._model.encode(text=text, device=self.device).tolist()[0]
                embeddings.append(emb)
                pass
        return embeddings

    def embed_chunks(self, texts: List[Union[str, None]], images: List[Union[str, None]]) -> List[List[float]]:
        # 让紧密度更近一部
        embeddings = []
        self._model.eval()
        with torch.no_grad():
            for uri, text in zip(images, texts):
                emb = self._model.encode(image=uri, text=text, device=self.device).tolist()[0]
                embeddings.append(emb)
                pass

        return embeddings

    def get_dim(self):
        return 1024

    def embed_chunk(self, text: Union[str, None], image: Union[str, None]) -> List[float]:
        self._model.eval()
        with torch.no_grad():
            text = text.replace("\n", " ")
            embedding = self._model.encode(text=text, image=image, device=self.device).tolist()[0]
        return embedding

    def embed_query(self, text: str) -> List[float]:
        self._model.eval()
        with torch.no_grad():
            text = text.replace("\n", " ")
            embedding = self._model.encode(text=text, device=self.device).tolist()[0]
        return embedding


if __name__ == "__main__":
    import os
    import time

    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    my_embeddings = VBGEEmbeddings(device='cuda:0')

    image_query = r'C:\MyScripts\Indie\MMeRAG\rag\FlagEmbedding\visual\imgs\cir_candi_1.png'
    print(f"Model is running on: {my_embeddings.device}")

    s = time.time()
    for i in range(0, 50):
        emb_q = my_embeddings.embed_chunks(images=[image_query], texts=["在世界中心呼唤爱"])
        pass
    r = time.time()
    # print(emb_q)
    print(f"用时如下：{r - s}")
