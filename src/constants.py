# constants.py
import json
import os

# Chemin vers le fichier JSON
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "mentors.json")

def load_mentors_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

data = load_mentors_data()

# On recrée les variables attendues par le reste de l'app
MENTORS = data["mentors"]

# On cherche le mentor par défaut selon l'ID spécifié dans le JSON
DEFAULT_COACH = next(
    (m for m in MENTORS if m["id"] == data["default_mentor_id"]), 
    MENTORS[0]
)