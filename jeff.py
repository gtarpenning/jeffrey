
from enum import IntFlag
from utils import *
from core import OpenAIWrapper

from typing import List, Dict, Any, Optional, Tuple

import random
import glob
import subprocess

MAX_TOKENS = 4097

header_prompt = """
    You are a psychiatrist assistant. The following is a properly formatted header for a patient report. \

    "Psychiatric History Form

    Demographic Information

    First name Last name is a NaN-year-old, divorced, Caucasian, other, East Indian, female.
    Who goes by a preferred pronoun of she/her/hers.
    Person@people.com
    111-111-1111"

    \n
    Now, take the following information and write only the header, in this style, using Markdown to format:
    \n
"""


prompt = """
    Accurately construct sections of a psychiatric patient report, based on the provided information.
    Write relevant section paragraphs, with formatted headers, retaining as much information as possible.
    Use Markdown for formatting the report. Quote when appropriate. You MUST use full sentences. Do not
    include questions in the report. Patient information:
    \n\n
"""


def robot_psychiatrist():
    bot = OpenAIWrapper(model_name = ChatModel.GPT_35_TURBO, disable_wandb=False)

    intake_form = read_docx("./sample/question_2023-09-04.docx")
    header_form, intake_form = intake_form.split("111-111-1111")
    header_form += "111-111-1111"
    intake_form = "\n" + intake_form

    markdown_str = ""

    # construct header from intake form
    r = bot.call_chatgpt(messages=[
        {"role": "system", "content": header_prompt},
        {"role": "user", "content": header_form}
    ])
    markdown_str += r.message + "\n"

    prompt_tokens = num_tokens_from_string(prompt)
    intake_tokens = num_tokens_from_string(intake_form)
    print("prompt tokens: ", prompt_tokens)
    print("intake tokens: ", intake_tokens)

    # split the intake form into chunks CHEATING
    # TODO(gst): make agnostic to intake form
    chunks = []
    seperators = [
        "Current Employer (If Different Than Above)",
        "GAD-7",
        "Current Treatment",
        "Substance Use",
        "Relationship History",
        "Social History",
    ]

    for sep in seperators:
        chunks += [sep + intake_form.split(sep)[0]]
        intake_form = intake_form.split(sep)[1]

    # todo(gst): make concurrent calls to chatgpt

    # iterate through chunks and launch async processes to call_chatgpt
    for i, chunk in enumerate(chunks + [intake_form]):
        print(f"chunk {i}/{len(chunks) + 1} tokens: ", num_tokens_from_string(chunk))
        r = bot.call_chatgpt(messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": chunk}
        ])
        markdown_str += r.message + "\n"

    prev_versions = glob.glob("./output/md/v0-*.md")
    name = f"v0-{bot.model_name.value}-{len(prev_versions)}"
    with open(f"./output/md/{name}.md", "w") as f:
        f.write(markdown_str)

    subprocess.run(["mdpdf", "-o", f"./output/pdf/{name}.pdf", f"./output/md/{name}.md"])


def make_async_calls_to_chatgpt(text_list: List[str], bot: OpenAIWrapper):
    from multiprocessing import Process,Queue
    """Take a list of strings, and make calls to chatgpt using a process pool"""
    queue = Queue()
    p = Process(target=bot.call_chatgpt, args=(queue, 1))
    p.start()
    p.join()
    retult = queue.get()
    return result


def main():
    robot_psychiatrist()


if __name__ == "__main__":
    main()
