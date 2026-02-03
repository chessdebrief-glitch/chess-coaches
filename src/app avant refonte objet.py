# app.py (version ultra-découpée)
import streamlit as st
import ui_styles, ui_components, state_manager
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
    📥 Copie-colle ton PGN avec les **évaluations**.
""")

pgn_input = st.text_area(
    "PGN", 
    height=150, 
    placeholder=pgn_exemple, 
    label_visibility="collapsed"
)

# Initialisation des variables par défaut pour éviter les erreurs plus bas
game = None
move_range = (1, 50)

if pgn_input:
    from src.chess_engine import validate_pgn
    
    # Grâce au @st.cache_data, cette ligne est instantanée si on bouge juste le slider
    game, error_message = validate_pgn(pgn_input)

    if error_message:
        st.error("⚠️ PGN invalide")
        st.info(error_message)
    else:
        # --- ÉTAPE RÉUSSIE : ON EST DANS L'ENTONNOIR ---
        st.success("PGN valide !")
        
        # 1. Calcul de la longueur de la partie
        total_moves = 0
        temp_game = game
        while temp_game.next():
            total_moves += 1
            temp_game = temp_game.next()

        # 2. Affichage du Slider (apparaît seulement si PGN OK)
        move_range = st.slider(
            "Plage d'analyse :",
            min_value=1,
            max_value=max(1, total_moves),
            value=(1, min(50, total_moves)),
        )

# 3. Affichage du Bouton d'Action
    button_label = st.session_state.coach['punchlines'].get('analyse', "Analyser")
        
    if st.button(button_label, type="primary", use_container_width=True):
        # --- CONSTRUCTION DU PAYLOAD ---
        payload = {
            "user": {
                "name": prenom,
                "elo": user_elo,
                "is_white": st.session_state.joueur_est_blanc
            },
            "coach": st.session_state.coach, # id, nom, emoji, desc, vibe, punchlines
            "analysis_settings": {
                "move_range": move_range,
                "pgn_raw": pgn_input
            }
        }

        with st.spinner(f"Analyse par {st.session_state.coach['nom']}..."):
            from src.analysis_engine import run_analysis_flow
            
            # On récupère les DEUX éléments maintenant
            resultat_analyse, df_debug = run_analysis_flow(payload)
            
            st.markdown("---")

            # 1. On affiche le DataFrame pour débugger (en haut, pour vérifier les données)
            ui_components.display_debug_data(df_debug)

            # 2. On affiche le résultat (le prompt pour l'instant, plus tard la réponse IA)
            st.markdown("### 🤖 Analyse du Mentor")
            st.markdown(resultat_analyse, unsafe_allow_html=True)