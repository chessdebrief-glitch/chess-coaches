import chess.pgn
import io

def get_segment_analysis(pgn_text, start_move, window_size):
    """
    Extrait une portion précise de la partie sans erreur d'attribut.
    """
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return {"fen": "", "sequence": "Erreur de lecture PGN"}

    headers = {
        "white": game.headers.get("White", "Inconnu"),
        "black": game.headers.get("Black", "Inconnu"),
        "white_elo": game.headers.get("WhiteElo", "?"),
        "black_elo": game.headers.get("BlackElo", "?"),
        "opening": game.headers.get("Opening", "Inconnue"),
        "event": game.headers.get("Event", "Partie amicale"),
        "result": game.headers.get("Result", "*"),
        "time_control": game.headers.get("TimeControl", "N/A")
    }

    # 1. On avance jusqu'au point de départ pour obtenir le FEN
    node = game
    moves = list(game.mainline_moves())
    
    # On avance le 'node' jusqu'au coup start_move
    for i in range(min(start_move, len(moves))):
        node = node.next()
    
    # On capture le FEN à ce moment précis
    starting_fen = node.board().fen()
    
    # 2. On extrait la séquence de coups à partir de ce node
    segment_data = []
    current_node = node
    
    for i in range(window_size):
        next_node = current_node.next()
        if next_node is None:
            break
            
        move_san = current_node.board().san(next_node.move)
        
        # Récupération de l'évaluation propre
        eval_str = "Pas d'éval"
        if next_node.comment:
            # On cherche souvent l'eval dans le commentaire
            eval_str = next_node.comment
            
        segment_data.append(f"Coup {start_move + i + 1}: {move_san} (Eval: {eval_str})")
        current_node = next_node
        
    return {
        "fen": starting_fen,
        "sequence": "\n".join(segment_data),
        "headers": headers # On ajoute les headers au dictionnaire de retour
    }