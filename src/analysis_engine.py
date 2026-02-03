from .prompt_builder import PromptBuilder
from src.mentor import Mentor # On importe notre nouvelle classe
from .ai_service import AIService

# src/analysis_engine.py

# src/analysis_engine.py
from .prompt_builder import PromptBuilder
from .ai_service import AIService

def run_analysis_flow(payload, analyzer, mode="debug"):
    """
    Coordination de l'analyse.
    Modes disponibles : 'debug' (affiche le prompt) ou 'api' (appelle Gemini)
    """
    move_range = payload["analysis_settings"]["move_range"]
    mentor = payload["coach"]
    
    # 1. Extraction des données techniques
    moments_critiques = analyzer.get_critical_moments(threshold=1.5)
    
    # 2. Construction du prompt (C'est là que tu vas travailler le plus)
    builder = PromptBuilder(payload["user"], mentor, analyzer)
    prompt = builder.get_coach_prompt(move_range, moments_critiques)
    
    # 3. Logique de retour selon le mode
    if mode == "debug":
        # On retourne le prompt brut pour pouvoir le lire dans l'interface
        # On ajoute une petite note visuelle pour savoir qu'on est en debug
        debug_output = f"""
        **🔧 MODE DEBUG : PROMPT GÉNÉRÉ**
        ---
        {prompt}
        ---
        *Note : En mode API, ce texte serait envoyé à Gemini.*
        """
        return debug_output, analyzer.get_analysis_slice(move_range)
    
    else:
        # Mode API réel
        ai_service = AIService(debug_mode=False)
        reponse_ia = ai_service.get_coach_response(prompt, mentor)
        return reponse_ia, analyzer.get_analysis_slice(move_range)