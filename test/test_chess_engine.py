import unittest
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
        self.assertTrue(validate_pgn(valid_pgn) is not None)

    def test_validate_pgn_invalid(self):
        invalid_pgn = "This is not a valid PGN"
        self.assertIsNone(validate_pgn(invalid_pgn))

    def test_validate_pgn_empty(self):
        empty_pgn = ""
        self.assertIsNone(validate_pgn(empty_pgn))

    def test_validate_pgn_invalid_moves(self):
        invalid_pgn = """[Event ""]
[Site ""]
[Date "????.??.??"]
[Round "?"]
[White ""]
[Black ""]
[Result "*"]

1. e4 e6 2. Qh5 Qh4 *"""
        self.assertTrue(validate_pgn(invalid_pgn) is not None)

    def test_validate_pgn_castling(self):
        valid_pgn = """[Event "Petit Roque"]
        1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O O-O *"""
            # Ici, le passage est libéré, le roque est légal.
        self.assertIsNotNone(validate_pgn(valid_pgn))

        def test_validate_pgn_promotion(self):
                valid_pgn = """[Event ""]
        [Site ""]
        [Date "????.??.??"]
        [Round "?"]
        [White ""]
        [Black ""]
        [Result "*"]

        1. e7 d1=Q *"""
        self.assertTrue(validate_pgn(valid_pgn) is not None)

    def test_validate_pgn_en_passant(self):
        valid_pgn = """[Event "En Passant"]
    1. e4 a6 2. e5 d5 3. exd6 *"""
        # Les Blancs sont en e5, les Noirs poussent d7-d5, les Blancs mangent en d6.
        self.assertIsNotNone(validate_pgn(valid_pgn))

    def test_validate_pgn_impossible_move(self):
        # Un coup syntaxiquement correct (e4) mais c'est au tour des noirs !
        pgn_impossible = "[White \"Moi\"]\n[Black \"Lui\"]\n\n1. e4 e5 2. e4 *" 
        self.assertIsNone(validate_pgn(pgn_impossible))


if __name__ == '__main__':
    unittest.main()