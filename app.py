import streamlit as st
import main
import os

# Initialisation automatique des dossiers au lancement
main.setup_folders()

# 1. On définit le dictionnaire de mapping (Texte affiché : Clé technique)
COACHS_DISPO = {
    "Satori 🧘 - Le Maître Zen": "satori",
    "Vladimir 🇷🇺 - Le GM Russe Impitoyable": "vladimir",
    "Titi 🍻 - Le pote chambreur du club": "titi"
}

# Configuration de la page
st.set_page_config(page_title="Chess Coaches", page_icon="♟️")

st.title("♟️ Chess Coaches")
st.subheader("L'analyse pédagogique (et personnalisée) de vos parties")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("Configuration")
    prenom = st.text_input("Ton prénom", placeholder="Ex: Garry")
    
    couleur = st.radio(
        "Tu jouais avec les :",
        ["Blancs", "Noirs"],
        index=0
    )
    
    # On utilise les clés du dictionnaire pour l'affichage
    nom_coach_choisi = st.radio(
        "Choisis ton coach :",
        list(COACHS_DISPO.keys())
    )
    
    # On récupère l'ID technique (ex: "vladimir") pour l'envoyer au moteur
    coach_id = COACHS_DISPO[nom_coach_choisi]
    
    st.divider()
    st.caption("Astuce : Exportez depuis Lichess avec 'Analyse Ordinateur'.")

# --- ZONE PRINCIPALE ---
st.write(f"### Bienvenue {prenom if prenom else 'champion'} !")
st.write(f"Ton coach **{nom_coach_choisi.split(' ')[0]}** examine tes coups...")

# Zone pour le PGN
pgn_input = st.text_area(
    "Colle ton PGN ici :",
    placeholder="[Event 'Live Chess']\n1. e4 e5 2. Nf3...",
    height=200
)

if st.button("Lancer l'Analyse"):
    if pgn_input:
        game_obj = main.validate_pgn(pgn_input)
        
        if game_obj:
            with st.spinner(f"Analyse en cours avec {nom_coach_choisi.split(' ')[0]}..."):
                try:
                    # 1. On envoie l'ID technique (vladimir, satori...) au lieu du long texte
                    rapport_brut = main.generate_analysis(pgn_input, coach_id, prenom)

                    # 2. Injection des visuels (diagrammes + courbe)
                    rapport_visuel = main.process_visuals(rapport_brut, game_obj, pgn_input)

                    # 3. Affichage final
                    st.divider()
                    st.markdown(rapport_visuel, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Détails de l'erreur : {e}")
        else:
            st.error("PGN invalide. Vérifiez le texte collé.")
    else:
        st.warning("Veuillez coller un PGN.")