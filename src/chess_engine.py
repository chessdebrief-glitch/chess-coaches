import chess.pgn
import io
import re

import chess.pgn
import io

def validate_pgn(pgn_string):
    """
    Valide une chaîne PGN et la charge en tant qu'objet partie.

    Retourne un tuple (game, error_message).
    - Si la validation réussit, retourne (objet game, None).
    - Si la validation échoue, retourne (objet game partiel ou None, message d'erreur).
    """
    # 1. On élimine le vide ou les espaces
    if not pgn_string or not pgn_string.strip():
        return None, "Le PGN fourni est vide."
    pgn_io = io.StringIO(pgn_string)
    
    # 2. Tentative de lecture par le parser
    try:
        game = chess.pgn.read_game(pgn_io)
    except Exception as e:
        return None, f"Erreur lors de la lecture du PGN: {e}"
    # 3. Si le parser n'a rien trouvé (ex: texte aléatoire)
    if game is None:
        return None, "Format PGN invalide ou texte illisible."
    # 4. On vérifie s'il y a des erreurs de syntaxe (ex: 1. e55)
    if game.errors:
        return game, f"Erreur de syntaxe dans le PGN : {game.errors[0]}"

# 5. On vérifie que le jeu contient des données
    # On accepte le jeu si : il y a des coups OU si un header au moins est rempli (pas "?")
    has_moves = not game.is_end()
    # On vérifie si au moins un des headers standards contient autre chose que "?"
    important_headers = ["Event", "White", "Black", "FEN"]
    has_headers = any(game.headers.get(h, "?") != "?" for h in important_headers)

    if not has_moves and not has_headers:
        return game, "Le PGN ne contient ni en-têtes valides ni coups."

    # 6. Vérification des coups légaux
    board = game.board()
    try:
        for move in game.mainline_moves():
            if move not in board.legal_moves:
                return game, f"Coup illégal détecté: {move.uci()}"
            board.push(move)
    except Exception as e:
        return game, f"Erreur lors de la vérification des coups légaux: {e}"

    # Si tout est en ordre
    return game, None

def extract_evals(game):
    evals = [0.0]
    node = game
    while node.mainline_moves():
        node = node.variation(0)
        match = re.search(r"\[%eval ([-#.\d]+)\]", node.comment)
        if match:
            val = match.group(1)
            evals.append(10.0 if "#" in val else float(val))
        else:
            evals.append(evals[-1])
    return evals