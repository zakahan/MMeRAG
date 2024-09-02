import os
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Union, Tuple
import torch
from database.sqlite_base import SQLiteBase
from rag.elastic_vector import ElasticVector
from rag.embed import Embeddings, create_embeddings
from loader.mme_loader import MMeLoader
from rag.control import RAGController
from rag.llm.base_llm import BaseLLM
from config.mme_rag_config import KWARGS_EMBED_NAME, KB_RAW_PATH, ALLOWED_EXTENSIONS, CHECK_MODEL, FIRST_DOWNLOAD_TYPE
from config.mme_rag_logger import logger
from config.config_check import check_all_models
from fastapi import UploadFile, File
import warnings
warnings.filterwarnings("ignore")

# 采用依赖注入实现
class DependsResource:
    def __init__(self, **kwargs):
        logger.info('启动检查项： 1/5 模型检查 启动完毕 --------------------------')
        if CHECK_MODEL:
            check_all_models(FIRST_DOWNLOAD_TYPE)
        self.embedding = create_embeddings(emb_type=KWARGS_EMBED_NAME, **kwargs)
        logger.info('启动检查项： 2/5 embedding 启动完毕 -----------------------')
        # 加载解析过程 ： MMeLoader初始化
        self.mmeloader = MMeLoader(embedding_instance=self.embedding, **kwargs)
        logger.info('启动检查项： 3/5 mmeloader 启动完毕 -----------------------')
        # RAG过程 ：ES知识库初始化
        self.rag_controller = RAGController(embedding_instance=self.embedding, **kwargs)
        logger.info('启动检查项： 4/5 rag模块 启动完毕 --------------------------')
        # 其他CURD过程：sqlite数据库
        self.sqlbase = SQLiteBase()
        logger.info('启动检查项： 5/5 sql模块 启动完毕 --------------------------')
        # 固定目录
        self.raw_path = KB_RAW_PATH
        logger.info('系统依赖启动完毕. -----------------------------------------')

    def get_vector(self) -> ElasticVector:
        return self.rag_controller.get_es_vector()

    def get_loader(self) -> MMeLoader:
        return self.mmeloader

    def get_embeds(self) -> Embeddings:
        return self.embedding

    def get_base(self) -> SQLiteBase:
        return self.sqlbase

    def get_controller(self) -> RAGController:
        return self.rag_controller

    def get_llm(self) -> BaseLLM:
        return self.rag_controller.get_llm()

    def get_raw_path(self) -> str:
        return self.raw_path


# 唯一实例
depends_resource = DependsResource()


class BaseResponse(BaseModel):
    code: int = Field(200, description='API status code')
    msg: str = Field('success', description='API message')
    data: Any = Field(None, description='API data')

    class Config:
        json_schema_extra = {
            'example': {
                'code': 200,
                'msg': 'success'
            }
        }


# 防止路径名攻击
def validate_kb_name(collection_name: str) -> bool:
    # 检查是否包含预期外的字符或路径攻击关键字
    if any(char in collection_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '.']):
        return False
    else:
        return True


def human_readable_size_bytes(size_of_byte: Union[str, int]) -> str:
    # 如果参数是 str，那么转成 int
    if isinstance(size_of_byte, str):
        size_of_byte = int(size_of_byte)

    # 定义单位转换的阈值
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    index = 0
    while size_of_byte >= 1024 and index < len(units) - 1:
        size_of_byte /= 1024.0
        index += 1
    return f"{size_of_byte:.2f} {units[index]}"


def upload_file(
        base_raw_path: str,
        collection_name : str,
        file: UploadFile = File(...)
) -> Tuple[str, str]:
    allowed_extensions = ALLOWED_EXTENSIONS

    # 检查文件扩展名
    _, file_extension = os.path.splitext(file.filename)
    if file_extension.lower() not in allowed_extensions:
        raise ValueError("仅支持音频和视频文件类型")

    file_location = os.path.join(base_raw_path, collection_name, os.path.basename(file.filename))
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    return os.path.basename(file.filename), file_location
