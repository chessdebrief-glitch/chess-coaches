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
    def _check_evaluations(pgn_string):
        """Vérifie la présence de tags [%eval]."""
        if not re.search(r"\[%eval", pgn_string):
            return "Le PGN ne contient aucune donnée d'évaluation ([%eval])."
        return None

    @staticmethod
    def _check_legality(game):
        """Vérifie si tous les coups de la partie sont légaux."""
        board = game.board()
        for move in game.mainline_moves():
            if move not in board.legal_moves:
                return f"Coup illégal détecté: {move.uci()}"
            board.push(move)
        return None

    @staticmethod
    def _has_content(game):
        """Vérifie si le PGN contient de la substance (coups ou headers)."""
        has_moves = not game.is_end()
        important_headers = ["Event", "White", "Black", "FEN"]
        has_headers = any(game.headers.get(h, "?") != "?" for h in important_headers)
        return has_moves or has_headers

    @staticmethod
    def validate_pgn(pgn_string):
        """Fonction chef d'orchestre pour la validation."""
        # 1. Validation de base du texte
        if not pgn_string or not pgn_string.strip():
            return None, "Le PGN fourni est vide."

        # 2. Parsing
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_string))
        except Exception as e:
            return None, f"Erreur de lecture: {e}"

        if game is None:
            return None, "Format PGN invalide."

        # 3. Validations en cascade
        if game.errors:
            return game, f"Erreur de syntaxe: {game.errors[0]}"

        if not ChessAnalyzer._has_content(game):
            return game, "Le PGN est vide (ni coups, ni en-têtes)."

        # 4. Validation spécifique au projet (évaluations)
        eval_error = ChessAnalyzer._check_evaluations(pgn_string)
        if eval_error:
            return game, eval_error

        # 5. Validation de la logique du jeu
        try:
            legality_error = ChessAnalyzer._check_legality(game)
            if legality_error:
                return game, legality_error
        except Exception as e:
            return game, f"Erreur lors de la vérification légale: {e}"

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

    def get_top_moments(self, is_white_player=True, top_n=3, types=['Blunder', 'Mistake']):
        """
        Identifie les N pires moments pour une couleur donnée.
        is_white_player: True pour Blancs, False pour Noirs.
        top_n: Nombre de gaffes à extraire.
        """
        df_copy = self.df.copy()

        # 1. On définit la cible
        target_color = 'White' if is_white_player else 'Black'
        
        # 2. On calcule la "punition" (perte de points) subie par le joueur
        # Rappel : eval est vue du côté Blanc. 
        # Si Blanc joue, une baisse de l'éval (delta < 0) est une erreur.
        # Si Noir joue, une hausse de l'éval (delta > 0) est une erreur.
        def calculate_punishment(row):
            if row['turn'] == 'White':
                return -row['delta'] if row['delta'] < 0 else 0
            else:
                return row['delta'] if row['delta'] > 0 else 0

        df_copy['punishment'] = df_copy.apply(calculate_punishment, axis=1)

        # 3. On filtre par couleur ET par type d'erreur
        mask = (df_copy['turn'] == target_color)
        df_filtered = df_copy[mask].copy()

        # 4. Étiquetage selon la punition
        def label_error(p):
            if p >= 3.0: return "Blunder"
            if p >= 1.0: return "Mistake"
            return "Inaccuracy"

        df_filtered['label'] = df_filtered['punishment'].apply(label_error)
        
        # Filtrage des types (Blunder/Mistake uniquement par défaut)
        df_filtered = df_filtered[df_filtered['label'].isin(types)]

        # 5. On prend le Top N des plus grosses punitions
        top_df = df_filtered.sort_values(by='punishment', ascending=False).head(top_n)

        moments = []
        for _, row in top_df.iterrows():
            moments.append({
                "move": int(row['move']),
                "turn": row['turn'],
                "notation": row['notation'],
                "eval": float(row['eval']),
                "delta": float(row['delta']),
                "punishment": round(float(row['punishment']), 2),
                "label": row['label'],
                "fen": row['fen']
            })
        
        # On trie par numéro de coup pour que l'affichage soit chronologique
        return sorted(moments, key=lambda x: x['move'])


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
        """Retourne un dictionnaire de statistiques globales avec types Python natifs."""
        if self.df.empty:
            return {}
            
        # On utilise .item() ou on force le cast pour éviter le marquage np.int64
        return {
            "total_moves": int(self.df['move'].max()),
            "avg_delta": float(round(self.df['delta'].abs().mean(), 2)),
            "blunders_white": int(len(self.df[(self.df['turn'] == 'White') & (self.df['delta'] <= -3.0)])),
            "blunders_black": int(len(self.df[(self.df['turn'] == 'Black') & (self.df['delta'] >= 3.0)])),
            "peak_white": float(self.df['eval'].max()),
            "peak_black": float(self.df['eval'].min())
        }
    
    def generate_eval_chart(self, move_range):
        """
        Génère un graphique d'évaluation stylisé pour le Dark Mode.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        start, end = move_range
        df_slice = self.get_analysis_slice(move_range)
        
        # Configuration du style sombre
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='#0e1117') # Couleur de fond Streamlit
        ax.set_facecolor('#0e1117')

        # Préparation des données
        plies = df_slice['ply'].values
        # On clip à 4 pour garder de la lisibilité (au-delà, c'est gagné de toute façon)
        evals = df_slice['eval'].clip(-4, 4).values 

        # Remplissage dégradé (Blancs - Vert / Noirs - Violet)
        ax.fill_between(plies, evals, 0, where=(evals >= 0), 
                        interpolate=True, color='#2ecc71', alpha=0.4, label='Avantage Blancs')
        ax.fill_between(plies, evals, 0, where=(evals < 0), 
                        interpolate=True, color='#9b59b6', alpha=0.4, label='Avantage Noirs')

        # Ligne principale plus douce
        ax.plot(plies, evals, color='#3498db', linewidth=2.5, alpha=0.8)

        # Axe central et grille
        ax.axhline(0, color='white', linewidth=1, alpha=0.5)
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.3)

        # Personnalisation des axes
        ax.set_title("ANALYSE DE LA PARTIE", fontsize=12, pad=15, color='white', fontweight='bold')
        ax.set_xlabel("Demi-coups (Ply)", fontsize=9, color='gray')
        ax.set_ylabel("Évaluation (CP)", fontsize=9, color='gray')
        
        # Légende stylisée
        legend = ax.legend(loc='upper left', frameon=True, fontsize=8)
        legend.get_frame().set_facecolor('#1e2130')
        legend.get_frame().set_edgecolor('gray')

        # Supprimer les bordures inutiles
        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout()
        return fig
    
    def get_board_svg(self, move_number, orientation_white=True):
        """
        Génère le plateau SVG à un coup précis de manière instantanée.
        """
        import chess.svg
        import base64

        # On récupère la FEN directement dans notre DataFrame (pas de boucle !)
        fen = self.get_fen_at_move(move_number)
        if not fen:
            return ""

        board = chess.Board(fen)
        side = chess.WHITE if orientation_white else chess.BLACK
        
        svg_data = chess.svg.board(
            board, 
            orientation=side, 
            size=350,
            style=".square.light { fill: #eae9d2; } .square.dark { fill: #4b7399; }"
        )
        
        # On garde le Base64 uniquement si on veut l'afficher dans un bloc HTML custom,
        # sinon Streamlit peut afficher du SVG directement.
        return svg_data

    def export_pgn_with_evals(self, move_range=None):
            """
            Génère la chaîne PGN annotée à partir du DataFrame de l'analyzer.
            """
            df_to_export = self.df
            if move_range:
                start, end = move_range
                # On filtre sur la colonne 'move' qui contient le numéro du coup
                df_to_export = self.df[self.df['move'].between(start, end)]

            pgn_moves = []
            for _, row in df_to_export.iterrows():
                # Correction : ton DF utilise 'turn' (White/Black) et 'move' (int)
                prefix = f"{row['move']}. " if row['turn'] == 'White' else ""
                
                val = row['eval']
                eval_str = f"{val:+.1f}" if isinstance(val, (int, float)) else str(val)
                eval_comment = f"{{[%eval {eval_str}]}}"
                
                pgn_moves.append(f"{prefix}{row['notation']} {eval_comment}")

            return " ".join(pgn_moves)
    
    def get_lichess_image_url(self, move_number, orientation_white=True):
        """Génère l'URL d'une image statique via Lichess avec encodage strict."""
        import urllib.parse
        
        fen = self.get_fen_at_move(move_number)
        if not fen:
            return None
        
        # Étape CRUCIALE : On encode la FEN pour qu'elle soit compatible URL
        # Cela transforme les espaces en %20 et les caractères spéciaux
        safe_fen = urllib.parse.quote(fen)
        
        orientation = "white" if orientation_white else "black"
        
        # On utilise l'URL officielle d'export de Lichess
        url = f"https://lichess.org/export/fen.png?fen={safe_fen}&orientation={orientation}"
        print(f"DEBUG URL: {url}") # Regarde dans ton terminal VS Code
        return url


    def get_lichess_embed_url(self, move_number, orientation_white=True):
        """Génère l'URL pour l'iframe interactif de Lichess."""
        fen = self.get_fen_at_move(move_number)
        if not fen:
            return None
        
        import urllib.parse
        # Pour l'iframe, on remplace les espaces par des underscores dans la FEN
        # C'est une convention spécifique à l'analyseur Lichess
        safe_fen = fen.replace(" ", "_")
        orientation = "white" if orientation_white else "black"
        
        # On utilise l'URL d'analyse avec le paramètre theme et orientation
        return f"https://lichess.org/analysis/standard/{safe_fen}?color={orientation}"
    
    def get_fen_before_move(self, move_number):
        """Récupère la FEN juste avant que le coup spécifié ne soit joué."""
        # Si on veut voir l'erreur du coup 15, on affiche la position après le coup 14
        target_move = move_number - 1
        
        # On cherche dans le dataframe la FEN du coup précédent
        row = self.df[self.df['move'] == target_move]
        
        if not row.empty:
            return row.iloc[0]['fen']
        else:
            # Si c'est le premier coup, on renvoie la position de départ
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        

    def get_fen_by_ply(self, ply_number):
            """
            Récupère la FEN à un ply (demi-coup) précis.
            Ply 0 = Position initiale.
            """
            if ply_number <= 0:
                return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            
            # On cherche dans le dataframe la ligne où ply correspond
            res = self.df[self.df['ply'] == ply_number]
            
            if not res.empty:
                return res.iloc[0]['fen']
            
            # Si on ne trouve pas (ex: ply trop élevé), on renvoie la dernière position connue
            return self.df.iloc[-1]['fen'] if not self.df.empty else None