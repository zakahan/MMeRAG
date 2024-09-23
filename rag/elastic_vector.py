import uuid
from typing import Any, List, Tuple, Dict, Set
from elasticsearch import Elasticsearch
from pydantic import BaseModel, Field
from rag.chunk import Chunk
from config.mme_rag_config import ELASTIC_PASSWORD, CA_CERTS, KWARGS_DIM, KWARGS_SIMILARITY_TYPE
from config.mme_rag_logger import logger


class ElasticConfig(BaseModel):
    host: str = Field(default='https://localhost:9200', description='本地情况下')  # 注意是https而不是http
    ca_certs_path: str = Field(default=CA_CERTS, description='ca证书所在路径')
    basic_auth: Tuple[str, str] = Field(default=('elastic', ELASTIC_PASSWORD), description='设置密码')


class ElasticVector:
    def __init__(
            self,
            config: ElasticConfig,
            **kwargs
    ):
        # 初始化一些信息
        self.dim = kwargs.get('dim', KWARGS_DIM)
        self.similarity_type = kwargs.get('similarity_type', KWARGS_SIMILARITY_TYPE)
        # 连接客户端
        self.client = self.init_client(config)
        logger.info("ElasticVector 初始化完成")
        # 初始化collection names
        # self._collection_name = collection_name
        self._collection_set: Set = set()
        self.upgrade_set()  # 加载collection_name_list
        logger.info(f'collection set: {self._collection_set}')

    def init_client(
            self,
            config: ElasticConfig
    ):
        # 初始化ES客户端
        client = Elasticsearch(
            config.host,
            basic_auth=config.basic_auth,
            verify_certs=True,
            ca_certs=config.ca_certs_path
        )
        # 测试一下es的链接
        try:
            # 调用Elasticsearch的_cat/health API
            response = client.cat.health(v=True)
            logger.info("ElasticVector 连接成功！集群健康状态：")
            logger.info(response)
        except Exception as e:
            logger.info("ElasticVector 连接失败，错误信息：")
            logger.info(e)
            print(e)
            raise Exception("ElasticVector 连接失败，请确定配置信息是否正确。")
        return client

    def get_type(self) -> str:
        # 获得当前类型
        return 'elasticsearch'

    def __repr__(self):
        return f"ElasticSearch kb with {len(self._collection_set)} set."

    def collection_exist(self, collection_name: str):
        # return the result of is collection_name in self._collection_set
        return collection_name in self._collection_set

    def show_set(self) -> Set:
        self.upgrade_set()
        return self._collection_set

    def show_detail(self, collection_name):
        count_result = self.client.count(index=collection_name)
        stats_info = self.client.indices.stats(index=collection_name, metric='store')
        return count_result['count'], stats_info['indices'][collection_name]['primaries']['store']['size_in_bytes']

    def upgrade_set(self) -> None:
        """
            更新collection set，
            其实好像没必要专门做这个东西，有点脱裤子放屁了，每次直接访问ES查找就好了，
        """
        response = self.client.cat.indices(format='json')
        collection_list = [index['index'] for index in response]
        self._collection_set = set(collection_list)

    def get_settings(self) -> Dict:
        # 获取setting
        settings = {
            'index': {
                'number_of_shards': 1,  # 分片数量
                'number_of_replicas': 0,  # 副本数量
                'similarity': {
                    'custom_bm25': {
                        'type': 'BM25',
                        'k1': 1.2,
                        'b': 0.75
                    }
                }
            }  # end-of-index
        }
        return settings

    def get_mappings(self) -> Dict:
        mappings = {
            "properties": {
                "chunk_id": {
                    "type": "keyword",
                    "index": True,
                },
                "content": {
                    "type": "text",
                    "similarity": "custom_bm25",  # 使用自定义的BM25相似度评分函数
                    "index": True,
                    "analyzer": "standard",
                    "search_analyzer": "standard"
                },
                "chunk_type": {
                    "type": "keyword",
                    "index": False,
                },
                "time": {
                    "type": "keyword",
                    "index": False,  # 不索引title，仅用于存储
                },
                "source_id": {
                    "type": "keyword",
                    "index": True  #
                },
                "source_type": {
                    "type": "keyword",
                    "index": False,  # 不索引source，仅用于存储
                },
                "source_path": {
                    "type": "keyword",
                    "index": False,  # 不索引source，仅用于存储
                },
                "embedding": {
                    "type": "dense_vector",  # 向量字段的数据类型
                    "dims": 1024,  # 向量的维度
                    "index": True,  # 向量需要被索引
                    "similarity": "l2_norm"  # 使用点积相似度评分函数
                }
            }
        }
        return mappings

    def response2chunk(self, response_dict: Dict) -> Chunk:
        return Chunk(
            chunk_id=response_dict['chunk_id'],
            text=response_dict['content'],
            chunk_type=response_dict['chunk_type'],
            time=response_dict['time'],
            source_id=response_dict['source_id'],
            source_type=response_dict['source_type'],
            source_path=response_dict['source_path'],
        )

    def create(self, collection_name: str) -> None:
        # fixme: 为了支持并发处理，需要加上锁
        # 首先判断是否已经存在这个名称了
        if collection_name in self._collection_set:
            msg = f'ES_{collection_name} 已经存在，无法重复创建'
            raise Exception(msg)

        # 创建index
        mappings = self.get_mappings()
        settings = self.get_settings()

        self.client.indices.create(index=collection_name, mappings=mappings, settings=settings)
        msg = f'ES_{collection_name} 创建成功'
        logger.info(msg)
        # 将其添加到set中
        self.upgrade_set()  # 保存set
        return

    def copy(self, source_collection_name: str, dest_collection_name: str) -> None:
        # 首先判断是否已经存在这个名称了
        if source_collection_name not in self._collection_set:
            raise Exception(f'无法执行复制，原知识库{source_collection_name}不存在')
        if dest_collection_name not in self._collection_set:
            raise Exception(f'无法执行复制，新知识库{dest_collection_name}未创建')

        # 从原知识库复制数据到新的知识库
        res = self.client.reindex(body={
            "source": {
                "index": source_collection_name
            },
            "dest": {
                "index": dest_collection_name
            }
        }, request_timeout=60)
        self.upgrade_set()

    def add_chunks(self, collection_name: str, chunks: List[Chunk], embeddings: List[List[float]]) -> List[
        str]:
        # 检查是否存在这个collection_name
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')
        # doc_ids
        doc_ids = []
        # 检查documents和embedding长度是否一致
        if not len(chunks) == len(embeddings):
            raise Exception(f'chunks和embeddings的长度不一致，分别为{len(chunks)}和{len(embeddings)}，不符合要求')

        # 1）整理待插入的字典信息
        for chunk, embedding in zip(chunks, embeddings):
            doc = {
                'chunk_id': chunk.chunk_id,
                'content': chunk.text,
                'chunk_type': chunk.chunk_type.value,
                'time': chunk.time,
                'source_id':chunk.source_id,
                'source_type': chunk.source_type,
                'source_path': chunk.source_path,
                'embedding': embedding,
            }
            response = self.client.index(
                index=collection_name,
                document=doc,
                id=chunk.chunk_id
            )
            # logger.debug(str(response))
            doc_ids.append(chunk.chunk_id)

        return doc_ids

    def search_text_by_id(self, collection_name: str, _id: str) -> Chunk:
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')

        # 需要再组装一次

        response = self.client.get(index=collection_name, id=_id)
        logger.info(f"完成一次基于id的搜索： response: {str(response)}")
        response_dict = dict(response)['_source']
        chunk = self.response2chunk(response_dict=response_dict)
        return chunk

    def search_by_vector(
            self,
            collection_name: str,
            query_vector: List[float],
            top_k: int = 1,
            num_candidates: int = 100
    )-> List[Tuple[Chunk, Any]]:
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')
        # 采用近似kNN检索
        knn_query = {
            'knn': {
                'field': 'embedding',
                'query_vector': query_vector,
                'k': top_k,
                'num_candidates': num_candidates
            },
            'fields': [
                'embedding',
                'content'
            ]
        }
        response = self.client.search(index=collection_name, body=knn_query)
        result_list = []
        result_dicts = dict(response)['hits']['hits']
        for item_dict in result_dicts:
            response_dict = item_dict['_source']
            chunk = self.response2chunk(response_dict=response_dict)
            score = item_dict['_score']
            result_list.append(
                (chunk, score)
            )
            pass

        return result_list

    def search_by_bm25(self, collection_name: str, query: str, top_k: int) -> List[Tuple[Chunk, Any]]:
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')
        search_results = []
        bm25_query = {
            'size': top_k,
            'query': {
                'match': {
                    'content': query
                }
            }
        }
        response = self.client.search(index=collection_name, body=bm25_query)
        result_list = []
        result_dicts = dict(response)['hits']['hits']
        for item_dict in result_dicts:
            response_dict = item_dict['_source']
            chunk = self.response2chunk(response_dict=response_dict)
            score = item_dict['_score']
            result_list.append(
                (chunk, score)
            )
            pass
        return result_list

    def search_by_mix(
            self,
            collection_name: str,
            query_vector: List[float],
            query: str,
            top_k: int = 10,
            num_candidates: int = 100
    ):  # 新增
        # 混合检索操作
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')
        v_results = self.search_by_vector(collection_name, query_vector=query_vector, top_k=top_k,
                                          num_candidates=num_candidates)
        b_results = self.search_by_bm25(collection_name, query=query, top_k=top_k)
        # todo 得试验之后考虑一下怎么综合

    def delete_by_ids(self, collection_name: str, ids: List[str]) -> bool:
        # 细粒度的，这个是针对chunk级的删除
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')
        if ids is None:
            return False
        # 这个大概得逐个删除吧，这次就不能批量检查是否能删除之类的了...欸？那我可以维护一个id表，额
        # 不过那样大概也没有很重要，因为...算了
        for i, _id in enumerate(ids):
            try:
                response = self.client.delete(index=collection_name, id=_id)
                logger.info(f'添加成功 返回信息 {response}')
            except Exception as e:
                logger.info(f'遇到了错误的id，无法进行删除。 目前已删除 {i}个id，无法删除的id为{_id}')
                return False
            pass
        return True

    def delete_by_source(self, collection_name: str, source_id: str):
        # 中等粒度的删除，针对文档级别进行删除
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')

        response = self.client.delete_by_query(index=collection_name, body={
            "query": {
                "term": {
                    "source_id": source_id
                }
            }
        })
        logger.info(f'已删除{collection_name}库中所有 source_id为 {source_id}的文档')
        # logger.debug(str(response))
        pass

    def drop_collection(self, collection_name: str) -> str:
        # 删除某个知识库
        if collection_name not in self._collection_set:
            raise Exception(f'collection_nmae 错误，知识库列表中，不存在{collection_name} ')
        self.client.indices.delete(index=collection_name)
        logger.info(f'已成功删除知识库 {collection_name}')
        self.upgrade_set()
        return collection_name

    def drop_all_collection(self) -> List[str]:
        # 删除所有知识库
        res = []
        response = self.client.cat.indices(format='json')
        for index in response:
            self.client.indices.delete(index=index['index'])
            logger.info(f'已成功删除知识库 {index["index"]}')
            res.append(index['index'])
            pass
        self.upgrade_set()
        return res


if __name__ == "__main__":
    esconfig = ElasticConfig()
    print(esconfig)
    esvector = ElasticVector(config=esconfig)
    esvector.drop_all_collection()

