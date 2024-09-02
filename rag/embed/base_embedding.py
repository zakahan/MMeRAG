from abc import ABC, abstractmethod
from typing import List, Union
from pathlib import Path
import numpy as np  # cv


class Embeddings(ABC):
    """Interface for embedding models."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        raise NotImplementedError

    @abstractmethod
    def embed_chunks(self, texts: List[Union[str,None]],  images: List[Union[str, None]]) -> List[List[float]]:
        """ Embed chunks. """
        raise NotImplementedError

    @abstractmethod
    def embed_chunk(self, text: Union[str, None], image: Union[str, None]) -> List[float]:
        raise NotImplementedError


    @abstractmethod
    def get_dim(self):
        raise NotImplementedError