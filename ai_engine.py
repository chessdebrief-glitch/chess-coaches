import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from constants import PROMPT_TEMPLATE

def call_gemini(pgn, coach_data, user_name, debug_mode=True):
    # 1. Préparation du dictionnaire de données
    input_data = {
        "pgn": pgn, 
        "coach_nom": coach_data["nom"], 
        "coach_style": coach_data["desc"], 
        "coach_vibe": coach_data["vibe"],
        "user_name": user_name
    }

    # 2. Construction du prompt final (ce qui est envoyé réellement)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    final_prompt = prompt_template.format(**input_data)

    # 3. MODE DEBUG : On affiche le prompt dans la console ou l'UI
    if debug_mode:
        print("\n--- DEBUG PROMPT ENVOYÉ ---")
        print(final_prompt)
        print("---------------------------\n")
        
        # On retourne un faux rapport (Mock) pour tester le reste de l'app sans payer
        return f"""
        Salut {user_name}, je suis {coach_data['nom']} (Mode Debug). 
        
        Voici ton analyse fictive pour économiser tes tokens :
        
        {{{{CHART_EVAL_TENSION}}}}
        
        Un moment clé ici au coup 10 :
        {{{{DIAGRAM_MOMENT_10_B}}}}
        
        Bravo pour cette partie !
        """

    # 4. MODE RÉEL (Si debug_mode=False)
    api_key = st.secrets.get("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", google_api_key=api_key)
    chain = prompt_template | llm
    
    return chain.invoke(input_data).content