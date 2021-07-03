import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import re
import bibtexparser
import io
import boto3

# import files from S3:
# get credentials from environment variables
aws_id = st.secrets['AWS_KEY']
aws_secret = st.secrets['AWS_KEY_SECRET']
aws_region = st.secrets['AWS_REGION']

client = boto3.client('s3', aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret, region_name=aws_region)

bucket_name = 'retraction-check'

object_key = 'sample_literature_retraction.bib'
retracted_obj = client.get_object(Bucket=bucket_name, Key=object_key)
retracted_literature = retracted_obj['Body']

object_key = 'sample_literature.bib'
unretracted_obj = client.get_object(Bucket=bucket_name, Key=object_key)
unretracted_literature = unretracted_obj['Body']

object_key = 'sample_database_cleaned.csv'
sample_database_obj = client.get_object(Bucket=bucket_name, Key=object_key)
sample_database = sample_database_obj['Body'].read().decode('utf-8')
sample_database = io.StringIO(sample_database)
sample_database.seek(0)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache(persist=True)
def prepare_database():
    database = pd.read_csv(sample_database, sep=",", encoding = "utf-8")
    database.drop(["Unnamed: 0","Group.1"], axis=1, inplace=True, errors = 'ignore')

    database.rename(columns={database.columns[0]: 'paper', database.columns[1]: 'reason', database.columns[2]: 'authors', database.columns[3]: 'paper_info', database.columns[4]: 'retraction_info', database.columns[5]: 'article_type', database.columns[6]: 'countries'}, inplace=True)

    return database

def load_bibtex(input):
    input = input.read().decode('utf-8')
    input = io.StringIO(input)
    input.seek(0)

    bib_database = bibtexparser.load(input)
    bibtex_str = bibtexparser.dumps(bib_database)
    # st.write(bibtex_str)
    print_lit(bibtex_str)

    return bibtex_str

def check_retractions(bibtex):
    dois = re.findall('doi = {(.+?)}', bibtex)

    st.subheader("DOIs in .bib File")
    st.write(dois)
    contains_no_retractions = True
    for doi in dois:
        if doi in retracted_dict:
            contains_no_retractions = False
            st.write("#")
            st.markdown(f'<p class = "retracted">RETRACTED: {doi}</p>', unsafe_allow_html=True)

    if contains_no_retractions == True:
        st.write("#")
        st.text("Yeay, no retractions!")

def print_lit(bib):
    st.markdown(f'<div class="bib-content">{bib}</div>', unsafe_allow_html=True)


# load retraction database
database = prepare_database()
# create a dict
retracted_dict = { key : "retracted" for key in [re.sub(".*, ", "", i).strip() for i in database['paper_info']]}

# load style.css
local_css("style.css")

# Header
components.html(
    """
    <div>
        <h1 style="color: white; text-align: center">Retraction Check</h1>

    </div>
    """,
)

st.markdown('<h2 style="font-size: 1.5em; color: white; text-align: center">Check whether your references contain retracted papers</h2>', unsafe_allow_html=True)


# Create some title
# st.subheader("Check whether your references contain retracted papers")

st.write("#")

st.header('Sample Database')
st.write(database)

components.html(
    """
    <div>
        <p style="color: white; text-align: center"> ------------------------------------------------------------------------------------ </p>
    </div>
    """,
)

st.header("Example with retraction in .bib file")
retracted_example = load_bibtex(retracted_literature)
check_retractions(retracted_example)

components.html(
    """
    <div>
        <p style="color: white; text-align: center"> ------------------------------------------------------------------------------------ </p>
    </div>
    """,
)

st.header("Example without retraction in .bib file")
unretracted_example = load_bibtex(unretracted_literature)
check_retractions(unretracted_example)

components.html(
    """
    <div>
        <p style="color: white; text-align: center"> ------------------------------------------------------------------------------------ </p>
    </div>
    """,
)

# file selector for uploading bibliography
st.header("Test with your own .bib file!")
upload = st.file_uploader("Upload a bib file", type=["bib"])
if upload != None:
    # st.text(bib_file.read())
    st.text("Upload successful!")

    upload.seek(0) # reset cursor in the file-like object

    upload = load_bibtex(upload)
    check_retractions(upload)
