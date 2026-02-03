# src/ai_service.py
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class AIService:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        self.model_name = "gemini-3-flash-preview" 

    def get_coach_response(self, prompt, mentor):
        """
        Envoie le prompt à Gemini.
        """
        if self.debug_mode:
            return self._get_mock_response(mentor)

        if not self.api_key:
            st.error("Clé API Google manquante dans les secrets.")
            return None

        try:
            llm = ChatGoogleGenerativeAI(
                model=self.model_name, 
                google_api_key=self.api_key,
                temperature=0.7
            )
            
            # On définit les messages pour Gemini
            messages = [
                SystemMessage(content=f"Tu es {mentor.nom}. {mentor.desc}. Ton style est {mentor.vibe}."),
                HumanMessage(content=prompt)
            ]
            
            # Appel à l'IA
            response = llm.invoke(messages)
            return response.content
            
        except Exception as e:
            st.error(f"Erreur Gemini : {e}")
            return None

    def _get_mock_response(self, mentor):
        """Réponse fictive pour le mode debug."""
        return f"""
        (MODE DEBUG ACTIVÉ - {mentor.nom})
        
        Salut, je suis ton coach. Voici une analyse simulée :
        
        {{{{CHART_EVAL_TENSION}}}}
        
        Au coup 15, tu as fait une erreur tactique :
        {{{{DIAGRAM_MOVE_15}}}}
        
        Concentrate-toi sur le centre !
        """