import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from constants import PROMPT_TEMPLATE

def call_gemini(pgn, coach_data, user_name):
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview", 
        google_api_key=st.secrets["GEMINI_API_KEY"]
    )
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm
    return chain.invoke({
        "pgn": pgn, 
        "coach_nom": coach_data["nom"], 
        "coach_style": coach_data["desc"], 
        "user_name": user_name,
        "coach_vibe" : coach_data["vibe"]
    }).content
