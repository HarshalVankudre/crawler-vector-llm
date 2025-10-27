import streamlit as st
from openai import OpenAI
from pinecone import Pinecone

from src.config import OPENAI_API_KEY, PINECONE_API_KEY

@st.cache_resource
def get_openai_client():
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY not found. Please set it in your .env file.")
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        client.models.list()
        return client
    except Exception as e:
        st.error(f"OpenAI client init error: {e}")
        return None

@st.cache_resource
def get_pinecone_client():
    if not PINECONE_API_KEY:
        st.error("PINECONE_API_KEY not found. Please set it in your .env file.")
        return None
    try:
        return Pinecone(api_key=PINECONE_API_KEY)
    except Exception as e:
        st.error(f"Pinecone client init error: {e}")
        return None
