# src/prompt_builder.py

class PromptBuilder:
    def __init__(self, user, mentor, analyzer):
        self.user = user
        self.mentor = mentor
        self.analyzer = analyzer

    # --- BLOCS DE CONSTRUCTION (PRIVES) ---

    def _get_identity_header(self):
        return f"""
        TON IDENTITÉ :
        Tu es {self.mentor.nom}.
        Style : {self.mentor.vibe}.
        Personnalité : {self.mentor.desc}
        Ton : {self.mentor.get_punchline('intro')}
        
        CONSIGNES DE TON :
        - Ne sors jamais de ton personnage.
        - Sois direct, pas de blabla d'IA générique.
        """

    def _get_technical_constraints(self):
        return """
        CONTRAINTES DE FORMATAGE (STRICTES) :
        - Langue : Français exclusivement.
        - Notation : Algébrique française (ex: Cf3, exd5, O-O).
        - Style : Markdown (titres #, gras **, listes *).
        - INTERDICTION d'introduction ou de conclusion polie.
        - PLACEHOLDERS OBLIGATOIRES : 
          Utilise {{CHART_EVAL_TENSION}}, {{STATS_TABLE}} et {{DIAGRAM_MOMENT_XX_Y}} 
          (où XX est le coup et Y est W ou B).
        """

    def _get_data_body(self, move_range, moments):
        stats = self.analyzer.get_stats()
        # On passe move_range à l'export pour ne donner que les coups utiles
        history = self.analyzer.export_for_ai(move_range)
        moments_txt = self._format_moments(moments)
        
        adversaire = self.analyzer.headers.get('Black' if self.user['is_white'] else 'White', 'Inconnu')
        resultat = self.analyzer.headers.get('Result', 'En cours')

        return f"""
        DONNÉES DE LA PARTIE :
        - Élève : {self.user['name']} ({self.user['elo']} ELO) vs {adversaire}
        - Résultat : {resultat}
        - Stats : {stats}
        - Moments critiques détectés : 
        {moments_txt}
        - Historique des coups : {history}
        """

    def _format_moments(self, moments):
        if not moments:
            return "Aucune gaffe majeure détectée sur cette séquence."
        lines = [f"- Coup {m['move']} ({m['turn']}): {m['notation']} | Delta: {m['delta']} | {m['label']}" for m in moments]
        return "\n".join(lines)

    # --- ASSEMBLAGES SPÉCIFIQUES ---

    def get_full_game_prompt(self, moments):
        structure = """
        MISSION : Analyse globale de la partie.
        STRUCTURE DE LA RÉPONSE :
        # Chapitre 1 : Identité de la partie {{CHART_EVAL_TENSION}} {{STATS_TABLE}}
        # Chapitre 2 : L'Ouverture (Verdict du coach)
        # Chapitre 3 : Moments Critiques (Analyse détaillée de chaque erreur listée)
        # Chapitre 4 : Profil & Progrès (Ton avis final et un exercice {{DIAGRAM_MOMENT_XX_Y}})
        """
        return f"{self._get_identity_header()}\n{self._get_technical_constraints()}\n{structure}\n{self._get_data_body(None, moments)}"

    def get_focus_prompt(self, move_range, moments):
        structure = f"""
        MISSION : Focus chirurgical sur les coups {move_range[0]} à {move_range[1]}.
        STRUCTURE DE LA RÉPONSE :
        # Analyse de la séquence (Pourquoi c'était le tournant ?)
        # Zoom Tactique {{DIAGRAM_MOMENT_XX_Y}}
        # Conseil spécifique pour cette phase de jeu
        """
        return f"{self._get_identity_header()}\n{self._get_technical_constraints()}\n{structure}\n{self._get_data_body(move_range, moments)}"

    # --- LE POINT D'ENTRÉE UNIQUE ---

    def get_coach_prompt(self, move_range, moments):
        """
        Décide quel type de prompt générer en fonction du contexte.
        """
        total_moves = len(self.analyzer.df)
        is_full_game = move_range[0] <= 1 and move_range[1] >= (total_moves - 1)

        if is_full_game:
            return self.get_full_game_prompt(moments)
        else:
            return self.get_focus_prompt(move_range, moments)