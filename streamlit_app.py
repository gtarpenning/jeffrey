# streamlit cloud path

import streamlit as st

from jeff import robot_large

st.title('Jeffrey-v0 the psychiatry assistant')

# Initialization
if 'file' not in st.session_state:
    st.session_state.file = None

if not st.session_state.file:
    st.session_state.file = st.file_uploader('Upload a questionaire', type=['docx', 'txt', 'md'])

if st.session_state.file:
    st.write('File uploaded successfully!')
    st.write('Processing...')

    # my_bar = st.progress(0, text='Processing...')
    # for percent_complete in range(100):
    #     my_bar.progress(percent_complete + 1, text='Processing...')

    md, pdf = robot_large(st.session_state.file)

    st.write('Processing complete!')
    st.download_button('Download PDF', open(pdf, 'rb'), file_name='report.pdf')

    st.write('Markdown preview:')
    st.markdown(open(md, 'r').read()[:1000])
