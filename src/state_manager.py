# state_manager.py
import streamlit as st
from constants import DEFAULT_COACH

def init_state():
    if 'coach' not in st.session_state:
        st.session_state.coach = DEFAULT_COACH
    if 'joueur_est_blanc' not in st.session_state:
        st.session_state.joueur_est_blanc = True

def set_coach(coach_dict):
    st.session_state.coach = coach_dict

def toggle_color():
    st.session_state.joueur_est_blanc = not st.session_state.joueur_est_blanc