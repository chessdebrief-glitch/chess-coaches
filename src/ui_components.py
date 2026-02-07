# ui_components.py
import re
import streamlit as st
from html import escape # Plus léger que bleach pour des simples chaînes
import streamlit.components.v1 as components
from src.utils import extract_clean_text

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

def elo_selector():
    """Composant de sélection du niveau ELO."""
    # On utilise une colonne pour centrer ou ajuster le slider
    elo = st.slider(
        label="Glisse pour définir ton niveau",
        min_value=1000,
        max_value=2500,
        value=1500,
        step=50,
        help="Ceci aide le coach à adapter ses explications à ton niveau technique."
    )
    
    # Petit feedback visuel sur le niveau
    if elo < 1400:
        label = "Débutant / Intermédiaire"
    elif elo < 1900:
        label = "Confirmé"
    else:
        label = "Expert / Maître"
        
    st.info(f"Niveau configuré : **{elo}** ({label})")
    return elo

def display_debug_data(df):
    """Affiche proprement le DataFrame pour le debugging."""
    if df is None or df.empty:
        st.warning("⚠️ Aucune donnée à afficher pour le moment.")
        return

    with st.expander("🛠️ Debug : Inspection du DataFrame (Pandas)"):
        st.write("Voici les données extraites pour l'analyse :")
        
        # On stylise un peu pour repérer les grosses variations d'éval
        # (Delta négatif = erreur du joueur si on est Blanc)
        st.dataframe(
            df.style.background_gradient(subset=['eval'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        # Petit résumé technique
        cols = st.columns(3)
        cols[0].metric("Nombre de positions", len(df))
        if 'eval' in df.columns:
            cols[1].metric("Eval Max", f"{df['eval'].max():.2f}")
            cols[2].metric("Eval Min", f"{df['eval'].min():.2f}")


# src/ui_components.py

def display_critical_moments(df):
    blunders = df[df['delta'].abs() >= 1.5] # Seuil de gaffe
    
    if not blunders.empty:
        st.error(f"🚨 {len(blunders)} moment(s) critique(s) détecté(s) !")
        # On affiche un tableau simplifié
        st.table(blunders[['move', 'turn', 'notation', 'delta']])

def display_critical_moment_card222(analyzer, moment, is_white):
    """Affiche une carte élégante pour un moment critique avec image Lichess."""
    
    # On crée un container avec une bordure pour isoler le moment
    with st.container(border=True):
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            # On récupère l'URL de l'image via l'analyzer
            img_url = analyzer.get_lichess_image_url(
                moment['move'], 
                orientation_white=is_white
            )
            if img_url:
                st.image(img_url, use_container_width=True)
            else:
                st.warning("Image indisponible")
                
        with col2:
            # Badge de couleur pour le label
            color = "red" if moment['label'] == "Blunder" else "orange"
            st.markdown(f"### Coup {moment['move']} : :{color}[{moment['label']}]")
            
            st.markdown(f"**Coup joué :** `{moment['notation']}`")
            st.markdown(f"**Impact :** `Delta {moment['delta']}`")
            
            # Bouton d'action pour aller plus loin
            fen_url = f"https://lichess.org/analysis/{moment['fen'].replace(' ', '_')}"
            st.link_button("🔍 Analyser sur Lichess", fen_url, use_container_width=True)

def display_critical_moment_card333(analyzer, moment, is_white):
    # On récupère la FEN AVANT le coup
    fen_before = analyzer.get_fen_before_move(moment['move'])
    fen_pieces_only = fen_before.split(' ')[0]
    
    orientation = 'white' if is_white else 'black'

    with st.container(border=True):
        st.markdown(f"### 🧩 Défi : Coup {moment['move']}")
        
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            # L'échiquier montre la position AVANT l'erreur
            html_board = f"""
            <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
            <div id="board_{moment['move']}" style="width: 100%; max-width: 280px; margin: auto;"></div>
            <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
            <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
            <script>
                var board = Chessboard("board_{moment['move']}", {{
                    position: '{fen_pieces_only}',
                    orientation: '{orientation}',
                    draggable: false,
                    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png'
                }});
            </script>
            """
            components.html(html_board, height=300)
            
        with col2:
            st.write("**La situation :**")
            st.write(f"C'est aux {'Blancs' if moment['turn'] == 'White' else 'Noirs'} de jouer.")
            
            # On cache le coup joué dans un expander pour ne pas spoiler tout de suite
            with st.expander("Voir ce que tu as joué..."):
                st.write(f"Tu as joué : **{moment['notation']}**")
                st.write(f"Critique : :{ 'red' if moment['label'] == 'Blunder' else 'orange'}[{moment['label']}]")
                st.write(f"Perte d'évaluation : {moment['punishment']} pions")

            # Bouton pour aller voir la solution
            url_solution = f"https://lichess.org/analysis/{fen_before.replace(' ', '_')}"
            st.link_button("💡 Voir la solution", url_solution, use_container_width=True)

def display_critical_moment_card(analyzer, moment, is_white):
    # 1. On récupère la FEN AVANT le coup fautif
    fen_before = analyzer.get_fen_before_move(moment['move'])
    fen_pieces_only = fen_before.split(' ')[0]
    
    # 2. L'orientation doit être celle du joueur (pour qu'il voie l'échiquier de son point de vue)
    orientation = 'white' if is_white else 'black'

    with st.container(border=True):
        st.markdown(f"### 🧩 Défi : Coup {moment['move']}")
        
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            html_board = f"""
            <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
            <div id="board_{moment['move']}" style="width: 100%; max-width: 280px; margin: auto;"></div>
            <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
            <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
            <script>
                var board = Chessboard("board_{moment['move']}", {{
                    position: '{fen_pieces_only}',
                    orientation: '{orientation}',
                    draggable: false,
                    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png'
                }});
            </script>
            """
            components.html(html_board, height=300)
            
        with col2:
            # Correction ici : moment['turn'] indique qui a joué le coup. 
            # Si c'est un moment critique pour vous, c'est à vous de jouer.
            trait_au_joueur = "Blancs" if moment['turn'] == "White" else "Noirs"
            
            st.write(f"**Le trait est aux {trait_au_joueur}**")
            st.info("Quelle est la meilleure suite ici ?")
            
            with st.expander("Voir ton erreur..."):
                st.write(f"Tu as joué : **{moment['notation']}**")
                color = "red" if moment['label'] == 'Blunder' else "orange"
                st.markdown(f"Critique : :{color}[{moment['label']}]")
                st.write(f"Perte : {abs(moment['delta']):.1f} pions")

            url_solution = f"https://lichess.org/analysis/{fen_before.replace(' ', '_')}"
            st.link_button("💡 Voir la solution", url_solution, use_container_width=True)


def display_moments(analyzer, moments, is_white):
    """Affiche la section complète des moments critiques avec titre dynamique."""
    st.divider()
    
    # Titre dynamique selon la couleur sélectionnée
    if is_white == st.session_state.joueur_est_blanc:
        titre = "🎯 Zoom sur tes erreurs"
    else:
        titre = "🎯 Zoom sur les erreurs de ton adversaire"
        
    st.subheader(titre)
    
    if not moments:
        st.info("Aucune erreur majeure détectée. Beau jeu ! Ton mentor est presque impressionné.")
        return

    # Affichage des cartes
    for m in moments:
        display_critical_moment_card(analyzer, m, is_white)


# Dans src/ui_components.py

def render_pgn_section(mentor):
    """Gère l'affichage de la zone PGN et retourne le texte saisi."""
    step_title(4, mentor.get_punchline('pgn', "Donne-moi ta partie."))
    
    col_toggle, _ = st.columns([1, 2])
    with col_toggle:
        label_couleur = "⚪ BLANCS" if st.session_state.joueur_est_blanc else "⚫ NOIRS"
        st.toggle(label_couleur, key="joueur_est_blanc")

    return st.text_area(
        "PGN", 
        height=150, 
        placeholder="1. e4 e5...", 
        label_visibility="collapsed"
    )

def render_analysis_results(mentor, resultat_analyse, analyzer, move_range):
    """Affiche uniquement les graphiques et stats techniques."""
    st.markdown("---")
    
    # 1. Le Graphique (maintenant il sera toujours là)
    st.subheader("📈 Courbe d'évaluation")
    fig = analyzer.generate_eval_chart(move_range)
    if fig:
        st.pyplot(fig)
    else:
        st.warning("Impossible de générer le graphique d'évaluation.")

    # 2. Les Stats (Optionnel : si tu as une fonction pour ça)
    # ui_components.display_game_stats(analyzer) 

    # --- IMPORTANT : On a supprimé le st.markdown(resultat_analyse) ici ---
    # Car il est géré par render_smart_analysis juste après dans app.py

def render_smart_analysis(raw_res, analyzer, is_white):
    """
    Transforme la réponse brute de l'IA en une analyse riche avec échiquiers.
    """
    # 1. UTILISATION DU FILTRE (La "petite fonction")
    text = extract_clean_text(raw_res)
    
    if not text:
        return

    # 2. LOGIQUE DE DÉCOUPAGE (Ta "grosse fonction")
    # On découpe le texte autour des tags [BOARD_MOVE_12]
    parts = re.split(r'(\[BOARD_MOVE_\d+(?:_white|_black)?\])', text)

    for part in parts:
        match = re.search(r'BOARD_MOVE_(\d+)', part)
        
        if match:
            move_num = int(match.group(1))
            # Extraction des données depuis l'analyzer
            row = analyzer.df[analyzer.df['move'] == move_num]
            
            if not row.empty:
                r = row.iloc[0]
                moment = {
                    'move': int(r['move']),
                    'turn': r['turn'],
                    'notation': r['notation'],
                    'delta': r['delta'],
                    'label': "Analyse Clé",
                    'punishment': abs(r['delta']),
                    'fen': r['fen']
                }
                # Rendu visuel de l'échiquier
                display_critical_moment_card(analyzer, moment, is_white)
            else:
                st.caption(f"(Position du coup {move_num} introuvable)")
        
        else:
            # Rendu du texte normal entre les échiquiers
            # On en profite pour nettoyer les placeholders résiduels
            clean_text = part.replace("{{CHART_EVAL_TENSION}}", "")
            st.markdown(clean_text, unsafe_allow_html=True)

def display_game_header(analyzer):
    """Affiche un bandeau avec les infos réelles du match."""
    # Extraction des données depuis les headers du PGN
    white = analyzer.headers.get("White", "Joueur Blanc")
    black = analyzer.headers.get("Black", "Joueur Noir")
    white_elo = analyzer.headers.get("WhiteElo", "?")
    black_elo = analyzer.headers.get("BlackElo", "?")
    result = analyzer.headers.get("Result", "*")
    date = analyzer.headers.get("Date", "????.??.??")
    event = analyzer.headers.get("Event", "Partie amicale")

    # Style visuel du bandeau
    st.markdown(f"#### 🏆 {event} ({date})")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown(f"⚪ **{white}**")
        st.caption(f"Rating: {white_elo}")
        
    with col2:
        st.markdown(f"<div style='text-align: center; font-size: 24px; font-weight: bold;'>{result}</div>", unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"<div style='text-align: right;'>⚫ **{black}**</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right; color: gray; font-size: 0.8em;'>Rating: {black_elo}</div>", unsafe_allow_html=True)
    
    st.divider()