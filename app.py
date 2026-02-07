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
    # Toggle activé par défaut et renonmmé "Analyse IA"
    mode_ia = st.toggle("Activer l'IA", value=True)
    run_mode = "api" if mode_ia else "debug"
    initial_sidebar_state="collapsed"

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
prenom_raw = st.text_input("Surnom", placeholder="Petit Magnus", label_visibility="collapsed")
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

        # --- 6. ZONE D'AFFICHAGE ---
        if "derniere_analyse" in st.session_state:
            res, df_debug, range_used = st.session_state.derniere_analyse
            
            # Extraction sécurisée du texte
            analysis_text = ""
            
            if isinstance(res, list):
                # Si c'est une liste de dictionnaires, on cherche la clé 'text' ou 'content'
                extracted_parts = []
                for item in res:
                    if isinstance(item, dict):
                        # On prend la première valeur string qu'on trouve ou une clé spécifique
                        text_val = item.get('text') or item.get('content') or str(item)
                        extracted_parts.append(text_val)
                    else:
                        extracted_parts.append(str(item))
                analysis_text = "\n\n".join(extracted_parts)
            
            elif isinstance(res, dict):
                analysis_text = res.get('text') or res.get('content') or str(res)
            else:
                analysis_text = str(res)

            ui_components.display_game_header(analyzer)
            
            st.subheader("📈 Évolution de l'avantage")
            # Appel de la fonction de l'analyzer pour récupérer la figure Matplotlib
            fig = analyzer.generate_eval_chart(range_used)
            st.pyplot(fig)
            
            st.divider() # Séparation visuelle entre le graph et le texte

            ui_components.render_smart_analysis(
                analysis_text, st.session_state.analyzer, st.session_state.joueur_est_blanc
            )