import warnings

from fastapi import Body
from fastapi import Depends

# -------------------
from rag.embed import Embeddings
from rag.elastic_vector import ElasticVector
from rag.control import RAGController
from rag.llm.base_llm import BaseLLM
from apis.utils import depends_resource, BaseResponse
warnings.filterwarnings("ignore")
from config.server_config import args

# 设置日志
from config.mme_rag_logger import logger



# 这里处理的都是RAG业务相关的，主要涉及检索、问答、重排序等
# 常规检索
def vector_search(
        collection_name: str = Body(..., description="数据库名称"),
        text: str = Body(..., description="等待向量化的文本"),
        top_k: int = Body(args['top_k'], description="返回多少个结果"),
        num_candidates: int = Body(args['num_candidates'], description="候选数量"),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        embedding: Embeddings = Depends(depends_resource.get_embeds)
) -> BaseResponse:
    vector = embedding.embed_query(text)
    try:
        result = elastic_vector.search_by_vector(
            collection_name=collection_name,
            query_vector=vector,
            top_k=top_k,
            num_candidates=num_candidates
        )
        return BaseResponse(
            code=200,
            msg='检索成功',
            data={
                'data': result
            }
        )
    except Exception as e:
        logger.info(f"检索过程遇到了问题： Exception {str(e)}")
        return BaseResponse(
            code=500,
            msg='检索过程中出现了意外',
            data={
                'exception': str(e)
            }
        )

    pass


# bm25检索
def bm25_search(
        collection_name: str = Body(..., description="数据库名称"),
        text: str = Body(..., description="等待向量化的文本"),
        top_k: int = Body(args['top_k'], description="返回多少个结果"),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
) -> BaseResponse:
    try:
        result = elastic_vector.search_by_bm25(
            collection_name=collection_name,
            query=text,
            top_k=top_k,
        )
        return BaseResponse(
            code=200,
            msg='检索成功',
            data={
                'data': result
            }
        )
    except Exception as e:
        logger.info(f"检索过程遇到了问题： Exception {str(e)}")
        return BaseResponse(
            code=500,
            msg='检索过程中出现了意外',
            data={
                'exception': str(e)
            }
        )


# 混合检索
def hybrid_search(
        collection_name: str = Body(..., description="数据库名称"),
        text: str = Body(..., description="等待向量化的文本"),
        top_k: int = Body(args['top_k'], description="返回多少个结果"),
        num_candidates: int = Body(args['num_candidates'], description="候选数量"),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        embedding: Embeddings = Depends(depends_resource.get_embeds)
) -> BaseResponse:
    # 容我仔细思考
    pass


# --------------------------------
# 大模型问答 -----------------------
# 1 简单rag问答
def naive_rag_qa(
        collection_name: str = Body(..., description="数据库名称"),
        query: str = Body(..., description="问答文本"),
        top_k: int = Body(args['top_k'], description="返回多少个结果"),
        api_key: str = Body(args['api_key'], description='大模型的api key'),
        model_id: str = Body(args['model_id'], description='模型名称'),
        rag_controller: RAGController = Depends(depends_resource.get_controller),
) -> BaseResponse:
    try:
        llm_ans, ref_ans = rag_controller.naive_rag(
            collection_name=collection_name,
            user_question=query,
            top_k=top_k,
            api_key=api_key,
            model_id=model_id
        )
        return BaseResponse(
            code=200,
            msg='问答返回',
            data={
                'llm_ans': llm_ans,
                'ref_ans': ref_ans
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg='问答过程出现了意外',
            data={
                'exception': str(e)
            }
        )
    pass


def advanced_rag_qa(
        collection_name: str = Body(..., description="数据库名称"),
        query: str = Body(..., description="问答文本"),
        top_k: int = Body(args['top_k'], description="返回多少个结果"),
        num_candidates: int = Body(args['num_candidates'], description='候选数量'),
        is_rewritten: bool = Body(False, description='是否进行问题重生成'),
        is_rerank: bool = Body(False, description='是否进行重排序'),
        search_method: str = Body('search_by_vector', description='搜索方法'),
        api_key: str = Body(args['api_key'], description='大模型的api key'),
        model_id: str = Body(args['model_id'], description='模型名称'),
        rag_controller: RAGController = Depends(depends_resource.get_controller),
) -> BaseResponse:
    try:
        llm_ans, ref_ans = rag_controller.advanced_rag(
            collection_name=collection_name,
            user_question=query,
            num_candidates=num_candidates,
            top_k=top_k,
            is_rewritten=is_rewritten,
            is_rerank=is_rerank,
            search_method=search_method,
            api_key=api_key,
            model_id=model_id
        )
        return BaseResponse(
            code=200,
            msg='问答返回',
            data={
                'llm_ans': llm_ans,
                'ref_ans': ref_ans
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg='问答过程出现了意外',
            data={
                'exception': str(e)
            }
        )


def query_decompose_rag_qa(
        collection_name: str = Body(..., description="数据库名称"),
        query: str = Body(..., description="问答文本"),
        top_k: int = Body(args['top_k'], description="返回多少个结果"),
        num_candidates: int = Body(args['num_candidates'], description='候选数量'),
        is_rerank: bool = Body(False, description='是否进行重排序'),
        search_method: str = Body('search_by_vector', description='搜索方法'),
        api_key: str = Body(args['api_key'], description='大模型的api key'),
        model_id: str = Body(args['model_id'], description='模型名称'),
        rag_controller: RAGController = Depends(depends_resource.get_controller),
) -> BaseResponse:
    try:
        llm_ans, ref_chunks, final_qa= rag_controller.query_decompose_rag(
            collection_name=collection_name,
            user_question=query,
            num_candidates=num_candidates,
            top_k=top_k,
            is_rerank=is_rerank,
            search_method=search_method,
            api_key=api_key,
            model_id=model_id
        )

        # 对ref_chunks做处理
        chunk_list = []
        for i, (k, chunk) in enumerate(ref_chunks.items()):
            chunk_list.append(chunk)

        return BaseResponse(
            code=200,
            msg='问答返回',
            data={
                'llm_ans': llm_ans,
                'ref_ans': chunk_list,
                'mid_qa': final_qa
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg='问答过程出现了意外',
            data={
                'exception': str(e)
            }
        )


def chat_qa(
        query: str = Body(..., description='问答文本'),
        api_key: str = Body(args['api_key'], description='大模型的api key'),
        model_id: str = Body(args['model_id'], description='模型名称'),
        llm : BaseLLM = Depends(depends_resource.get_llm),
) -> BaseResponse:
    try:
        answer = llm.chat_base(
            content=query,
            model_source=model_id,
            api_key=api_key
        )
        return BaseResponse(
            code=200,
            msg='回复成功',
            data={
                'llm_ans' : answer
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg='出现了意外的错误',
            data={
                'exception' : str(e)
            }
        )

if __name__ == "__main__":
    print('hello')
