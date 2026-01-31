import chess_engine
import visualizer
import ai_engine
from constants import MENTORS

def get_analysis(pgn_text, coach_id, user_name):
    coach_data = next((m for m in MENTORS if m["id"] == coach_id), MENTORS[1])
    return ai_engine.call_gemini(pgn_text, coach_data, user_name)

def process_visuals(rapport_raw, pgn_text, joueur_est_blanc):
    game = chess_engine.validate_pgn(pgn_text)
    # On remplace les placeholders par les appels au visualizer
    # ... logique de re.sub ici ...
    return final_report

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
    rapport_ia = ai_engine.call_gemini(pgn_text, coach_data, user_name)

    # 3. Injecter les visuels (Graphiques et Diagrammes)
    rapport_final = _process_visuals(rapport_ia, game, pgn_text, joueur_est_blanc)
    
    return rapport_final