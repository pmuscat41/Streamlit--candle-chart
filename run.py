import streamlit as st
import docx2txt
import io
import re
from redlines import Redlines
from itertools import zip_longest
import base64

st.set_page_config(layout="wide")


def get_data():
    if 'all_markdown' not in st.session_state:
        st.session_state['all_markdown'] = []
    return st.session_state['all_markdown']

def read_word_or_text_file(file):
    if file.type == "text/plain":
        # Read text file

        content = str(file.read(), "utf-8")
    else:
        # Read Word file
        content = docx2txt.process(io.BytesIO(file.read()))
    return content

def split_claims(content):
    claims = re.split(r"\.(?=\s*\d)", content)
    return [claim.strip() for claim in claims if claim.strip()]

def display_claims(claims1, claims2,mtype):
    all_markdown = []
    col1, col2, col3 = st.columns(3)  # Define columns
    for i, (claim1, claim2) in enumerate(zip_longest(claims1, claims2)):
        with col1:
            if claim1 is not None:
                st.text_area(f"Claim {i+1}", claim1, key=f"claim_{i+1}")
        with col2:
            if claim2 is not None:
                st.text_area(f"Claim {i+1}", claim2, key=f"claim_b{i+1}")
        with col3:
            if claim1 is not None and claim2 is not None:
                diff = Redlines(claim1, claim2, markdown_style=mtype)
                opt = diff.output_markdown
                st.markdown(opt+".\n", unsafe_allow_html=True)
                all_markdown.append(opt)
                all_markdown.append(".\n")
            if claim1 is not None and claim2 is  None:
                diff = Redlines(claim1, " ",markdown_style=mtype)
                opt = diff.output_markdown
                st.markdown(opt+".\n", unsafe_allow_html=True)
                all_markdown.append(opt)
                all_markdown.append(".\n")
            if claim1 is  None and claim2 is not None:
               diff=Redlines(" ", claim2, markdown_style=mtype)
               opt = diff.output_markdown
               st.markdown(opt+".\n", unsafe_allow_html=True)
               all_markdown.append(opt)
               all_markdown.append(".\n")
    return '\n'.join(all_markdown)
        

def main():
    st.sidebar.title("Claim Operations")
    file1 = st.sidebar.file_uploader("Upload First File", type=['docx', 'txt'])
    file2 = st.sidebar.file_uploader("Upload Second File", type=['docx', 'txt'])

    operation = st.sidebar.radio("Select Operation", ["Mark-up Claim Changes", "Print Markup"])
    
    mtype = st.sidebar.selectbox("Select markup type", ["red-green", "none", "red","ghfm"])


    if operation == "Mark-up Claim Changes" and file1 is not None and file2 is not None:
        content = read_word_or_text_file(file1)
        current_claims = split_claims(content)
        content_2 = read_word_or_text_file(file2)
        new_claims_2 = split_claims(content_2)
    
        # Call display_claims and store the result in session state
        st.session_state['all_markdown'] = display_claims(current_claims, new_claims_2,mtype)

    if st.sidebar.button('Clear Screen'):
        st.session_state['all_markdown'] = []
        st.experimental_rerun()
    if st.sidebar.button('Download'):
        markdown_content = '\n'.join(st.session_state['all_markdown'])
        b64 = base64.b64encode(markdown_content.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="output2.md">Download Markdown</a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)

    if operation == "Print Markup":
        st.markdown(st.session_state['all_markdown'], unsafe_allow_html=True)
        
if __name__ == "__main__":
    main()
