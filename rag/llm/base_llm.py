import os
from abc import ABC, abstractmethod
from typing import Union


class BaseLLM(ABC):
    def __init__(
            self,
            url: str,
            **kwargs
    ):
        # self.api_key = os.getenv('CHAT_API_KEY')
        # self.model_source = model_source
        self.url = url


    @abstractmethod
    def chat_base(self, content: str, model_source: Union[str, None]=None,
                  api_key: Union[str, None]=None) -> str:
        raise NotImplementedError

    def chat_in_template(self, prompt:str, model_source: Union[str, None]=None,
                         api_key: Union[str, None]=None, **kwargs) -> str:
        prompt = prompt.format(**kwargs)
        result = self.chat_base(content=prompt, model_source=model_source, api_key=api_key)
        return result


if __name__ == "__main__":


    def func(**kwargs):
        x = "{a}是{b}"
        print(x.format(**kwargs))

    func(a=1, b=2)