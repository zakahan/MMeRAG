from rag.embed.base_embedding import Embeddings
from rag.embed.vbge_embed import VBGEEmbeddings


def create_embeddings(emb_type: str, **kwargs) -> Embeddings:
    emb_factory = {
        'VBGEEmbedding': VBGEEmbeddings
    }
    if emb_type not in emb_factory:
        raise ValueError(f'Unknown Embedding type: {emb_type}')
    return emb_factory[emb_type](**kwargs)

