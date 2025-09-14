# app.py
import streamlit as st
st.set_page_config(page_title="Class Game", page_icon="🎮", layout="wide")

st.title("Class Game (Supabase-backed)")
st.write("Use the sidebar to open Host or Player pages.")
st.markdown("""
- Host controls the class flow (team → Q1..Q5 → mini-game → scoreboard).  
- Players join with a room code and team name.  
- All state is stored in Supabase tables; pages poll every ~1s.
""")
