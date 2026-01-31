import chess.pgn
import io
import re

def validate_pgn(pgn_string):
    pgn_io = io.StringIO(pgn_string)
    return chess.pgn.read_game(pgn_io)

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