# pages/01_Host.py
import json, time
import streamlit as st
from lib.db import upsert_game, set_stage, get_game, list_teams, fetch_answers
import pathlib
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Host", page_icon="🧭", layout="wide")
st.title("Host console")

room_code = st.text_input("Room code (letters/numbers)", value=st.session_state.get("room_code","ABC123"))
col_a,col_b = st.columns([1,1])
with col_a:
    if st.button("Create/Load room"):
        g = upsert_game(room_code)
        st.session_state["room_code"] = g.room_code
with col_b:

    st_autorefresh(interval=1000, key="host_poll")

if "room_code" not in st.session_state:
    st.info("Enter a room code and click Create/Load room.")
    st.stop()

g = get_game(st.session_state["room_code"])
if not g:
    st.error("Room not found. Click Create/Load room.")
    st.stop()

st.subheader(f"Room {g.room_code} · Round {g.round}/3 · Stage: {g.stage}")

left,right = st.columns([2,1])

with left:
    st.write("Stage")
    stage = st.selectbox("Stage", ["team","q1","q2","q3","q4","q5","minigame","scoreboard"], index=["team","q1","q2","q3","q4","q5","minigame","scoreboard"].index(g.stage))
    new_round = st.number_input("Round", min_value=1, max_value=3, value=g.round)
    c1,c2,c3 = st.columns(3)
    if c1.button("Apply stage/round"):
        set_stage(g.room_code, int(new_round), stage)
    if c2.button("Next round ➜"):
        set_stage(g.room_code, min(3, g.round+1), "q1")
    if c3.button("Scoreboard"):
        set_stage(g.room_code, g.round, "scoreboard")

with right:
    st.write("Teams in room")
    for t in list_teams(g.room_code):
        st.write(f"• {t['name']}")

st.markdown("---")
st.subheader("Scoreboard (for current round)")
from lib.db import get_client
import json
# compute scores
import json, os
import pathlib
qs = json.loads((pathlib.Path("lib")/"questions.json").read_text(encoding="utf-8"))
round_qs = qs[str(g.round)]["questions"]
by_team = fetch_answers(g.room_code, g.round)

def score_team(entry):
    corrects = 0
    for qi in range(1,6):
        ans = entry["answers"].get(qi, None)
        if ans is not None and ans == round_qs[qi-1]["answer_idx"]:
            corrects += 1
    bonus = (entry["mg"] or 0)//5
    return corrects + bonus, corrects, bonus

rows = []
for team_id, entry in by_team.items():
    total, corr, bonus = score_team(entry)
    rows.append((entry["name"], total, corr, bonus, entry["mg"]))
if rows:
    rows.sort(key=lambda r: r[1], reverse=True)
    st.table({"Team":[r[0] for r in rows],
              "Score":[r[1] for r in rows],
              "Correct":[r[2] for r in rows],
              "Bonus":[r[3] for r in rows],
              "MiniGame":[r[4] for r in rows]})
else:
    st.info("No teams / answers yet.")
