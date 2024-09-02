import os
import requests
import json
from config.mme_rag_config import CHAT_URL, CHAT_API_KEY, CHAT_MODEL_ID
from typing import Union
from rag.llm.base_llm import BaseLLM

class ChatAPILLM(BaseLLM):
    def __init__(
            self,
            # model_source: str = CHAT_MODEL_ID,
            url: str = CHAT_URL,
            **kwargs
    ):
        super().__init__(url, **kwargs)
        # self.api_key = CHAT_API_KEY  # os.getenv('CHAT_API_KEY')

    def chat_base(self, content: str, model_source: Union[str, None]=None, api_key: Union[str, None]=None) -> str:
        if model_source is None:
            model_source =CHAT_MODEL_ID
        if api_key is None:
            api_key = CHAT_API_KEY

        data = {
            "model": model_source,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "stream": False
        }
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.post(self.url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            raise Exception(f'LLM连接错误：{response.text}')
        return response.json()['choices'][0]['message']['content']
        # x = json.dumps(response.json(), indent=4, ensure_ascii=False)
        # return x


if __name__ == '__main__':


    chat_llm = ChatAPILLM(
        model_source='glm-4-flash',
        url = CHAT_URL
    )
    from rag.llm.prompt_config import rag_base_prompt
    # x = chat_llm.chat_base('你是谁？')
    x = chat_llm.chat_in_template(
        prompt=rag_base_prompt,
        message="""小明今年23岁，他的父亲是他年龄的两倍多1岁""",
        question='请问小明父亲的年龄？'
    )
    print(x)
