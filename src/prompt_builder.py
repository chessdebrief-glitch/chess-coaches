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

    # ASSURE-TOI QUE LE NOM EST BIEN CELUI-CI :
    def get_coach_prompt(self, move_range, moments):
        stats = self.analyzer.get_stats()
        history = self.analyzer.export_for_ai(move_range)
        
        prompt = f"""
Tu es {self.mentor.nom}. Style : {self.mentor.vibe}.
{self.mentor.desc}

ÉLÈVE : {self.user['name']} ({self.user['elo']} ELO)
SÉQUENCE : Coups {move_range[0]} à {move_range[1]}

MOMENTS CLÉS :
{self._format_moments(moments)}

MISSION :
{self.mentor.get_punchline('intro')}
Analyse ces coups avec ton ton "{self.mentor.vibe}".
{self.mentor.get_punchline('conclusion')}
"""
        return prompt