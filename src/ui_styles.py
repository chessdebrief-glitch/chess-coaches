# ui_styles.py
import streamlit as st
import bleach
import os

def load_css(file_name="style.css"):
    """Version durcie de chargement CSS"""
    if not os.path.exists(file_name):
        return

    with open(file_name, "r", encoding="utf-8") as f:
        css_content = f.read()
        
    # On vérifie que le fichier ne contient pas de balises <script>
    # Même si c'est NOTRE fichier, on applique le principe de Zero Trust.
    if "<script" in css_content.lower():
        st.error("Sécurité : Contenu suspect détecté dans le CSS.")
        return

    # On utilise st.html (disponible dans les versions récentes de Streamlit)
    # ou on reste sur markdown mais avec un contenu contrôlé.
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

def render_safe_report(raw_report):
    # 1. Définition des balises autorisées
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 
        'ul', 'li', 'div', 'img', 'span', 'hr'
    ]

    # 2. Définition des attributs et des protocoles de liens
    # CRITIQUE : On ajoute 'data' pour autoriser les images en Base64/SVG inline
    allowed_attrs = {
        'img': ['src', 'style', 'width', 'alt'],
        'div': ['style'],
        'span': ['style'],
        'p': ['style']
    }
    
    # On limite les protocoles pour éviter <img src="javascript:...">
    allowed_protocols = ['http', 'https', 'data']

    # 3. Styles CSS autorisés (Whitelist stricte)
    allowed_styles = [
        'color', 'font-weight', 'text-align', 'background-color', 
        'border', 'border-radius', 'padding', 'margin', 
        'display', 'flex-direction', 'justify-content', 'align-items',
        'width', 'max-width', 'box-shadow', 'font-style'
    ]
    
    # Nettoyage
    clean_html = bleach.clean(
        raw_report, 
        tags=allowed_tags, 
        attributes=allowed_attrs, 
        styles=allowed_styles,
        protocols=allowed_protocols
    )
    
    # Rendu
    st.markdown(clean_html, unsafe_allow_html=True)