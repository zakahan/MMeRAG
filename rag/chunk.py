from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Optional, Dict, List, Iterable, Union
from pydantic import Field, BaseModel
from enum import Enum
from pathlib import Path

class FileType(Enum):       # 暂时没用
    UNK = 'unknown'
    EMPTY = 'empty'
    # MS Office Types
    DOC = 'doc'
    DOCX = 'docx'
    XLS = 'xls'
    XLSX = 'xlsx'
    PPT = 'ppt'
    PPTX = 'pptx'
    MSG = 'msg'
    # Adobe Types
    PDF = 'pdf'
    # Image Types
    JPG = 'jpg'
    PNG = 'png'
    TIFF = 'tiff'
    BMP = 'bmp'
    HEIC = 'heic'
    # Plain Text Types
    EML = 'eml'
    RTF = 'rtf'
    TXT = 'txt'
    JSON = 'json'
    CSV = 'csv'
    TSV = 'tsv'
    # Markup Types
    HTML = 'html'
    XML = 'xml'
    MD = 'markdown'
    EPUB = 'ebup'
    RST = 'rst'
    ORG = 'org'
    # Compressed Types
    ZIP = 'zip'
    # Audio Files
    WAV = 'wav'
    MP3 = 'mp3'
    # Video Files
    MP4 = 'mp4'
    AVI = 'avi'


class ChunkType(Enum):
    # 文档
    # TEXT = 'TEXT'
    # IMAGE = 'IMAGE'
    # TABLE = 'TABLE'
    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'


def get_chunk_type(chunk_str):
    try:
        return ChunkType[chunk_str]
    except KeyError:
        return None


class Chunk(BaseModel):
    # 标识字段
    chunk_id: str
    chunk_type: ChunkType
    # 内容字段
    text: Optional[str] = Field(default=None, title='文本内容，如果不存在文本内容则此处为空')
    # image: Optional[Union[str, Path]] = Field(default=None, title='图片路径，不存在则为空')/
    # audio: Optional[Union[str, Path]] = Field(default=None, title='音频路径，不存在则为空，目前该字段无用，考虑可扩展性添加了本字段')
    # 记录字段
    time: Optional[str] = Field(default=None, title='该记录所在的原始视频、音频文件中对应的时间点，生成阶段可能使用到，单位是毫秒')
    # 来源字段，代表原生文档的信息，存储在知识库的raw_file中
    source_id: str
    source_type: Optional[str] = Field(default='unknown', title='存储来源文件的类型')
    source_path: Optional[str] = Field(default=None, title='存储来源文件所在的本地路径-raw关联')




if __name__ == '__main__':
    # import time
    # x = Document(
    #     text='8581330',
    #     metadata={
    #         'source': 'ack',
    #         'time': time.time()
    #     }
    # )
    #
    # print(x)
    # print(dict(x))

    import numpy as np
    arr = np.random.rand(1024).astype(np.float64)
    element_size = arr.itemsize

    size_in_bytes = arr.nbytes

    print(f"The array occupies {size_in_bytes} bytes")