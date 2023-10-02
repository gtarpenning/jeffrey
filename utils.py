import os
from enum import Enum
from typing import Dict

import tiktoken


OPENAI_ENV_KEY = "OPENAI_API_KEY"


class ChatModel(Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_PINNED = "gpt-3.5-turbo-0613"
    GPT_4 = "gpt-4"


def make_cost_breakdown(
    model_name: ChatModel,
    prompt_tokens: float,
    completion_tokens: float,
    **kwargs,
) -> Dict[str, float]:
    """Create a price breakdown dict.

    usage:
        make_cost_breakdown("gpt-3.5-turbo", **response.usage)

    returns: {
        "prompt": float,
        "completion": float,
        "total": float
    }
    """
    # gpt-3.5
    if model_name in [ChatModel.GPT_35_TURBO, ChatModel.GPT_35_TURBO_PINNED]:
        cost_per_input_token: float = 0.0015 / 1000
        cost_per_output_token: float = 0.002 / 1000
    # gpt-4
    elif model_name == ChatModel.GPT_4:
        cost_per_input_token: float = 0.03 / 1000
        cost_per_output_token: float = 0.06 / 1000
    else:
        assert False, "Invalid model name in response object"

    return {
        "prompt": prompt_tokens * cost_per_input_token,
        "completion": completion_tokens * cost_per_output_token,
        "total": (prompt_tokens * cost_per_input_token) + (completion_tokens * cost_per_output_token)
    }

def num_tokens_from_string(message: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(message))

    return num_tokens

def get_openai_key() -> str | None:
    key = os.environ.get(OPENAI_ENV_KEY)
    user_path = os.path.expanduser('~')
    if not key:
        # try read from secrets file
        user_path = os.path.expanduser('~')
        secrets = open(f"{user_path}/.secrets").read()
        for line in secrets.split("\n"):
            if OPENAI_ENV_KEY in line:
                key = line.split(f"{OPENAI_ENV_KEY}=")[1].replace("\"", "")
    else:
        # user has key, dump it to secrets for longterm storage
        if '.secrets' not in os.listdir(user_path):
            with open(f"{user_path}/.secrets", "w") as f:
                f.write(f"{OPENAI_ENV_KEY}={key}")
    return key
