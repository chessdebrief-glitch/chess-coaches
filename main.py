import streamlit as st
from google import genai
from google.genai import types
import chess.pgn
import io
import re
import os
import chess.svg
from cairosvg import svg2png
import matplotlib.pyplot as plt
import base64

# --- UTILITAIRES SYSTÈME ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return None

def setup_folders():
    for folder in ['data', 'temp', 'exports']:
        if not os.path.exists(folder):
            os.makedirs(folder)

def get_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)

# --- LOGIQUE COACH & IA ---
def generate_analysis(pgn_data, coach_id, player_name):
    client = get_client()
    
    personalities = {
        "vladimir": "Ton ton est froid, sarcastique et extrêmement exigeant. Tu considères toute imprécision comme une insulte au jeu d'échecs.",
        "satori": "Ton ton est calme, philosophique. Tu parles d'équilibre, de flux et d'harmonie des pièces.",
        "titi": "Tu es familier, tu charries l'élève sur ses gaffes comme si vous étiez au bar du club."
    }
    
    coach_style = personalities.get(coach_id, "Tu es un coach expert et pédagogue.")

    sys_instruction = f"""
Rôle : Tu es un moteur d'analyse d'échecs technique et un coach expert.
Personnalité : {coach_style}
Cible : Tu t'adresses directement à {player_name} (l'élève).

Contraintes :
- Pas d'introduction ni de conclusion.
- Notation algébrique française (Cf3, d5).
- Placeholders : {{DIAGRAM_MOMENT_XX_Y}}, {{CHART_EVAL_TENSION}}, {{STATS_TABLE}}.

Structure :
# Chapitre 1 : Identité de la partie
* Noms, Date, Résultat.
{{CHART_EVAL_TENSION}}
{{STATS_TABLE}}

# Chapitre 2 : Ouverture
* Nom et code ECO. Verdict. {{DIAGRAM_MOMENT_XX_Y}}

# Chapitre 3 : Moments Critiques
## Erreur au coup XX
{{DIAGRAM_MOMENT_XX_Y}}
* Analyse et alternative.

# Chapitre 4 : Profil & Progrès
* Style et exercice final : {{DIAGRAM_MOMENT_XX_Y}}
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"Voici le PGN de la partie de {player_name} :\n{pgn_data}",
        config=types.GenerateContentConfig(system_instruction=sys_instruction)
    )
    return response.text

# --- RENDU VISUEL ---
def generate_stats_html(w, b):
    def row(label, val_w, val_b, color="#aaa"):
        return f"""
        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333;">
            <div style="width: 30%; text-align: left; color: white; font-weight: bold;">{val_w}</div>
            <div style="width: 40%; text-align: center; color: {color}; font-size: 0.85em; text-transform: uppercase;">{label}</div>
            <div style="width: 30%; text-align: right; color: white; font-weight: bold;">{val_b}</div>
        </div>"""

    return f"""
    <div style="background-color: #262730; padding: 20px; border-radius: 8px; max-width: 500px; margin: 20px auto; border: 1px solid #3c3f41;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 15px; border-bottom: 2px solid #444; padding-bottom: 10px; color: white; font-weight: bold;">
            <span>BLANCS</span><span>VS</span><span>NOIRS</span>
        </div>
        {row("Précision", f"{w['acc']}%", f"{b['acc']}%", "#00ff00")}
        {row("Gaffes ‼️", w['gaffes'], b['gaffes'], "#ff5555")}
        {row("Erreurs ❓", w['err'], b['err'], "#ff8000")}
        {row("Imprécisions ?!", w['imp'], b['imp'], "#f1c40f")}
        {row("Perte ACPL", w['acpl'], b['acpl'], "#3498db")}
    </div>"""

def generate_eval_chart(pgn_text):
    game = validate_pgn(pgn_text)
    if not game: return ""

    evals = [0.0]
    for node in game.mainline():
        score = extract_eval_from_comment(node.comment)
        if score is not None:
            evals.append(max(min(score, 10), -10))
    
    if len(evals) <= 1: return "*(Pas de données d'analyse)*"

    plt.figure(figsize=(10, 3), facecolor='none')
    x = range(len(evals))
    plt.fill_between(x, evals, 0, where=[e >= 0 for e in evals], color='white', alpha=0.3, interpolate=True)
    plt.fill_between(x, evals, 0, where=[e <= 0 for e in evals], color='black', alpha=0.3, interpolate=True)
    plt.plot(x, evals, color="#2196F3", linewidth=2)
    plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    plt.title("Évolution de l'avantage", color="white", fontsize=12)
    plt.ylim(-11, 11)
    plt.yticks([-10, -5, 0, 5, 10], ["Mat (N)", "-5", "0", "+5", "Mat (B)"], color="gray", fontsize=8)
    
    chart_path = "temp/tension_chart.png"
    plt.savefig(chart_path, transparent=True, bbox_inches='tight', dpi=120)
    plt.close()
    
    img_b64 = get_image_base64(chart_path)
    return f'<img src="{img_b64}" style="width:100%; border-radius:8px; background-color: #1e1e1e; padding: 10px; margin: 15px 0;">'

def process_visuals(md_text, game, pgn_raw):
    """Transforme les balises Gemini en visuels Chess et force le rendu HTML."""
    
    # 1. Rendu du graphique d'évaluation
    if "{CHART_EVAL_TENSION}" in md_text or "{{CHART_EVAL_TENSION}}" in md_text:
        res = generate_eval_chart(pgn_raw)
        # On ajoute des sauts de ligne pour éviter que le Markdown ne "mange" le HTML
        res_wrapped = f"\n\n{res}\n\n"
        md_text = md_text.replace("{{CHART_EVAL_TENSION}}", res_wrapped).replace("{CHART_EVAL_TENSION}", res_wrapped)

    # 2. Rendu du tableau de statistiques
    if "{STATS_TABLE}" in md_text or "{{STATS_TABLE}}" in md_text:
        # Valeurs de test (à rendre dynamiques plus tard)
        w_stats = {'acc': 80, 'acpl': 53, 'gaffes': 3, 'err': 3, 'imp': 8}
        b_stats = {'acc': 85, 'acpl': 42, 'gaffes': 1, 'err': 2, 'imp': 5}
        
        res = generate_stats_html(w_stats, b_stats)
        
        # CRUCIAL : Isoler le bloc HTML avec des doubles sauts de ligne
        # et supprimer les indentations que Gemini pourrait ajouter
        res_wrapped = f"\n\n{res.strip()}\n\n"
        
        md_text = md_text.replace("{{STATS_TABLE}}", res_wrapped).replace("{STATS_TABLE}", res_wrapped)

    # 3. Rendu des diagrammes d'échiquier
    pattern = r"\{{1,2}DIAGRAM_MOMENT_(\d+)_([BN])\}{1,2}"
    for match in re.finditer(pattern, md_text):
        full_tag, move_num, color = match.group(0), match.group(1), match.group(2)
        image_path = f"temp/diag_{move_num}_{color}.png"
        board = game.board()
        target_ply = int(move_num) * 2 - (1 if color == 'B' else 0)
        moves = list(game.mainline_moves())
        for i in range(min(target_ply, len(moves))):
            board.push(moves[i])
            
        svg_data = chess.svg.board(board, size=350, orientation=(chess.WHITE if color == 'B' else chess.BLACK), coordinates=True)
        svg2png(bytestring=svg_data, write_to=image_path)
        img_b64 = get_image_base64(image_path)
        md_text = md_text.replace(full_tag, f"![Position]({img_b64})")

    # --- NETTOYAGE FINAL ANTI-TEXTE BRUT ---
    # 1. Supprime les balises de code Markdown injectées par l'IA
    md_text = md_text.replace("```html", "").replace("```HTML", "").replace("```", "")
    
    # 2. On s'assure qu'aucune ligne HTML ne commence par un espace (ce qui déclencherait le mode "code")
    lines = md_text.split("\n")
    cleaned_lines = [line.lstrip() if line.lstrip().startswith("<div") or line.lstrip().startswith("<img") else line for line in lines]
    md_text = "\n".join(cleaned_lines)
    
    return md_text

# --- ANALYSE PGN ---
def validate_pgn(pgn_str):
    pgn_io = io.StringIO(pgn_str.strip())
    game = chess.pgn.read_game(pgn_io)
    return game if game and any(game.mainline_moves()) else None

def extract_eval_from_comment(comment):
    match = re.search(r"\[%eval (-?\d+\.?\d*)\]", comment)
    if match: return float(match.group(1))
    if "#" in comment: return 10.0 if "+" in comment or "#-" not in comment else -10.0
    return None