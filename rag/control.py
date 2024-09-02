'''
controller的作用:
    顾名思义，控制器，控制的是信息的流向和流程的进行，用来控制rag过程的
    首先思考一个基本的rag过程，
    检索文档-> k个文档 -> 重排序 -> k个文档 -> 组织好条目，传输给大模型 -> 大模型 -> 答案
    这里有很多问题，如何检索，采用哪种检索方案？hybrid？ vector？ 还是bm25？这个需要考虑，是一个分歧点，一个参数....
    Q：那么为什么不直接在api里做这些事情呢？
    A: 因为我在考虑有循环寻找等复杂操作的可能性，比如self.rag等，需要涉及到多个流程交互的，我怀疑会在rag这个流程上多出来一层抽象，这个就是controller的作用和意义所在了
    但是，类内和类外的这个关系我还是没想好，就是还有一种可能性，我只把 controller暴露给他，额，不行，这个好像不行，肯定还得暴露一下ElasticSearch，不然的话通用性堪忧

    说白了，就是rag的这个检索生成的流程，可能有多种，所有要多抽象一层。

'''
import re
import torch
from typing import Tuple, List, Any, Dict
from rag.elastic_vector import ElasticVector, ElasticConfig
from rag.embed import create_embeddings, Embeddings
from rag.llm import BaseLLM, create_llms
from rag.llm.prompt_config import *
from rag.reranker.bge_reranker import BGEReranker
from rag.chunk import Chunk, ChunkType
from config.mme_rag_config import reranker_path, CHAT_URL, CHAT_API_KEY, CHAT_MODEL_ID
from config.mme_rag_config import KWARGS_EMBED_NAME, CHAT_LLM_TYPE
from config.mme_rag_logger import logger


# -----------------------------------
# 正则提取
def get_query_list(text: str) -> List[str]:
    # query字符串转list
    # 使用正则表达式匹配非数字开始直到换行符的内容
    pattern = r'\d+\.(.*?)(?=\n|$)'  # 使用正则表达式匹配以数字开始直到换行符的内容
    # 使用 findall 方法找到所有匹配项
    matches = re.findall(pattern, text)
    # 去除matches里所有字符串的前后空格
    query_list = [match.strip() for match in matches]
    return query_list


def reference_extract(text: str) -> Tuple[str, List[int]]:
    # 提取文本中不含方括号的部分
    text_without_brackets = re.sub(r'\[\d+]', '', text)

    # 提取方括号内的数字
    numbers_in_brackets = re.findall(r'\[\d+]', text)
    numbers_only = [int(num.strip('[]')) for num in numbers_in_brackets]
    return text_without_brackets.strip(), numbers_only


class RAGController:
    def __init__(self, **kwargs):
        """
            考虑：
            1. reranker
            2. query_rewrite
            3. summary？
        """
        # 配置embedding
        embed_name = kwargs.get('embed_name', KWARGS_EMBED_NAME)
        embedding_instance = kwargs.get('embedding_instance', None)  # 用来捕获embedding实例，如果没有，后续会创造
        device = kwargs.get('device', 'cuda:0' if torch.cuda.is_available() else 'cpu')
        # 配置embedding
        if embedding_instance is None:
            # 若为空 则创建
            self.embedding = create_embeddings(embed_name, device=device)
        else:
            self.embedding = embedding_instance

        # 配置es知识库
        self.elastic_config = ElasticConfig()
        self.elastic_vector = ElasticVector(
            config=self.elastic_config,
            **kwargs
        )
        # 配置reranker
        self.reranker = BGEReranker(reranker_path, device=device)

        # 配置大模型
        llm_type = kwargs.get('llm_type', CHAT_LLM_TYPE)
        llm_chat_url = kwargs.get('llm_chat_url', CHAT_URL)
        self.llm = create_llms(
            llm_type=llm_type,
            url=llm_chat_url
        )
        pass

    def get_es_vector(self) -> ElasticVector:
        return self.elastic_vector

    def get_llm(self) -> BaseLLM:
        return self.llm

    def get_embeddings(self) -> Embeddings:
        return self.embedding

    def get_reranker(self) -> BGEReranker:
        # 这个得改一下，最好reranker也做一个类（好像也没那么有所谓）
        return self.reranker

    def retrieval(
            self,
            question: str,
            collection_name: str,
            search_method: str = 'search_by_vector',
            top_k: int = 10,
            num_candidates: int = 100,
    ) -> List[Chunk]:

        if search_method == 'search_by_vector':
            # 问题向量化
            query_vector = self.embedding.embed_query(text=question)
            # 向量检索
            ans_list = self.elastic_vector.search_by_vector(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k
            )
        elif search_method == 'search_by_bm25':
            ans_list = self.elastic_vector.search_by_bm25(
                collection_name=collection_name,
                query=question,
                top_k=top_k
            )
        elif search_method == 'search_by_mix':
            # 问题向量化
            query_vector = self.embedding.embed_query(text=question)
            ans_list = self.elastic_vector.search_by_mix(
                collection_name=collection_name,
                query_vector=query_vector,
                query=question,
                top_k=top_k,
                num_candidates=num_candidates
            )
        else:
            raise ValueError(
                f'unknown search method {search_method}, the value could only be search_by_vector, search_by_bm25 and search_by_mix')

        results = [chunk for chunk, score in ans_list]
        return results

    def rerank(self, query:str, answer_chunks: List[Chunk]) -> List[Chunk]:
        return self.reranker.reranker_chunks(query, chunks=answer_chunks)

    def naive_rag(
            self, collection_name: str, user_question: str, top_k: int,
            api_key: str = CHAT_API_KEY,
            model_id: str = CHAT_MODEL_ID
        ) -> Tuple[str, List[Chunk]]:
        """
        原始rag流程：
        用户提问 -> 检索器(纯向量检索) -> 简单整理一下 -> LLM（生成器） -> 回答
        仅作为一个非常普通的演示使用，基本上派不上用场
        """

        # 检索器检索
        ans_list = self.retrieval(
            collection_name=collection_name, question=user_question, top_k=top_k)  # 使用默认的向量检索

        # chunk整理
        retrieval_answer = ''
        for i, chunk in enumerate(ans_list):
            retrieval_answer += f"{str(i)}.{chunk.text}+\n"

        # 生成回答
        llm_answer = self.llm.chat_in_template(
            prompt=rag_base_prompt, message=retrieval_answer, question=user_question,
            model_source=model_id, api_key=api_key
        )
        return llm_answer, ans_list

    def advanced_rag(
            self,
            collection_name: str,
            user_question: str,
            num_candidates: int = 100,
            top_k: int = 10,
            is_rewritten: bool = False,
            is_rerank: bool = False,
            search_method: str = 'search_by_vector',
            api_key: str = CHAT_API_KEY,
            model_id: str = CHAT_MODEL_ID
    ) -> Tuple[str, List[Chunk]]:
        """
        高级RAG：
        全流程如下：
        用户提问 -> 问题重生成 -> 检索器（选择检索方案） -> 重排序/summary -> 整理结果 -> LLM（生成器） -> 回答问题
        但这个其实还是没啥用，因为没有针对chunk做优化，考虑时间戳等信息，问题也要考虑带有依据的回答之类的
        """
        # 问题重生成
        if is_rewritten:
            user_question = self.llm.chat_in_template(
                prompt=query_rewritten_prompt, question=user_question
            )

        ans_list = self.retrieval(
            question=user_question,
            collection_name=collection_name,
            search_method=search_method,
            top_k=top_k,
            num_candidates=num_candidates
        )

        # 重排序
        if is_rerank:
            ans_list = self.reranker.reranker_chunks(query=user_question, chunks=ans_list)

        # chunk整理
        retrieval_answer = ''
        for i, chunk in enumerate(ans_list):
            retrieval_answer += f"{str(i)}.{chunk.text}+\n"

        # 生成回答
        llm_answer = self.llm.chat_in_template(
            prompt=rag_base_prompt, message=retrieval_answer, question=user_question,
            model_source=model_id, api_key=api_key
        )
        return llm_answer, ans_list

    def query_decompose_rag(
            self,
            collection_name: str,
            user_question: str,
            num_candidates: int = 100,
            top_k: int = 10,
            is_rerank: bool = False,
            search_method: str = 'search_by_vector',
            api_key: str = CHAT_API_KEY,
            model_id: str = CHAT_MODEL_ID


    ) -> Tuple[str, Dict[str, Chunk], str]:
        # 问题重构的方式进行rag，缺点是因为循环和反复问答，非常消耗时间、消耗token
        reference_chunk_dict = {}

        # 1. 问题分解
        new_query = self.llm.chat_in_template(
            prompt=query_split_prompt, question=user_question,
            model_source=model_id, api_key=api_key
        )
        query_list = get_query_list(new_query)
        answer_list = []

        while len(answer_list) < len(query_list):
            logger.info(f"while中： {len(answer_list)} / {len(query_list)}")
            # 2. 指代消除
            i = len(answer_list)  # 处理第i号query
            q_i = query_list[i]
            qa = ''
            for j in range(0, i):
                # 组织QA对
                qa += f'{str(j)}. Q:{query_list[j]} A:{answer_list[j]}'
                pass
            new_q_i = self.llm.chat_in_template(
                prompt=coreference_resolution_prompt, qa=qa, question=q_i

            )
            # 更新query_list
            query_list[i] = new_q_i
            # 3. 根据新的q_i进行检索问答
            chunk_list = self.retrieval(
                question=new_q_i,
                collection_name=collection_name,
                search_method=search_method,
                top_k=top_k,
                num_candidates=num_candidates
            )
            # rerank
            if is_rerank:
                chunk_list = self.reranker.reranker_chunks(query=user_question, chunks=chunk_list)

            # 整理一下
            retrieval_answer = ''
            for i, chunk in enumerate(chunk_list):
                retrieval_answer += f"{str(i)}.{chunk.text}+\n"  # 这里的编号加1了，之后记得这事儿

            # 4. 带指向性回答
            a_i = self.llm.chat_in_template(prompt=rag_with_reason_prompt, message=retrieval_answer, question=new_q_i)
            pure_a_i, reference_num_list = reference_extract(a_i)
            # 5. 补充到qa结果里
            answer_list.append(pure_a_i)
            for j in reference_num_list:
                # 大模型问答可能会抽风，所有要加一些限制，防止超出范围
                if 0 <= j <= len(chunk_list):
                    reference_chunk_dict[chunk_list[j].chunk_id] = chunk_list[j]
                else:
                    # 加上点日志记录
                    pass
            pass

        # 跳出来了，说明长度足够了
        final_message = ''
        for j, (key, chunk) in enumerate(reference_chunk_dict.items()):
            final_message += f"{str(j)}.{chunk.text}\n"
        final_qa = ''
        for j in range(0, len(query_list)):
            final_qa += f'{str(j)}. Q:{query_list[j]} A:{answer_list[j]}\n'
            pass
        final_question = user_question

        # 生成回答
        llm_answer = self.llm.chat_in_template(
            prompt=rag_base_prompt, question=final_question,
            message=final_message, qa=final_qa
        )
        return llm_answer, reference_chunk_dict, final_qa


if __name__ == "__main__":
    rag_controller = RAGController()
    qdr = True


    if not qdr:
        llm_ans, ref_ans = rag_controller.naive_rag(
            collection_name='test_kb1',
            user_question='是谁杀了胡太后？这个人的最后是怎么死的？',
            top_k=5,

        )
        print('参考资料：' + '=' * 40)
        print(ref_ans)
        print('最终答案' + '=' * 40)
        print(llm_ans)
    else:
        llm_ans, ref_chunks, qa = rag_controller.query_decompose_rag(
            collection_name='test_kb1',
            user_question='是谁杀了胡太后？这个人的最后是怎么死的？',
            top_k=5,
            is_rerank=True,
            num_candidates=100,
            search_method='search_by_vector'
            # is_rewritten=True
        )
        print('参考资料：' + '=' * 40)
        for k, v in ref_chunks.items():
            print(v.text)
        print('中间过程：' + '=' * 40)
        print(qa)
        print('最终答案' + '=' * 40)
        print(llm_ans)


