# chess_processor.py
import chess.pgn
import io

def get_segment_analysis(pgn_text, start_move, window_size):
    """
    Extrait une portion précise de la partie.
    start_move: coup de début (ex: 20)
    window_size: nombre de coups à analyser (ex: 10)
    """
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    board = game.board()
    moves = list(game.mainline_moves())
    
    # 1. On avance jusqu'au point de départ
    for move in moves[:start_move]:
        board.push(move)
    
    # 2. On capture le FEN à ce moment précis
    starting_fen = board.fen()
    
    # 3. On extrait la séquence de coups avec eval (si dispo)
    segment_data = []
    node = game.navigate(moves[:start_move]) # On se place au bon endroit
    
    for i in range(window_size):
        if not node.mainline_moves():
            break
        next_node = node.variation(0)
        move_uci = next_node.move.uci()
        
        # Récupération de l'évaluation stockée dans le commentaire [%eval ...]
        comment = next_node.comment
        segment_data.append(f"Coup {start_move + i + 1}: {move_uci} (Eval: {comment})")
        node = next_node
        
    return {
        "fen": starting_fen,
        "sequence": "\n".join(segment_data)
    }