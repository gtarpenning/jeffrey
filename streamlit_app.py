# streamlit cloud path

import streamlit as st

import subprocess
import os
import random

from utils import *
from core import OpenAIWrapper
import jeff


st.title('Jeffrey-v0 the psychiatry assistant')
file = st.file_uploader('Upload a questionaire', type=['docx', 'txt', 'md'])
if file:
    st.write('File uploaded successfully!')

    test = st.checkbox('Test mode')
    start = st.button('Start processing')
    if start:

        with st.expander(label="Report", expanded=True):
            bot = OpenAIWrapper(model_name=ChatModel.GPT_35_TURBO_16K_PINNED, disable_wandb=True)
            file_contents = read_docx(file)
            header_form, intake_form = file_contents.split("—————")
            if test:
                intake_form = intake_form[:1000]

            markdown_str = "# Psychiatric History Report\n"

            # first make the section header:
            header_messages=[
                {"role": "system", "content": jeff.header_prompt},
                {"role": "user", "content": header_form}
            ]

            stream_text = st.empty()
            for chunk in bot.call_chatgpt_stream(messages=header_messages):
                msg = chunk["choices"][0]["delta"].get("content")
                if msg:
                    markdown_str += msg.replace("$", "\$")
                stream_text.write(markdown_str)

            markdown_str += "\n"
            # then make the report body:
            question_messages=[
                {"role": "system", "content": f"Patient demographic info: {markdown_str}"},
                {"role": "system", "content": jeff.questionare_prompt},
                {"role": "user", "content": intake_form}
            ]
            for chunk in bot.call_chatgpt_stream(messages=question_messages):
                msg = chunk["choices"][0]["delta"].get("content")
                if msg:
                    markdown_str += msg.replace("$", "\$")
                stream_text.write(markdown_str)

        st.write('Processing complete!')
        os.makedirs('./output/md', exist_ok=True)
        n = round(random.random()*1000000)
        name = f"{file.name.split('.')[0]}-{n}"
        with open(f"./output/md/{name}.md", "w") as f:
            f.write(markdown_str)

        os.makedirs('./output/pdf', exist_ok=True)
        subprocess.run(["mdpdf", "-o", f"./output/pdf/{name}.pdf", f"./output/md/{name}.md"])

        st.download_button('Download PDF', open(f"./output/pdf/{name}.pdf", 'rb'), file_name='report.pdf')
