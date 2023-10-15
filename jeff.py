
from enum import IntFlag
from utils import *
from core import OpenAIWrapper

from typing import List, Dict, Any, Optional, Tuple

import random
import glob
import subprocess


JEFFREY_SIGNATURE = """
```
Report created by Jeffrey-v0 and ChatGPT. Jeffrey-v0 is a psychiatrist assistant that can help you write psychiatric patient reports from intake forms.
```
"""


header_prompt = """
    The following is a properly formatted header for a patient report. \

    # Psychiatric History Form

    ## Demographic Information

    William Jeffery is a 45-year-old, divorced, Caucasian, other, East Indian, male.

    Who goes by a preferred pronoun of he/him/his.

    <Person@people.com>

    <111-111-1111>

    \n
    Now, take the following information and write a header, in this style, using Markdown to format:
    \n
"""


questionare_prompt = """
    Based on the provided questionaire, convert the question answer format into a report format.
    - Write in 3rd person. Use the patient's name.
    - Write in full paragraphs, with section headers for major sections.
    - Use Markdown for formatting the report.
    - Quote from the answer when appropriate.
    - Do not include questions, bullet points, or ":" in the report.
    - Retain as much information as possible from the questionaire.

    Example Section from a sample report:

    ## Medical History

    Mr. Jeffery reported that he suffers from hypertension as well as gastroesophageal reflux. \
    In February 2022, he injured his hand. He stated that this injury was due to repetitive motions, \
    but also explained, “It was smashed against a wall with a hand truck.” He denied experiencing any \
    anxiety, depressive, or other psychiatric symptoms regarding his hand injury. He was initially \
    placed on light duty, but was later placed on medical leave for two months. He stated that he has \
    been attending his physical therapy sessions and is hopeful that his hand will recover and he can \
    return to work. Mr. Jeffery stated that he also underwent a transurethral prostate laser procedure and removal \
    of a mass in his parotid gland in the past, but explained that neither of these were cancer related. \
    He does not know the dates of these procedures.


    Questionaire:
    \n\n
"""


def robot_large(file_path: Any):
    bot = OpenAIWrapper(model_name = ChatModel.GPT_35_TURBO_16K_PINNED, disable_wandb=True)

    intake_form = read_docx(file_path)
    header_form, intake_form = intake_form.split("111-111-1111")
    header_form += "111-111-1111"
    intake_form = "\n" + intake_form[:300]

    markdown_str = ""

    # construct header from intake form first section
    r = bot.call_chatgpt(messages=[
        {"role": "system", "content": header_prompt},
        {"role": "user", "content": header_form}
    ])
    markdown_str += r.message + "\n\n"

    # construct report from intake form
    r = bot.call_chatgpt(messages=[
        {"role": "system", "content": questionare_prompt},
        {"role": "user", "content": intake_form}
    ])

    markdown_str += r.message
    markdown_str += "\n"
    markdown_str += JEFFREY_SIGNATURE

    return markdown_str


def main():
    robot_large("./sample/question_2023-09-04.docx")


if __name__ == "__main__":
    main()
