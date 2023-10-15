import os
from enum import Enum
from typing import Dict, Any, Tuple, Union

import docx
import tiktoken
import glob
import subprocess
import logging

import streamlit as st

OPENAI_ENV_KEY = "OPENAI_API_KEY"


class ChatModel(Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_PINNED = "gpt-3.5-turbo-0613"
    # the normal 16k model returns the pinned version response, just use that
    # GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_35_TURBO_16K_PINNED = "gpt-3.5-turbo-16k-0613"
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
    if model_name in [ChatModel.GPT_35_TURBO, ChatModel.GPT_35_TURBO_PINNED, ChatModel.GPT_35_TURBO_16K_PINNED]:
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

def get_openai_key() -> Union[str, None]:
    """Get the openai key from the environment."""
    # check if in deployed environment, grab from streamlit
    if OPENAI_ENV_KEY in st.secrets:
        logging.log(logging.INFO, "Using openai streamlit secret")
        return st.secrets[OPENAI_ENV_KEY]

    key = os.environ.get(OPENAI_ENV_KEY)
    user_path = os.path.expanduser('~')
    if not key:
        # try read from secrets file
        user_path = os.path.expanduser('~')
        if os.path.exists(f"{user_path}/.secrets"):
            secrets = open(f"{user_path}/.secrets").read()
            for line in secrets.split("\n"):
                if OPENAI_ENV_KEY in line:
                    key = line.split(f"{OPENAI_ENV_KEY}=")[1].replace("\"", "")
    if not key:
        logging.log(logging.ERROR, "No openai key found in environment or secrets file")
    return key


def read_docx(filepath: Union[str, Any]) -> str:
    """Read a docx file and return a string."""
    doc = docx.Document(filepath)

    out_str = ""
    for paragraph in doc.paragraphs:
        out_str += paragraph.text + "\n"

    return out_str


def dump_output(markdown: str, bot_name: str, version: str) -> Tuple[str, str]:
    """Dump output to markdown and pdf."""
    prev_versions = glob.glob("./output/md/v0-*.md")
    name = f"v0-{bot_name}-{len(prev_versions)}"
    with open(f"./output/md/{name}.md", "w") as f:
        f.write(markdown)

    subprocess.run(["mdpdf", "-o", f"./output/pdf/{name}.pdf", f"./output/md/{name}.md"])

    return f"./output/md/{name}.md", f"./output/pdf/{name}.pdf"
