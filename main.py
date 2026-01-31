import os
import streamlit as st  # Pour les secrets si besoin
import re
import io
import base64
import chess
import chess.pgn
import chess.svg
import matplotlib.pyplot as plt

# Les imports LangChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION API ---
# Assure-toi que ta clé est bien dans tes variables d'environnement
os.environ["GOOGLE_API_KEY"] = "TON_API_KEY_ICI"

def setup_folders():
    """Crée les dossiers nécessaires si besoin."""
    if not os.path.exists("temp"):
        os.makedirs("temp")

def validate_pgn(pgn_string):
    """Vérifie si le PGN est valide et retourne l'objet game."""
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    return game

def generate_eval_chart(pgn_string):
    """
    Génère un graphique d'évolution factice basé sur le nombre de coups.
    Note : Pour une vraie évaluation, il faudrait interfacer Stockfish.
    """
    game = validate_pgn(pgn_string)
    moves = list(game.mainline_moves())
    
    # Simulation d'une courbe d'évaluation (à remplacer par Stockfish pour du réel)
    evals = [0]
    current = 0
    for i in range(len(moves)):
        current += (0.5 - (i % 3 == 0)) # Simule des fluctuations
        evals.append(current)

    plt.figure(figsize=(8, 3), facecolor='#1e1e1e')
    plt.plot(evals, color='#2196F3', linewidth=2)
    plt.fill_between(range(len(evals)), evals, color='#2196F3', alpha=0.2)
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close()
    data = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return f"""
    <div style="text-align:center; background:#1e1e1e; border-radius:10px; padding:10px; border:1px solid #333; margin:20px 0;">
        <p style="color:#aaa; font-size:0.8rem; margin-bottom:5px;">ÉVOLUTION DE LA TENSION</p>
        <img src="data:image/png;base64,{data}" style="width:100%; max-width:600px;"/>
    </div>
    """

def generate_chess_diagram(game_obj, move_number, orientation_white=True):
    """Génère l'image SVG d'une position précise du match."""
    board = game_obj.board()
    moves = list(game_obj.mainline_moves())
    
    # On avance jusqu'au coup X
    for i in range(min(move_number, len(moves))):
        board.push(moves[i])
    
    orientation = chess.WHITE if orientation_white else chess.BLACK
    
    # Style personnalisé du plateau
    svg_data = chess.svg.board(
        board, 
        orientation=orientation, 
        size=350,
        style="""
            .square.light { fill: #eae9d2; }
            .square.dark { fill: #4b7399; }
            .check { fill: url(#check_grad); }
        """
    )
    
    b64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
    return f"""
    <div style="text-align:center; margin:25px 0;">
        <img src="data:image/svg+xml;base64,{b64}" style="border:5px solid #333; border-radius:5px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);" width="300" />
        <p style="color:#666; font-size:0.7rem; margin-top:5px;">Position au coup {move_number}</p>
    </div>
    """

def generate_analysis(pgn_text, coach_id, user_name):
    """Appelle l'IA Gemini pour générer le texte du rapport."""
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    
    # On récupère la personnalité du coach
    coach_data = next((m for m in MENTORS if m["id"] == coach_id), MENTORS[1])
    
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm
    
    response = chain.invoke({
        "pgn": pgn_text,
        "coach_nom": coach_data["nom"],
        "coach_style": coach_data["desc"],
        "user_name": user_name
    })
    
    return response.content

def process_visuals(rapport_ia, game_obj, pgn, joueur_est_blanc):
    """Remplace les balises texte par du HTML (images et graphiques)."""
    md_text = rapport_ia
    
    # 1. Remplacement du graphique d'évaluation
    if "CHART_EVAL_TENSION" in md_text:
        chart_html = generate_eval_chart(pgn)
        md_text = re.sub(r'\{{1,2}\s?CHART_EVAL_TENSION\s?\}{1,2}', chart_html, md_text)

    # 2. Remplacement des diagrammes de moments clés
    # Capture {DIAGRAM_MOMENT_12_B} ou {{ DIAGRAM_MOMENT_5_N }}
    pattern = re.compile(r"\{{1,2}\s?DIAGRAM_MOMENT_(\d+)_([BN])\s?\}{1,2}")
    
    def replace_with_diagram(match):
        num_coup = int(match.group(1))
        # On force l'orientation choisie par l'utilisateur au départ
        return generate_chess_diagram(game_obj, num_coup, joueur_est_blanc)

    md_text = pattern.sub(replace_with_diagram, md_text)
    
    return md_text