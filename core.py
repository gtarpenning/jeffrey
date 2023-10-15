import os
import random
import argparse
from typing import Any, List, Dict, Union, Optional

from datetime import datetime

import openai
import wandb
from wandb.integration.openai import autolog


from utils import *

INTERNAL_VERSION: str = "v0"

DEFAULT_MODEL = "gpt-3.5-turbo"
WANDB_PROJECT = "jeffrey"

# load openai key from env var or secret file
openai.api_key = get_openai_key()


class ChatResponse:

    """
    {
      "id": "chatcmpl-852n4If6DiBkDkGtu7BiALgV1keT2",
      "object": "chat.completion",
      "created": 1696213058,
      "model": "gpt-3.5-turbo-0613",
      "choices": [],
      "usage": {
        "prompt_tokens": 1358,
        "completion_tokens": 220,
        "total_tokens": 1578
      }
    }
    """

    def __init__(self, response: Any):
        assert isinstance(response, dict), f"Response is not a dict! {response}"
        self._model_name: ChatModel = ChatModel(response['model'])
        self.response: Dict[str, Any] = response

    @property
    def message(self) -> str:
        return self.response['choices'][0]['message']['content']

    @property
    def tokens(self) -> int:
        return self.response['usage']['total_tokens']

    @property
    def usage(self) -> Dict[str, float]:
        return self.response['usage']

    @property
    def cost_breakdown(self):
        return make_cost_breakdown(self._model_name, **self.usage)

    def print_cost_breakdown(self):
        print(f"Prompt [{self.usage['prompt_tokens']}]: ${round(self.cost_breakdown['prompt'], 4)}")
        print(f"Completion [{self.usage['completion_tokens']}]: ${round(self.cost_breakdown['completion'], 4)}")
        print(f"Total [{self.tokens}]: ${round(self.cost_breakdown['total'], 4)}")


class OpenAIWrapper:
    """Manages connections to openAI api."""

    def __init__(
        self,
        model_name: ChatModel = ChatModel(DEFAULT_MODEL),
        model_temperature: float = 0.0,
        wandb_project: str = WANDB_PROJECT,
        disable_wandb: bool = False,
        max_tokens: Optional[int] = None,
    ) -> None:
        self.model_name: ChatModel = model_name
        self.model_temperature: float = model_temperature
        self.max_tokens: Optional[int] = None
        self.model_presence_penalty: float = 0.0
        self.model_frequency_penalty: float = 0.0

        # log of previous messages
        self.history: list = []

        # setup logging to wandb project if not disabled
        if not disable_wandb:
            autolog({"project": wandb_project})

    def call_chatgpt_stream(self, messages: List[Dict[str, str]], include_history: bool = False) -> Any:
        model_args = {
            "model": self.model_name.value,
            "stream": True,
            "messages": messages,
            "temperature": self.model_temperature,
            # Positive values penalize new tokens based on whether they appear in the text so far
            "presence_penalty": self.model_presence_penalty,
            # Positive values penalize new tokens based on their existing frequency in the text
            "frequency_penalty": self.model_frequency_penalty
        }

        stream = openai.ChatCompletion.create(**model_args)

        return stream


    def call_chatgpt(self, messages: List[Dict[str, str]], include_history: bool = False) -> ChatResponse:
        assert not self.stream, "Cannot call_chatgpt with stream=True"
        if include_history:
            messages = self.history + messages

        model_args = {
            "model": self.model_name.value,
            "messages": messages,
            "temperature": self.model_temperature,
            # Positive values penalize new tokens based on whether they appear in the text so far
            "presence_penalty": self.model_presence_penalty,
            # Positive values penalize new tokens based on their existing frequency in the text
            "frequency_penalty": self.model_frequency_penalty
        }

        if self.max_tokens:
            model_args["max_tokens"] = self.max_tokens

        print(f"[Calling chatgpt, model: {self.model_name.value}]")
        t = sum([num_tokens_from_string(x['content']) for x in messages])
        low_bound = round(t/50 / 60, 2)
        high_bound = round(t/25 / 60, 2)
        print(f"[Total tokens: {t}, ETA (m): {low_bound}-{high_bound}]")

        now = datetime.now()
        completion = openai.ChatCompletion.create(**model_args)
        elapsed = datetime.now() - now
        response = ChatResponse(completion)
        self.history += messages + [response.message]

        print(f"[Time elapsed: {elapsed}, tokens/s: {round(response.tokens / elapsed.total_seconds(), 3)}]")
        response.print_cost_breakdown()

        return response


class Summarizer(OpenAIWrapper):

    summary_message = "Please summarize the following text, preserving as much information as possible:"

    def __init__(self, max_tokens: int, **kwargs):
        super().__init__(**kwargs)

        # required for Summarizer
        self.max_tokens = max_tokens

    def summarize(self, text: str) -> ChatResponse:
        messages = [
            {"role": "system", "content": self.summary_message},
            {"role": "user", "content": text}
        ]
        r = self.call_chatgpt(messages=messages)

        return r


def test_summary(disable_wandb: bool):
    summary_bot = Summarizer(model_name = ChatModel.GPT_35_TURBO, max_tokens=1000, disable_wandb=disable_wandb)

    sample_message = open("./sample/sample.txt", "r").read()
    resp = summary_bot.summarize(sample_message)

    print(f"\n{resp.message}")


def test_create_report(disable_wandb: bool):
    chat_bot = OpenAIWrapper(model_name = ChatModel.GPT_35_TURBO, disable_wandb=disable_wandb)
    patient_info = """
        Name: Jeremy Trilling
        Age: 24
        "I am super depressed"
        I don't go outside and constantly feel like I am being watched.

        Past Psychiatric History:
        There is no history of withdrawal from any substance.
        Jeremy has never been psychiatrically hospitalized.
    """

    context = open("./sample/sample.txt", "r").read()
    psychiatrist_message = {
        "role": "system",
        "content": f"You are a psychiatrist's assistant. The following in an example of a report \
        you might write: {context} \n\n Now use this information to write a report IN MARKDOWN about the \
        following patient:"
    }
    message_2 = {"role": "user", "content": patient_info}

    final = chat_bot.call_chatgpt(messages=[psychiatrist_message, message_2])

    # dump to written report for viewing pleasure
    with open(f"./output/{INTERNAL_VERSION}-{int(random.random()*100000)}.md", "w") as f:
        f.write(final.message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--disable_wandb", "-dw", action="store_true", default=False)

    args = parser.parse_args()
    disable_wandb = args.disable_wandb

    # test_summary(disable_wandb)
    test_create_report(disable_wandb)


if __name__ == "__main__":
    main()
