# src/state_manager.py
import streamlit as st
from .constants import DEFAULT_COACH # ✅ Le "." signifie "dans le même dossier que moi"
from src.mentor import Mentor

def init_state():
    # On change 'coach' par 'mentor' ici
    if 'mentor' not in st.session_state:
        st.session_state.mentor = Mentor(DEFAULT_COACH)
        
    if 'joueur_est_blanc' not in st.session_state:
        st.session_state.joueur_est_blanc = True
        
    if 'pgn_prev' not in st.session_state:
        st.session_state.pgn_prev = ""

def set_mentor(mentor_obj):
    # On met à jour le nom de la variable de session
    st.session_state.mentor = mentor_obj

def toggle_color():
    st.session_state.joueur_est_blanc = not st.session_state.joueur_est_blanc