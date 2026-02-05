import streamlit as st
from src import ui_styles, ui_components, state_manager
from src.mentor import Mentor
from src.constants import MENTORS
from src.analysis_engine import run_analysis_flow

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Le Débrief", layout="centered")
ui_styles.load_css()
state_manager.init_state()
ui_components.header_section()

with st.sidebar:
    st.title("⚙️ Réglages")
    mode_ia = st.toggle("Activer l'IA (Gemini)", value=False)
    run_mode = "api" if mode_ia else "debug"

# --- 2. ÉTAPE 1 : MENTOR ---
ui_components.step_title(1, "Choisis ton mentor")
cols = st.columns(len(MENTORS))
for i, m_dict in enumerate(MENTORS):
    with cols[i]:
        is_sel = (st.session_state.mentor.id == m_dict["id"])
        if ui_components.mentor_card(m_dict['id'], m_dict['nom'], m_dict['emoji'], m_dict['desc'], m_dict['vibe'], is_sel):
            state_manager.set_mentor(Mentor(m_dict))
            st.rerun()

mentor = st.session_state.mentor

# --- 3. ÉTAPE 2 & 3 : INFO JOUEUR ---
ui_components.step_title(2, mentor.get_punchline('nom'))
prenom_raw = st.text_input("Surnom", placeholder="Garry", label_visibility="collapsed")
prenom = "".join(x for x in prenom_raw if x.isalnum())[:20] or "Ami"

ui_components.step_title(3, mentor.get_punchline('elo'))
user_elo = ui_components.elo_selector()

# --- 4. ÉTAPE 4 : PGN & ANALYZER ---
pgn_input = ui_components.render_pgn_section(mentor)

if pgn_input:
    from src.chess_analyzer import ChessAnalyzer
    game, error_message = ChessAnalyzer.validate_pgn(pgn_input)

    if error_message:
        st.error(f"⚠️ {error_message}")
    else:
        if "analyzer" not in st.session_state or st.session_state.pgn_prev != pgn_input:
            st.session_state.analyzer = ChessAnalyzer(game)
            st.session_state.pgn_prev = pgn_input
        
        analyzer = st.session_state.analyzer
        max_moves = analyzer.get_stats().get("total_moves", 1)
        move_range = st.slider("Plage d'analyse :", 1, max_moves, (1, min(50, max_moves)))

        # --- 5. LE BOUTON D'ACTION (Unique) ---
        if st.button(mentor.get_punchline('analyse'), type="primary", use_container_width=True):
            payload = {
                "user": {"name": prenom, "elo": user_elo, "is_white": st.session_state.joueur_est_blanc},
                "coach": mentor,
                "analysis_settings": {"move_range": move_range, "pgn_raw": pgn_input}
            }

            with st.spinner(f"Analyse par {mentor.nom}..."):
                # On calcule et on stocke
                res, df_debug = run_analysis_flow(payload, analyzer, mode=run_mode)
                st.session_state.derniere_analyse = (res, df_debug, move_range)
                st.rerun() # On relance pour passer à l'affichage en bas

        # --- 6. ZONE D'AFFICHAGE BRUTE ---
        # --- 6. ZONE D'AFFICHAGE ---
        if "derniere_analyse" in st.session_state:
            res, df_debug, range_used = st.session_state.derniere_analyse
            ui_components.display_game_header(analyzer)

            # A. Affiche la courbe d'éval
            ui_components.render_analysis_results(
                mentor, res, st.session_state.analyzer, range_used
            )
            
            # B. Affiche le texte du Maître Zen avec les échiquiers intégrés
            ui_components.render_smart_analysis(
                res, st.session_state.analyzer, st.session_state.joueur_est_blanc
            )

            # C. Debug (toujours utile)
            #with st.expander("🔍 Debug : Objet technique reçu"):
            #    st.json(res)    