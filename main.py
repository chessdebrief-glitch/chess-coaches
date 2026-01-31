import re
import chess_engine
import visualizer
import ai_engine
from constants import MENTORS

def get_analysis(pgn_text, coach_id, user_name):
    coach_data = next((m for m in MENTORS if m["id"] == coach_id), MENTORS[1])
    return ai_engine.call_gemini(pgn_text, coach_data, user_name)

def _process_visuals(text, game, pgn, joueur_est_blanc):
    """Remplace les balises {{...}} par du HTML visuel"""
    
    # Remplacement du graphique de tension
    if "{{CHART_EVAL_TENSION}}" in text:
        evals = chess_engine.extract_evals(game)
        chart_html = visualizer.generate_chart_html(evals)
        text = text.replace("{{CHART_EVAL_TENSION}}", chart_html)

    # Remplacement des diagrammes dynamiques
    # Cherche par exemple {{DIAGRAM_MOMENT_12_B}}
    pattern = re.compile(r"\{\{\s?DIAGRAM_MOMENT_(\d+)_([BN])\s?\}\}")
    
    def replace_with_diagram(match):
        num_coup = int(match.group(1))
        # On passe l'objet game et le numéro du coup au visualizer
        return visualizer.generate_svg_board(game, num_coup, joueur_est_blanc)

    final_text = pattern.sub(replace_with_diagram, text)
    
    return final_text

def run_full_analysis(pgn_text, user_name, coach_data, joueur_est_blanc):
    """
    Fonction principale appelée par app.py.
    Orchestre l'analyse IA et l'injection des visuels.
    """
    # 1. Valider le PGN via le moteur d'échecs
    game = chess_engine.validate_pgn(pgn_text)
    if not game:
        return "❌ Erreur : Le PGN fourni est invalide."

    # 2. Appeler l'IA pour générer le rapport brut (avec les balises {{...}})
    rapport_ia = ai_engine.call_gemini(pgn_text, coach_data, user_name, debug_mode=True)

    # 3. Injecter les visuels (Graphiques et Diagrammes)
    rapport_final = _process_visuals(rapport_ia, game, pgn_text, joueur_est_blanc)
    
    return rapport_final