
import io
import chess
import pandas as pd
from src.chess_preprocessor import get_segment_analysis

# src/analysis_engine.py

import pandas as pd
import re

def prepare_analysis_data(pgn_raw, move_range):
    # 1. TRANSFORMATION DU TEXTE EN OBJET CHESS GAME
    pgn_io = io.StringIO(pgn_raw)
    game = chess.pgn.read_game(pgn_io)
    
    if game is None:
        return pd.DataFrame(), {}

    start_move, end_move = move_range
    data = []
    node = game
    ply = 0
    prev_eval = 0.3  # Avantage blanc théorique au départ

    # 2. PARCOURS DE LA PARTIE
    while node.variations:
        next_node = node.variation(0)
        ply += 1
        
        move_number = (ply + 1) // 2
        turn = "White" if ply % 2 != 0 else "Black"
        notation = node.board().san(next_node.move)

        # Extraction de l'éval dans le commentaire [%eval 0.23]
        comment = next_node.comment
        current_eval = prev_eval
        
        match = re.search(r"\[%eval (-?\d+\.?\d*)\]", comment)
        if match:
            current_eval = float(match.group(1))
        
        # Calcul du Delta (différence avec le coup d'avant)
        delta = current_eval - prev_eval

        # Filtrage par la zone du slider
        if start_move <= move_number <= end_move:
            data.append({
                "move": move_number,
                "turn": turn,
                "notation": notation,
                "eval": current_eval,
                "delta": round(delta, 2)
            })

        prev_eval = current_eval
        node = next_node

    return pd.DataFrame(data), {"headers": game.headers}

def build_mentor_prompt(user, coach, move_range, segment):
    """Assemble le prompt final avec la 'vibe' du mentor."""
    h = segment.get("headers", {})
    role_user = "Blancs" if user['is_white'] else "Noirs"
    nom_adv = h.get('Black' if user['is_white'] else 'White', 'Adversaire')

    return f"""
# 🎭 IDENTITÉ : Tu es {coach['nom']} ({coach['vibe']})
# 👤 ÉLÈVE : {user['name']} ({user['elo']} ELO)
# ⚔️ MATCH : Contre {nom_adv} | Ouverture : {h.get('Opening', 'Inconnue')}

# 📝 DATA (Coups {move_range[0]} à {move_range[1]})
FEN : {segment.get('fen')}
Séquence : {segment.get('sequence')}

# 🎯 MISSION
Analyse cette séquence. Sois direct, pédagogique et garde ton style unique.
"""



# src/analysis_engine.py

def run_analysis_flow(payload):
    # 1. On génère le DataFrame ET on récupère l'objet game/headers
    df, extra_info = prepare_analysis_data(
        payload["analysis_settings"]["pgn_raw"],
        payload["analysis_settings"]["move_range"]
    )
    
    # 2. On prépare un dictionnaire "segment" compatible avec ton prompt
    # On reconstruit la séquence texte à partir du DataFrame propre
    sequence_string = " ".join([f"{row.move}.{row.notation}" for _, row in df.iterrows()])
    
    segment_compat = {
        "fen": extra_info.get("fen", "N/A"),
        "sequence": sequence_string,
        "headers": extra_info.get("headers", {})
    }
    
    # 3. On génère le prompt
    prompt = build_mentor_prompt(
        payload["user"], 
        payload["coach"], 
        payload["analysis_settings"]["move_range"],
        segment_compat
    )
    
    return prompt, df

def get_critical_moments(df, threshold=1.5):
    """
    Extrait les coups où l'évaluation a basculé de plus de 'threshold' pions.
    """
    if df.empty:
        return df
    
    # On calcule la valeur absolue de l'écart
    df['abs_delta'] = df['delta'].abs()
    
    # On trie par les plus gros écarts
    blunders = df[df['abs_delta'] >= threshold].sort_values(by='abs_delta', ascending=False)
    
    return blunders