# src/prompt_builder.py

class PromptBuilder:
    def __init__(self, user, mentor, analyzer):
        self.user = user
        self.mentor = mentor
        self.analyzer = analyzer

    # --- BLOCS DE CONSTRUCTION (PRIVES) ---

    def _get_mentor_identity(self):
        return f"""
        TON IDENTITÉ :
        Tu es {self.mentor.nom}.
        Style : {self.mentor.vibe}.
        Personnalité : {self.mentor.desc}
        Ton punchline : {self.mentor.get_punchline('intro')}
        
        CONSIGNES DE TON :
        - Ne sors jamais de ton personnage.
        - Sois direct, pas de blabla d'IA générique.
        """

    def _get_output_constraints(self):
        return """
        CONTRAINTES DE FORMATAGE (STRICTES) :
        - Langue : Français exclusivement.
        - Notation : Algébrique française (ex: Cf3, exd5, O-O).
        - Style : Markdown (titres #, gras **, listes *).
        - INTERDICTION d'introduction ou de conclusion polie.
        """

    def _get_game_metadata(self):
        adversaire = self.analyzer.headers.get('Black' if self.user['is_white'] else 'White', 'Inconnu')
        resultat = self.analyzer.headers.get('Result', 'En cours')
        return f"""
        CONTEXTE : {self.user['name']} ({self.user['elo']} ELO) vs {adversaire}
        RÉSULTAT : {resultat}
        """

    def _get_game_data_block(self, move_range, is_full_game):
        pgn = self.analyzer.export_pgn_with_evals(move_range)
        stats = self.analyzer.get_stats()
        
        fen_block = ""
        # On n'ajoute la FEN que si on n'est PAS au début de la partie
        if not is_full_game and move_range[0] > 1:
            # On récupère la position AVANT le premier coup du focus
            fen_initiale = self.analyzer.get_fen_at_move(move_range[0] - 1)
            if fen_initiale:
                fen_block = f"POSITION DE DÉPART (FEN) :{fen_initiale}"

        return f"""
        {fen_block}
        DONNÉES TECHNIQUES (PGN ANNOTÉ) :
        {pgn}

        """

    def _get_analysis_summary(self, moments):
        if not moments:
            return "POINTS CRITIQUES : Aucun incident majeur détecté."
        
        lines = [f"- Coup {m['move']}: {m['notation']} (Delta: {m['delta']}) -> {m['label']}" for m in moments]
        return "POINTS CRITIQUES (À ANALYSER EN PRIORITÉ) :\n" + "\n".join(lines)

    # --- LE POINT D'ENTRÉE UNIQUE ---

# --- LE POINT D'ENTRÉE UNIQUE ---

    def get_coach_prompt(self, move_range, moments):
        """
        Génère le prompt final en assemblant les briques selon le contexte.
        """
        # 1. Calcul des bornes pour détecter si c'est la partie entière
        first_move = self.analyzer.df['move'].min()
        last_move = self.analyzer.df['move'].max()
        
        is_full_game = move_range[0] <= first_move and move_range[1] >= last_move

        # 2. Définition de la mission selon le contexte
        if is_full_game:
            mission =  """
        MISSION : Analyse globale. 
        - Balaye l'ouverture, le milieu de jeu et la finale.
        - Identifie le tournant psychologique de la partie.
        - Utilise la structure : Identité {{CHART_EVAL_TENSION}}, Ouverture, Moments Critiques, Verdict final.
        """
        else:
            mission = f"""
        MISSION : Focus chirurgical (Coups {move_range[0]} à {move_range[1]}).
        - Utilise la FEN fournie pour visualiser la position initiale de cette séquence.
        - Explique pourquoi ces coups précis ont fait basculer l'évaluation.
        - Ne parle PAS du reste de la partie.
        """

        # 3. Assemblage final (Ordre logique : Identité -> Format -> Mission -> Data)
        prompt = [
            self._get_mentor_identity(),
            self._get_output_constraints(),
            self._get_game_metadata(),
            mission,
            self._get_game_data_block(move_range, is_full_game)
            #self._get_analysis_summary(moments)
        ]

        return "\n".join(prompt)

