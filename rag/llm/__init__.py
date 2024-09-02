from rag.llm.base_llm import BaseLLM
from rag.llm.online_llm import ChatAPILLM


def create_llms(
        llm_type: str,
        url: str,
        **kwargs) -> BaseLLM:
    llm_factory = {
        'ChatAPILLM' : ChatAPILLM
    }
    if llm_type not in llm_factory:
        raise ValueError(f'Unkown LLM type: {llm_type}')
    return llm_factory[llm_type](url=url, **kwargs)