# streamlit cloud path

import streamlit as st

import subprocess
import os
import random

from jeff import robot_large

st.title('Jeffrey-v0 the psychiatry assistant')

file = st.file_uploader('Upload a questionaire', type=['docx', 'txt', 'md'])

if file:
    st.write('File uploaded successfully!')

    test = st.checkbox('Test mode')

    start = st.button('Start processing')
    if start:
        st.write('Processing...')

        # my_bar = st.progress(0, text='Processing...')
        # for percent_complete in range(100):
        #     my_bar.progress(percent_complete + 1, text='Processing...')

        markdown_str = robot_large(file, test=test)

        st.write('Processing complete!')
        st.write('Markdown preview:')
        st.markdown(markdown_str)

        os.makedirs('./output/md', exist_ok=True)
        n = round(random.random()*1000000)
        name = f"{file.name.split('.')[0]}-{n}"
        with open(f"./output/md/{name}.md", "w") as f:
            f.write(markdown_str)

        os.makedirs('./output/pdf', exist_ok=True)
        subprocess.run(["mdpdf", "-o", f"./output/pdf/{name}.pdf", f"./output/md/{name}.md"])

        st.download_button('Download PDF', open(f"./output/pdf/{name}.pdf", 'rb'), file_name='report.pdf')
