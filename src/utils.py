def extract_clean_text(ai_res):
    """Extrait le texte pur d'une réponse IA (gère listes, dicts, objets)."""
    if not ai_res:
        return ""
    
    # Si c'est une liste (cas Gemini)
    if isinstance(ai_res, list) and len(ai_res) > 0:
        ai_res = ai_res[0]
    
    # Si c'est un dictionnaire
    if isinstance(ai_res, dict):
        return ai_res.get('text', str(ai_res))
    
    # Si c'est un objet avec un attribut .text
    if hasattr(ai_res, 'text'):
        return ai_res.text
        
    return str(ai_res)