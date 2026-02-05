import json

# 1. On charge ton fichier
with open("test_response.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# --- CORRECTION ICI ---
# Si le JSON commence par [, raw_data est déjà la liste qu'on veut
if isinstance(raw_data, list):
    res = raw_data
# Si c'est un dictionnaire qui contient 'res', on le récupère
elif isinstance(raw_data, dict) and 'res' in raw_data:
    res = raw_data['res']
else:
    res = raw_data
# ----------------------

def clean_ia_response(data):
    # Si c'est une liste, on prend le premier élément (le dictionnaire avec 'text')
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    # Si c'est un dictionnaire, on extrait la clé 'text'
    if isinstance(data, dict):
        return data.get('text', "Clé 'text' absente")
    
    return str(data)

texte_propre = clean_ia_response(res)

print("--- TEXTE NETTOYÉ ---")
print(texte_propre[:300]) # On affiche le début