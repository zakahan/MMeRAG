import torch
import numpy as np
from typing import List
from rag.chunk import Chunk
from third_party.FlagEmbedding import FlagReranker


class BGEReranker:
    def __init__(self, model_name_or_path: str, device: str):
        self.reranker_model = FlagReranker(model_name_or_path, device=device)

        pass

    def reranker_chunks(self, query: str, chunks: List[Chunk]) -> List[Chunk]:
        text_list = [(query, chunk.text) for chunk in chunks]
        scores = self.reranker_model.compute_score(text_list)
        sorted_chunk_score = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        sorted_chunk_score = [chunk for score, chunk in sorted_chunk_score]
        return sorted_chunk_score


if __name__ == "__main__":
    pass