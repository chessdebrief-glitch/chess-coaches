import unittest
import textwrap
from src.chess_engine import validate_pgn

class TestChessEngine(unittest.TestCase):

    def test_validate_pgn_valid(self):
        valid_pgn = """[Event ""]
[Site ""]
[Date "????.??.??"]
[Round "?"]
[White ""]
[Black ""]
[Result "*"]

1. e4 e5 *"""
        game, message = validate_pgn(valid_pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_invalid(self):
        invalid_pgn = "This is not a valid PGN"
        game, message = validate_pgn(invalid_pgn)
        self.assertIsNotNone(game)
        self.assertIsNotNone(message)

    def test_validate_pgn_empty(self):
        empty_pgn = ""
        game, message = validate_pgn(empty_pgn)
        self.assertIsNone(game)
        self.assertIsNotNone(message)

    def test_validate_pgn_invalid_moves(self):
        invalid_pgn = """[Event ""]
[Site ""]
[Date "????.??.??"]
[Round "?"]
[White ""]
[Black ""]
[Result "*"]

1. e4 e6 2. Qh5 Qh4 *"""
        game, message = validate_pgn(invalid_pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_castling(self):
        valid_pgn = textwrap.dedent("""[Event "Petit Roque"]\n\n
1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O O-O *""").strip()
        game, message = validate_pgn(valid_pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_promotion(self):
        valid_pgn = """[Event ""]
    [Site ""]
    [Date "????.??.??"]
    [Round "?"]
    [White ""]
    [Black ""]
    [Result "*"]

    1. e7 d1=Q *"""
        game, message = validate_pgn(valid_pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_en_passant(self):
        valid_pgn = """[Event "En Passant"]
1. e4 a6 2. e5 d5 3. exd6 *"""
        game, message = validate_pgn(valid_pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_impossible_move(self):
        pgn_impossible = "[White \"Moi\"]\n[Black \"Lui\"]\n\n1. e4 e5 2. e4 *" 
        game, message = validate_pgn(pgn_impossible)
        self.assertIsNotNone(game)
        self.assertIsNotNone(message)

    def test_validate_pgn_checkmate(self):
        """Test d'une partie courte se terminant par un mat (Coup du berger)."""
        pgn_mat = textwrap.dedent("""\
            [Event "Berger"]
            
            1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0""").strip()
        game, message = validate_pgn(pgn_mat)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_ambiguous_move(self):
        """Test de la levée d'ambiguïté (deux cavaliers pouvant aller sur la même case)."""
        pgn_ambigu = textwrap.dedent("""\
            [Event "Ambiguïté"]
            
            1. Nf3 d5 2. d4 Nf6 3. c4 e6 4. Nc3 Nbd7 *""").strip()
        game, message = validate_pgn(pgn_ambigu)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_with_comments(self):
        """Vérifie que les commentaires dans le PGN ne cassent pas l'analyse."""
        pgn_comments = '[Event "Comment"]\n\n1. e4 {Un bon coup} e5 {Réponse classique} *'
        game, message = validate_pgn(pgn_comments)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_illegal_king_move(self):
        """Test d'un roi qui tente de se mettre lui-même en échec."""
        pgn_suicide = textwrap.dedent("""\
            [Event "Suicide"]
            
            1. e4 e5 2. Ke2 d5 3. Ke3 d4+ 4. Kd3 *""").strip() 
        # Ici le coup 4. Kd3 pourrait être illégal si d4 est contrôlé
        # À adapter selon une position précise de mise en échec.
        
    def test_validate_pgn_under_promotion(self):
        """Test une promotion en Cavalier (plus rare que la Dame)."""
        pgn = textwrap.dedent("""\
            [White "Puzzle"]
            [FEN "8/4Ppk1/8/8/8/8/8/8 w - - 0 1"]

            1. e8=N+ *""").strip()
        game, message = validate_pgn(pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_with_annotations(self):
        """Test la résistance aux commentaires et symboles d'exclamation."""
        pgn = '1. e4 {Le meilleur coup!} e5 2. Nf3 !! (2. f4 !?) 2... Nc6 [%clk 0:05:00] *'
        game, message = validate_pgn(pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_ambiguous_rooks(self):
        """Test de la levée d'ambiguïté pour les tours sur une même colonne."""
        # On place deux tours blanches sur la colonne a
        pgn = textwrap.dedent("""\
            [FEN "R7/8/8/8/8/8/8/R6k w - - 0 1"]

            1. R1a4 *""").strip()
        game, message = validate_pgn(pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)

    def test_validate_pgn_double_check(self):
        """Test d'un échec double suite à une découverte."""
        # Position où un mouvement de cavalier libère une tour
        pgn = textwrap.dedent("""\
            [FEN "k7/8/8/8/8/3N4/3R4/K7 w - - 0 1"]

            1. Nb4+ *""").strip()
        game, message = validate_pgn(pgn)
        self.assertIsNotNone(game)
        self.assertIsNone(message)
if __name__ == '__main__':
    unittest.main()
