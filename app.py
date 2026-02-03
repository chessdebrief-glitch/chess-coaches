import streamlit as st

# Import des modules d'interface situés dans le dossier src
from src import ui_styles, ui_components, state_manager

# Import des constantes et des classes techniques
from src.constants import MENTORS
from src.mentor import Mentor
from src.analysis_engine import run_analysis_flow
from src.prompt_builder import PromptBuilder

# Setup
st.set_page_config(page_title="Le Débrief", layout="centered")
ui_styles.load_css()
state_manager.init_state()

ui_components.header_section()

with st.sidebar:
    st.title("⚙️ Réglages")
    mode_ia = st.toggle("Activer l'IA (Gemini)", value=False) # Off par défaut = Debug
    run_mode = "api" if mode_ia else "debug"

# 1. Sélection du Mentor
ui_components.step_title(1, "Choisis ton mentor")
cols = st.columns(len(MENTORS))

for i, m_dict in enumerate(MENTORS):
    with cols[i]:
        # On compare l'ID de l'objet Mentor en session avec le dict des constantes
        is_sel = (st.session_state.mentor.id == m_dict["id"])
        
        if ui_components.mentor_card(m_dict['id'], m_dict['nom'], m_dict['emoji'], m_dict['desc'], m_dict['vibe'], is_sel):
            # On transforme le dictionnaire en Objet Mentor avant de le stocker
            new_mentor = Mentor(m_dict)
            state_manager.set_mentor(new_mentor)
            st.rerun()

# On récupère l'objet mentor de la session pour plus de clarté
mentor = st.session_state.mentor

# 2. Surnom
titre_nom = mentor.get_punchline('nom', "Comment t'appelles-tu ?")
ui_components.step_title(2, titre_nom)
prenom_raw = st.text_input("Surnom", placeholder="Garry", label_visibility="collapsed")
prenom = "".join(x for x in prenom_raw if x.isalnum())[:20] or "Ami"

# 3. ELO
titre_elo = mentor.get_punchline('elo', "Quel est ton niveau ?")
ui_components.step_title(3, titre_elo)
user_elo = ui_components.elo_selector()

# 4. PGN
titre_partie = mentor.get_punchline('pgn', "Donne-moi ta partie.")
ui_components.step_title(4, titre_partie)

label_couleur = "⚪ BLANCS" if st.session_state.joueur_est_blanc else "⚫ NOIRS"
st.toggle(label_couleur, key="joueur_est_blanc")

pgn_input = st.text_area(
    "PGN", 
    height=150, 
    placeholder="1. e4 e5...", 
    label_visibility="collapsed"
)

# Initialisation
move_range = (1, 50)

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
        stats = analyzer.get_stats()
        max_moves = stats.get("total_moves", 1)
        
        if max_moves > 1:
            move_range = st.slider(
                "Plage d'analyse :",
                min_value=1,
                max_value=max_moves,
                value=(1, min(50, max_moves)),
            )
        else:
            move_range = (1, 1)

    # 5. Bouton d'Action
    button_label = mentor.get_punchline('analyse', "Analyser")
        
    if st.button(button_label, type="primary", use_container_width=True):
        payload = {
            "user": {
                "name": prenom,
                "elo": user_elo,
                "is_white": st.session_state.joueur_est_blanc
            },
            # On repasse le mentor (l'objet sera géré dans analysis_engine)
            "coach": mentor, 
            "analysis_settings": {
                "move_range": move_range,
                "pgn_raw": pgn_input
            }
        }

        with st.spinner(f"Analyse par {mentor.nom}..."):
            from src.analysis_engine import run_analysis_flow
            
            resultat_analyse, df_debug = run_analysis_flow(
                payload, 
                st.session_state.analyzer, 
                mode=run_mode # <--- On utilise la variable du sidebar
            )
            
            st.markdown("---")
            st.subheader("📈 Courbe d'évaluation")
            fig = st.session_state.analyzer.generate_eval_chart(move_range)
            if fig:
                st.pyplot(fig)

            # Debug Data
            with st.expander("🛠️ Données d'analyse (Debug)"):
                ui_components.display_debug_data(df_debug)

            st.markdown(f"### 🤖 Analyse de {mentor.nom}")
            st.markdown(resultat_analyse, unsafe_allow_html=True)