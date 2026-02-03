# src/prompt_builder.py

class PromptBuilder:
    def __init__(self, user, mentor, analyzer):
        self.user = user
        self.mentor = mentor
        self.analyzer = analyzer

    def _format_moments(self, moments):
        if not moments:
            return "Aucune gaffe majeure détectée sur cette séquence."
        
        lines = []
        for m in moments:
            lines.append(f"- Coup {m['move']} ({m['turn']}): {m['notation']} | Delta: {m['delta']} | {m['label']}")
        return "\n".join(lines)

    def get_coach_prompt(self, move_range, moments):
        # 1. On récupère les données traitées par l'analyzer
        stats = self.analyzer.get_stats()
        history = self.analyzer.export_for_ai(move_range)
        moments_texte = self._format_moments(moments) # Ta fonction de formatage précédente
        
        # 2. On définit l'identité du Mentor (Couche Système)
        identity_block = f"""
        Tu es {self.mentor.nom}.
        Description : {self.mentor.desc}
        Ton style de coaching : {self.mentor.vibe}
        """

        # 3. On injecte tes contraintes et la structure (Ta base actuelle)
        # Note : On utilise les attributs de self.mentor pour personnaliser
        structure_block = f"""
        Contraintes :
        - Parle avec ton ton "{self.mentor.vibe}".
        - Pas d'introduction ni de conclusion générique (sois direct).
        - Notation algébrique française (Cf3, d5, exd5).
        - Placeholders obligatoires pour les images : {{{{DIAGRAM_MOMENT_XX_Y}}}}, {{{{CHART_EVAL_TENSION}}}}, {{{{STATS_TABLE}}}}.

        Structure de ta réponse :
        # Chapitre 1 : Identité de la partie
        * Élève : {self.user['name']} vs {self.analyzer.headers.get('Black' if self.user['is_white'] else 'White')}
        * Résultat : {self.analyzer.headers.get('Result')}
        {{{{CHART_EVAL_TENSION}}}}
        {{{{STATS_TABLE}}}}

        # Chapitre 2 : Ouverture
        * Nom de l'ouverture. Verdict du coach. 
        * Si pertinent, ajoute un placeholder diagramme.

        # Chapitre 3 : Moments Critiques
        (Analyse ici les erreurs trouvées dans la liste fournie ci-dessous)
        Pour chaque erreur majeure :
        ## Erreur au coup XX
        {{{{DIAGRAM_MOMENT_XX_Y}}}}
        * Ton analyse de coach et l'alternative suggérée.

        # Chapitre 4 : Profil & Progrès
        * Ton avis sur le style de l'élève.
        * Exercice final : {{{{DIAGRAM_MOMENT_XX_Y}}}}
        """

        # 4. On fournit la "Matière Première" (Les données de la partie)
        data_block = f"""
        DONNÉES DE LA PARTIE :
        Stats : {stats}
        Moments clés détectés par l'ordinateur : {moments_texte}
        Historique des coups : {history}
        """

        # On assemble le tout
        return f"{identity_block}\n\n{structure_block}\n\n{data_block}"