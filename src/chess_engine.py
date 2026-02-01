import chess.pgn
import io
import re

import chess.pgn
import io

def validate_pgn(pgn_string):
    # 1. On élimine le vide ou les espaces
    if not pgn_string or not pgn_string.strip():
        return None
        
    pgn_io = io.StringIO(pgn_string)
    
    # 2. Tentative de lecture par le parser
    game = chess.pgn.read_game(pgn_io)
    
    # 3. Si le parser n'a rien trouvé (ex: texte aléatoire)
    if game is None:
        return None

    # 4. On vérifie s'il y a des erreurs de syntaxe (ex: 1. e55)
    if game.errors:
        return None

    # 5. On vérifie que le jeu n'est pas "vide" (au moins un coup ou des en-têtes)
    # Si on veut forcer la présence de coups, on peut utiliser : if not game.move_stack
    if not game.headers and not list(game.mainline()):
        return None

    return game

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