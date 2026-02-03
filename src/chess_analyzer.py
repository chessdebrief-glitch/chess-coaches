import pandas as pd
import chess.pgn
import io
import re

class ChessAnalyzer:
    def __init__(self, game_object):
        """
        On n'initialise plus avec du texte, mais avec l'objet 'game' 
        déjà validé. C'est beaucoup plus robuste.
        """
        self.game = game_object
        self.headers = self.game.headers
        # On capture le retour de la fonction pour remplir l'attribut de l'objet
        self.df = self._build_dataframe()

    @staticmethod
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
        # 5bis. Vérification de la présence d'évaluations
        if not re.search(r"\[%eval", pgn_string):
            # On ne bloque pas forcément, mais on peut retourner un message spécifique
            # pour prévenir l'utilisateur que l'analyse sera limitée.
            pass

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

    def _parse_pgn(self, pgn_text):
        """Transforme le texte en objet Chess Game."""
        return chess.pgn.read_game(io.StringIO(pgn_text))

    def _build_dataframe(self):
        """
        Parcourt la partie complète et génère le DataFrame maître.
        """
        data = []
        node = self.game
        ply = 0
        prev_eval = 0.3  # Neutre au début
        
        while node.variations:
            next_node = node.variation(0)
            ply += 1
            
            # 1. Infos de base
            move_number = (ply + 1) // 2
            turn = "White" if ply % 2 != 0 else "Black"
            # Important : node.board() est la position AVANT le coup
            notation = node.board().san(next_node.move)

            # 2. Extraction de l'éval avec gestion du Mat
            comment = next_node.comment
            current_eval = prev_eval
            
            # Regex pour les scores classiques [%eval 0.23]
            match_eval = re.search(r"\[%eval (-?\d+\.?\d*)\]", comment)
            # Regex pour les mats [%eval #3] (Mat en 3 pour les blancs)
            match_mate = re.search(r"\[%eval #(-?\d+)\]", comment)

            if match_mate:
                mate_in = int(match_mate.group(1))
                # On simule un score très haut/bas pour le graphique
                current_eval = 20.0 if mate_in > 0 else -20.0
            elif match_eval:
                current_eval = float(match_eval.group(1))
            
            # 3. Calcul du Delta (Point de vue Blanc)
            delta = round(current_eval - prev_eval, 2)

            data.append({
                "ply": ply,
                "move": move_number,
                "turn": turn,
                "notation": notation,
                "eval": current_eval,
                "delta": delta,
                "fen": next_node.board().fen() # On garde la FEN de chaque coup
            })

            prev_eval = current_eval
            node = next_node
            
        return pd.DataFrame(data)

    def get_summary_for_ai(self, move_range):
        """Retourne un texte optimisé pour le prompt du coach."""
        start, end = move_range
        mask = self.df['move'].between(start, end)
        subset = self.df[mask]
        
        # On ne garde que l'essentiel pour économiser les tokens
        return subset[['move', 'turn', 'notation', 'eval', 'delta']].to_string(index=False)

    def get_fen_at_move(self, move_number):
        """Récupère la FEN à un coup précis."""
        res = self.df[self.df['move'] == move_number]
        return res.iloc[0]['fen'] if not res.empty else None
    
    def get_analysis_slice(self, move_range):
        """Retourne uniquement la portion du DF choisie par l'utilisateur."""
        start, end = move_range
        return self.df[self.df['move'].between(start, end)].copy()
    
    def get_critical_moments(self, threshold=1.5):
        """
        Identifie les tournants de la partie (Blunders/Mistakes).
        Retourne une liste de dictionnaires 'CriticalMoment'.
        """
        # On définit ce qu'est une erreur selon le delta
        # Note : Delta positif = avantage Blanc, Delta négatif = avantage Noir
        critical_df = self.df[self.df['delta'].abs() >= threshold].copy()
        
        moments = []
        for _, row in critical_df.iterrows():
            # Étiquetage simple
            abs_delta = abs(row['delta'])
            label = "Blunder" if abs_delta >= 3.0 else "Mistake"
            
            moments.append({
                "move": row['move'],
                "turn": row['turn'],
                "notation": row['notation'],
                "eval": row['eval'],
                "delta": row['delta'],
                "label": label,
                "fen": row['fen']
            })
        return moments

    def export_for_ai(self, move_range):
        """
        Génère un format Markdown ultra-léger pour le prompt.
        On évite le bruit du DataFrame complet pour sauver des tokens.
        """
        subset = self.get_analysis_slice(move_range)
        
        # On construit une liste compacte : "1.e4 (0.2) 1...e5 (0.1) ..."
        history = []
        for _, row in subset.iterrows():
            history.append(f"{row['move']}{'...' if row['turn']=='Black' else '.'}{row['notation']} (eval: {row['eval']})")
        
        return " | ".join(history)
    
    def get_stats(self):
        """Retourne un dictionnaire de statistiques globales."""
        if self.df.empty:
            return {}
            
        return {
            "total_moves": self.df['move'].max(),
            "avg_delta": self.df['delta'].abs().mean(),
            "blunders_white": len(self.df[(self.df['turn'] == 'White') & (self.df['delta'] <= -3.0)]),
            "blunders_black": len(self.df[(self.df['turn'] == 'Black') & (self.df['delta'] >= 3.0)]),
            "peak_white": self.df['eval'].max(),
            "peak_black": self.df['eval'].min()
        }
    
    def generate_eval_chart(self, move_range):
        """
        Génère un graphique Matplotlib simple de l'évaluation.
        """
        import matplotlib.pyplot as plt
        
        start, end = move_range
        df_slice = self.get_analysis_slice(move_range)
        
        fig, ax = plt.subplots(figsize=(10, 4))
        # On lisse un peu l'éval pour le graphique (clip à -5/+5)
        evals = df_slice['eval'].clip(-5, 5)
        plies = df_slice['ply']
        
        ax.fill_between(plies, evals, 0, where=(evals >= 0), color='gray', alpha=0.3)
        ax.fill_between(plies, evals, 0, where=(evals < 0), color='black', alpha=0.3)
        ax.plot(plies, evals, color='blue', linewidth=2)
        
        ax.axhline(0, color='white', linewidth=0.8, linestyle='--')
        ax.set_title("Courbe d'évaluation")
        return fig
    