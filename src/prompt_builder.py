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
        Ta punchline : {self.mentor.get_punchline('intro')}
        
        CONSIGNES DE TON :
        - Ne sors jamais de ton personnage.
        - Sois direct, pas de blabla d'IA générique.
        - Adapte toi à l'élo de ton élève : self.user['elo'].

        """

    def _get_output_constraints(self):
            # On définit l'orientation par défaut du board selon le camp de l'user
            orientation = 'white' if self.user['is_white'] else 'black'
            
            return f"""
            CONTRAINTES DE FORMATAGE (STRICTES) :
                    - Langue : Français exclusivement.
                    - Notation : Algébrique française (ex: Cf3, exd5, O-O).
                    - Style : Markdown (titres #, gras **, listes *).
                    - ORIENTATION : L'utilisateur joue les {'Blancs' if self.user['is_white'] else 'Noirs'}, donc oriente tes réflexions (et les diagrammes) de son point de vue.
                    
                    CONTRAINTES DE DIAGRAMMES (DYNAMIQUES) :
                    Tu dois ponctuer ton analyse de 10 diagrammes maximum en utilisant la syntaxe suivante :
                    `[TYPE_PLY_XX](Titre court et percutant)`

                    TYPES DISPONIBLES :
                    1. [FOCUS_PLY_XX](Titre) : Pour illustrer un concept stratégique ou une position clé (ex: sortie d'ouverture, structure de pions).
                    -> L'UI affichera la position APRÈS le coup XX.
                    
                    2. [CHALLENGE_PLY_XX](Titre) : Pour mettre l'élève au défi sur une erreur (la sienne ou une gaffe adverse non punie).
                    -> L'UI affichera la position AVANT le coup XX pour forcer la réflexion.
                    -> Ex de titres : "Oups, l'imprécision !", "Le tournant du match", "Trouveras-tu mieux ?".

                    3. [BRILLIANT_PLY_XX](Titre) : Pour célébrer un coup exceptionnel ou une séquence tactique réussie par l'élève.
                    -> L'UI affichera la position APRÈS le coup avec un style visuel gratifiant.
                    -> Ex de titres : "Génie pur !", "Le coup de maître", "Dans la peau d'un GM".

                    IMPORTANT : 
                    - XX correspond au numéro de 'ply' (demi-coup) fourni dans les données.
                    - Ne mets pas d'espace entre le crochet et la parenthèse.
                    - Varie les titres selon ton style : {self.mentor.vibe}.
                    """

    def _get_game_metadata(self):
            # On détermine la couleur de l'utilisateur
            couleur_user = "BLANCS" if self.user['is_white'] else "NOIRS"
            adversaire = self.analyzer.headers.get('Black' if self.user['is_white'] else 'White', 'Inconnu')
            resultat = self.analyzer.headers.get('Result', 'En cours')
            
            return f"""
            CONTEXTE : {self.user['name']} ({self.user['elo']} ELO) vs {adversaire}
            RÉSULTAT : {resultat}
            
            MISSION CRITIQUE : 
            - Tu analyses la partie de ton élève {self.user['name']}.
            - {self.user['name']} joue avec les {couleur_user}.
            - Adresse-toi à lui directement ("Tu", "Ton", "Tes").
            - Ne te trompe pas de camp : si tu parles d'une erreur, assure-toi que c'est bien {self.user['name']} qui l'a commise avant de le réprimander.
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
            Ton rôle est d'effectuer une revue technique et psychologique de la rencontre en suivant ce plan strict :
            - Résumé de l'Ouverture : Identifie l'ouverture jouée. Indique qui est sorti de l'ouverture avec l'avantage et pourquoi (développement, structure, espace).
            - Le Moment Critique : Identifie le coup précis (ou la séquence) où l'avantage a basculé. Explique ce qui a été manqué (une tactique, un plan stratégique, une menace adverse).
            - Analyse Comparative : Pour les erreurs majeures (Blunders/Mistakes), propose la variante recommandée par le moteur et explique la logique derrière cette alternative.
            - Profil de Joueur : Donne-moi un feedback sur mon style de jeu lors de cette partie (ex: trop passif, prend des risques inutiles, solide en défense) et compare le à des joueurs connus
            - Le Conseil 'Next Level' : Donne-moi un seul concept ou principe à retenir pour mes 5 prochaines parties afin de ne pas répéter ce type d'erreur.
          
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

