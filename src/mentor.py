class Mentor:
    def __init__(self, data):
        self.id = data["id"]
        self.nom = data["nom"]
        self.emoji = data["emoji"]
        self.desc = data["desc"]
        self.vibe = data["vibe"]
        self.punchlines = data.get("punchlines", {})

    # --- Pour l'IHM (app.py) ---
    def get_punchline(self, key, default=""):
        return self.punchlines.get(key, default)

    # --- Pour l'IA (PromptBuilder) ---
    def get_identity_prompt(self):
        """Retourne le bloc de personnalité pour le système de l'IA."""
        return f"""
        Tu es {self.nom} {self.emoji}.
        Ton style : {self.vibe}
        Ta personnalité : {self.desc}
        """

    def format_analysis_instruction(self, player_name):
        """Définit comment le mentor doit s'adresser à l'élève."""
        return f"Tu t'adresses à ton élève {player_name} avec ton ton habituel ({self.vibe})."