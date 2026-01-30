import streamlit as st

st.title("♟️ Chess Debrief")
st.write("Hello World ! L'usine de production est officiellement lancée.")

# Petit test interactif
nom = st.text_input("Comment t'appelles-tu, futur Grand Maître ?")
if nom:
    st.write(f"Enchanté {nom}, prépare-toi à analyser tes parties !")
