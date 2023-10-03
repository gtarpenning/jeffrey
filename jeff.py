
from enum import IntFlag
from utils import *
from core import OpenAIWrapper

import random

MAX_TOKENS = 4097

header_prompt = """
    You are a psychiatrist assistant. The following is a properly formatted header for a patient report. \

    Psychiatric History Form

    Demographic Information

    First name Last name is a NaN-year-old, divorced, Caucasian, other, East Indian, female.
    Who goes by a preferred pronoun of she/her/hers.
    Person@people.com
    111-111-1111

    \n
    Now, take the following information and write only the header, IN MARKDOWN:
"""


prompt = """
    You are a psychiatrist assistant. Take the questionare and accurately construct the patient report. \
    An example of the first section of the report is provided below. \
    \n
    Employment Where the Physical or Emotional Injury Occurred

    "At the time of his injury, Ms. Last name worked for IBM. She described this business as computers.
    Her first day of work there was 1/1/2004. The most recent day she worked at this job was 1/1/2023.
    Her job title when she started this employment was as a programmer. Her most recent job title at this employment was manager.
    Her employment duties included the following: turn computers on and off.
    She stated, "I liked his job because of lots of money." She stated, "I do not like this job cause I don't especially
    like computers." Her typical work schedule was 40 hours a week. Her salary at this position is $1,000,000.
    Her hourly rate is $1,000. She does receive overtime pay consisting of $100...."

    Now use the following information to write relevant sections of a report in markdown, with formatted section headers,
    retaining as much information as possible:
    \n
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
    markdown_str += r.message

    prompt_tokens = num_tokens_from_string(prompt)
    intake_tokens = num_tokens_from_string(intake_form)
    print("prompt tokens: ", prompt_tokens)
    print("intake tokens: ", intake_tokens)

    if intake_tokens > MAX_TOKENS - num_tokens_from_string(prompt):
        print(f"Too many tokens! Splitting into chunks")

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

        for chunk in chunks + [intake_form]:
            r = bot.call_chatgpt(messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": chunk}
            ])
            markdown_str += r.message
    # else:
    #     r = bot.call_chatgpt(messages=[
    #         {"role": "system", "content": prompt},
    #         {"role": "user", "content": intake_form}
    #     ])
    #     markdown_str += r.message

    with open(f"./output/v0-{int(random.random()*100000)}.md", "w") as f:
        f.write(markdown_str)


def main():
    robot_psychiatrist()


if __name__ == "__main__":
    main()
