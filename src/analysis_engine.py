# src/analysis_engine.py
from src.chess_preprocessor import get_segment_analysis
# src/analysis_engine.py

def run_analysis_flow(payload):
    user = payload["user"]  # Infos de l'UI (nom, elo, is_white)
    coach = payload["coach"]
    settings = payload["analysis_settings"]
    
    segment = get_segment_analysis(
        settings["pgn_raw"], 
        start_move=settings["move_range"][0] - 1, 
        window_size=settings["move_range"][1] - settings["move_range"][0] + 1
    )
    
    h = segment.get("headers", {})
    
    # On identifie qui est l'adversaire dans le PGN pour que le coach puisse le citer
    role_user = "Blancs" if user['is_white'] else "Noirs"
    nom_adversaire = h.get('black') if user['is_white'] else h.get('white')
    elo_adversaire = h.get('black_elo') if user['is_white'] else h.get('white_elo')

    full_prompt = f"""
# 🎭 TON IDENTITÉ ET STYLE
Tu es {coach['nom']}.
Ton style : {coach['vibe']}
Ta mission : {coach['desc']}

# 👤 LE DEMANDEUR (TON ÉLÈVE)
- **Surnom :** {user['name']}
- **Niveau déclaré :** {user['elo']} ELO
- **Camp joué dans cette partie :** {role_user}

# ⚔️ CONTEXTE DU MATCH (DATA PGN)
- **Adversaire :** {nom_adversaire} ({elo_adversaire} ELO)
- **Événement :** {h.get('event', 'N/A')}
- **Ouverture :** {h.get('opening', 'Inconnue')}
- **Résultat global :** {h.get('result', '*')}

# 📝 ANALYSE DE LA SÉQUENCE (Coups {settings['move_range'][0]} à {settings['move_range'][1]})
FEN de départ : `{segment.get('fen', '')}`
Coups et évaluations :
{segment.get('sequence', 'Aucune séquence')}

# 🎯 INSTRUCTIONS DE RÉPONSE
1. Adresse-toi directement à **{user['name']}**.
2. Compare son niveau ({user['elo']}) à la difficulté de la séquence.
3. Si {user['name']} a fait une erreur face à {nom_adversaire}, explique-lui pourquoi sans pitié mais avec ton style {coach['nom']}.
"""
    
    return full_prompt