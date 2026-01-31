# app.py (version ultra-découpée)
import streamlit as st
import main, ui_styles, ui_components, state_manager
from constants import MENTORS

# Setup
st.set_page_config(page_title="Le Débrief", layout="centered")
ui_styles.load_css()
state_manager.init_state()

ui_components.header_section()

ui_components.step_title(1, "Choisis ton mentor")
cols = st.columns(len(MENTORS))
for i, m in enumerate(MENTORS):
    with cols[i]:
        is_sel = (st.session_state.coach["id"] == m["id"])
        if ui_components.mentor_card(m['id'], m['nom'], m['emoji'], m['desc'],m['vibe'], is_sel):
            state_manager.set_coach(m)
            st.rerun()

titre_nom = st.session_state.coach['punchlines'].get('nom', "Comment t'appelles-tu ?")
ui_components.step_title(2, titre_nom)
prenom_raw = st.text_input("Surnom", placeholder="Garry", label_visibility="collapsed")
prenom = "".join(x for x in prenom_raw if x.isalnum())[:20] or "Ami"

titre_elo = st.session_state.coach['punchlines'].get('elo', "elo ?")
ui_components.step_title(3, titre_elo)
user_elo = ui_components.elo_selector()

# Lors de la création du JSON pour l'IA :
#payload["players"]["user"]["elo_rating"] = user_elo

titre_partie = st.session_state.coach['punchlines'].get('pgn', "pgn ?")
ui_components.step_title(4, titre_partie)
label_couleur = "⚪ BLANCS" if st.session_state.joueur_est_blanc else "⚫ NOIRS"
st.toggle(label_couleur, key="joueur_est_blanc") # Streamlit gère le lien auto avec la clé

pgn_exemple = (
    "1. e4 { [%eval 0.2] } e5 { [%eval 0.23] } "
    "2. Nf3 { [%eval 0.25] } Nc6 { [%eval 0.21] } "
    "3. Bc4 { [%eval 0.15] } Nf6 { [%eval 0.28] }..."
)

st.caption("""
    📥 Copie-colle ton PGN depuis Chess.com ou Lichess.⚠️ Pour une analyse précise, assure-toi d'inclure les **évaluations d'ordinateur** (clique sur 'Analyse' avant d'exporter).
""")

pgn_input = st.text_area(
    "PGN", 
    height=150, 
    placeholder=pgn_exemple, # On injecte l'exemple ici
    label_visibility="collapsed"
)

# 4. ACTION
# Dans app.py, juste avant le bouton d'action
actions = {
    "zen": f"{st.session_state.coach['nom']}, guide mon esprit...",
    "prof": f"{st.session_state.coach['nom']}, corrige ma copie",
    "blitz": f"{st.session_state.coach['nom']}, montre-moi l'arnaque !",
    "boa": f"{st.session_state.coach['nom']}, montre-moi où j'ai serré..."
}

button_label =st.session_state.coach['punchlines'].get('analyse', "analyse ?")

# 4. ACTION
if st.button(button_label, type="primary", use_container_width=True):
    if not pgn_input:
        st.warning("Hé ! Il me faut un PGN pour travailler.")
    else:
        with st.spinner("Génération du prompt..."):
            # On récupère les données pour le debug
            coach_data = st.session_state.coach
            
            # --- ZONE DEBUG : RÉCUPÉRATION DU PROMPT ---
            from constants import PROMPT_TEMPLATE
            from langchain_core.prompts import ChatPromptTemplate
            
            # On simule ce que fait ai_engine pour voir le texte final
            prompt_obj = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
            prompt_final = prompt_obj.format(
                pgn=pgn_input,
                coach_nom=coach_data["nom"],
                coach_style=coach_data["desc"],
                coach_vibe=coach_data["vibe"],
                user_name=prenom
            )
            
            # Affichage du prompt pour que tu puisses le copier
            with st.expander("🔍 VOIR LE PROMPT ENVOYÉ (DEBUG)"):
                st.code(prompt_final, language="text")
            # ------------------------------------------

            # Appel de la logique métier (qui renvoie le mock en mode debug)
            resultat_analyse = main.run_full_analysis(
                pgn_input, 
                prenom, 
                coach_data, 
                st.session_state.joueur_est_blanc
            )
            
            st.markdown("---")
            st.markdown(resultat_analyse, unsafe_allow_html=True)