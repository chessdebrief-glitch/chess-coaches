
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

def run_analysis_flow(payload, analyzer):
    """
    Prend le payload (coach, user) et l'objet analyzer.
    Retourne le prompt final et le DataFrame filtré.
    """
    move_range = payload["analysis_settings"]["move_range"]
    
    # 1. On récupère les données formatées pour l'IA
    # On peut choisir le mode ici : soit tout, soit uniquement les moments critiques
    moments_critiques = analyzer.get_critical_moments()
    historique_compact = analyzer.export_for_ai(move_range)
    stats = analyzer.get_stats()

    # 2. Construction du Prompt (Logique à mettre dans PromptBuilder plus tard)
    # Pour l'instant on simule le retour du prompt
    prompt = f"""
    MENTOR: {payload['coach']['nom']} (Vibe: {payload['coach']['vibe']})
    ELEVE: {payload['user']['name']} ({payload['user']['elo']})
    
    STATS PARTIE: {stats}
    HISTORIQUE: {historique_compact}
    MOMENTS CLES: {moments_critiques}
    """
    
    return prompt, analyzer.get_analysis_slice(move_range)

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