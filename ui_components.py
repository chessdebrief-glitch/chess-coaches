# ui_components.py
import streamlit as st
from html import escape # Plus léger que bleach pour des simples chaînes

def mentor_card(mentor_id: str, nom: str, emoji: str, desc: str, vibe: str, is_selected: bool):
    """
    Composant de carte mentor. 
    Les arguments sont déstructurés pour respecter le principe de couplage faible.
    """
    # 1. Sécurisation des entrées (XSS protection)
    safe_nom = escape(nom)
    safe_desc = escape(desc)
    
    selected_css = "selected" if is_selected else ""
    
    # 2. Construction du template
    card_html = f"""
        <div class="coach-card {selected_css}">
            <div class="coach-emoji">{emoji}</div>
            <div class="coach-name">{safe_nom}</div>
            <div class="coach-vibe">{vibe}</div>
            <div class="coach-desc">{safe_desc}</div>
        </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # On retourne l'état du bouton pour que l'appelant gère la logique
    return st.button(f"Choisir", key=f"btn_{mentor_id}", use_container_width=True)

def header_section(title: str = "♔ LE DÉBRIEF"):
    # Utilisation d'escape même pour le titre par principe
    st.markdown(f'<h1 class="main-title">{escape(title)}</h1>', unsafe_allow_html=True)

def step_title(num: int, text: str):
    safe_text = escape(text)
    st.markdown(f'<p class="step-header">{num}. {safe_text}</p>', unsafe_allow_html=True)