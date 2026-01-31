import streamlit as st
import bleach
import main
import re
from constants import MENTORS, DEFAULT_COACH

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Le Débrief - Coach IA",
    page_icon="♔",
    layout="centered"
)

# --- INJECTION CSS (Version 4 Mentors) ---
st.markdown("""
<style>
    /* Titres et Structure */
    .main-title { text-align: center; color: white; font-size: 3rem; font-weight: 800; margin-bottom: 2rem; }
    .step-header { color: #2196F3; font-weight: 600; font-size: 1.2rem; margin-top: 2rem; margin-bottom: 1rem; text-transform: uppercase; text-align: center; }
    
    /* Grille des Mentors */
    .coach-card {
        padding: 12px 8px;
        border-radius: 12px;
        border: 1px solid #333;
        background-color: #1e1e1e;
        text-align: center;
        margin-bottom: 10px;
        transition: all 0.3s ease;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .coach-card.selected {
        border: 2px solid #00FF00 !important;
        background-color: #1a2e1a !important;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.2);
        transform: translateY(-5px);
    }
    
    .coach-emoji { font-size: 2.2rem; margin-bottom: 8px; }
    .coach-name { font-weight: bold; font-size: 1rem; color: white; display: block; margin-bottom: 5px; }
    .coach-desc { font-size: 0.75rem; color: #aaa; line-height: 1.2; }
    
    .coach-quote {
        text-align: center;
        font-style: italic;
        color: #888;
        margin-top: 15px;
        font-size: 0.9rem;
        min-height: 1.2rem;
    }

    div.stButton > button {
        border-radius: 8px !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
main.setup_folders()

if 'coach' not in st.session_state:
    st.session_state.coach = DEFAULT_COACH

# --- TITRE ---
st.markdown('<h1 class="main-title">♔ LE DÉBRIEF</h1>', unsafe_allow_html=True)

# --- ÉTAPE 1 : IDENTITÉ ---
st.markdown('<p class="step-header">1. Ton Surnom</p>', unsafe_allow_html=True)
prenom_raw = st.text_input("Comment le coach doit-il t'appeler ?", placeholder="Garry", label_visibility="collapsed")
prenom = "".join(x for x in prenom_raw if x.isalnum())[:20] or "Ami"

# --- ÉTAPE 2 : CHOIX DU MENTOR ---
st.markdown('<p class="step-header">2. Choisis ton Mentor</p>', unsafe_allow_html=True)
cols = st.columns(len(MENTORS))

for i, m in enumerate(MENTORS):
    with cols[i]:
        is_selected = st.session_state.coach["id"] == m["id"]
        card_class = "coach-card selected" if is_selected else "coach-card"
        
        st.markdown(f"""
            <div class="{card_class}">
                <div class="coach-emoji">{m['emoji']}</div>
                <span class="coach-name">{m['nom']}</span>
                <span class="coach-desc">{m['desc']}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Choisir", key=f"sel_{m['id']}", use_container_width=True):
            st.session_state.coach = m
            st.rerun()

quotes = {
    "zen": "« La victoire appartient à celui qui accepte le chaos sans s'y perdre. »",
    "prof": "« On ne construit pas une cathédrale sur du sable. Révisez vos bases. »",
    "blitz": "« Si tu ne lui fais pas peur, c'est lui qui va te braquer. »",
    "boa": "« Pourquoi prendre un risque quand on peut simplement lui ôter l'air ? »"
}

current_coach_id = st.session_state.coach.get("id", "prof")
display_quote = quotes.get(current_coach_id, quotes["prof"])
st.markdown(f'<p class="coach-quote">{display_quote}</p>', unsafe_allow_html=True)

# --- ÉTAPE 3 : PGN ET COULEUR ---
st.markdown('<p class="step-header">3. Ta Partie & Couleur</p>', unsafe_allow_html=True)
pgn_input = st.text_area("Colle ton PGN ici", height=150, placeholder="1. e4 e5 2. Nf3...", label_visibility="collapsed")

col_a, col_b = st.columns(2)
with col_a:
    st.write("Tu jouais avec :")
with col_b:
    couleur_radio = st.radio("", ["Blancs", "Noirs"], horizontal=True, label_visibility="collapsed")
    joueur_est_blanc = (couleur_radio == "Blancs")

st.markdown("---")

# --- ANALYSE ---
if st.button("🔍 Coach, explique moi !", type="primary", use_container_width=True):
    if not pgn_input:
        st.warning("Veuillez coller un PGN avant de continuer.")
        st.stop()
        
    game_obj = main.validate_pgn(pgn_input)
    if not game_obj:
        st.error("Le format PGN est invalide. Vérifiez votre copie.")
        st.stop()

    with st.spinner(f"{st.session_state.coach['nom']} analyse tes coups..."):
        try:
            # 1. Appel à l'IA
            rapport_ia = main.generate_analysis(
                pgn_input, 
                st.session_state.coach['id'], 
                prenom
            )
            
            # 2. Injection des images et diagrammes
            rapport_final = main.process_visuals(
                rapport_ia, 
                game_obj, 
                pgn_input, 
                joueur_est_blanc
            )
            
            # 3. Affichage direct (Sûr car le contenu est généré par ton code et Gemini)
            # On retire bleach qui bloque les images Base64 et les styles complexes
            st.markdown(rapport_final, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'analyse.")
            st.exception(e)
            
        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'analyse.")
            st.exception(e) # Pour le debug local

st.markdown("<br><br><center><small>Designé avec ❤️ par un joueur d'échecs pour des joueurs d'échecs</small></center>", unsafe_allow_html=True)