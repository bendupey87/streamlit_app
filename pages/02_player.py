# pages/02_Player.py
import json, pathlib
import streamlit as st
from lib.db import upsert_game, get_game, add_team, save_answer, set_minigame_score, fetch_answers
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="Player", page_icon="👥", layout="wide")

st_autorefresh(interval=1000, key="player_poll")

st.title("Player")
room = st.text_input("Enter room code", value=st.session_state.get("room_code","ABC123"))
team_name = st.text_input("Team name", value=st.session_state.get("team_name",""))
c1,c2 = st.columns(2)
if c1.button("Join room"):
    if not team_name.strip():
        st.warning("Enter a team name.")
        st.stop()
    upsert_game(room)  # create if missing
    team_id, team_name = add_team(room, team_name.strip())
    st.session_state.update(room_code=room, team_id=team_id, team_name=team_name)
if "team_id" not in st.session_state:
    st.stop()

g = get_game(st.session_state["room_code"])
if not g:
    st.error("Room not found.")
    st.stop()

st.caption(f"Room {g.room_code} · Round {g.round}/3 · Stage: {g.stage} · Team: {st.session_state['team_name']}")

qs = json.loads((pathlib.Path("lib")/"questions.json").read_text(encoding="utf-8"))
round_qs = qs[str(g.round)]["questions"]

if g.stage.startswith("q"):
    qi = int(g.stage[1:])
    q = round_qs[qi-1]
    st.subheader(f"Question {qi}/5")
    choice = st.radio(q["prompt"], range(4), format_func=lambda i: q["options"][i], key=f"choice_{g.round}_{qi}")
    if st.button("Save answer"):
        save_answer(st.session_state["team_id"], g.round, qi, int(choice))
        st.success("Saved.")

elif g.stage == "minigame":
    st.subheader("Mini-Game: click the bullseye for 15 seconds")
    import streamlit.components.v1 as components
    st.write("Clicks are counted client-side, then posted back.")
    score = st.text_input("MiniGameScoreInternal", "0", label_visibility="collapsed", key="mg_score")
    html = """
    <div id="hud" style="margin:6px 0;color:#e5e7eb;">Clicks: 0 · Time left: 15s</div>
    <div id="box" style="position:relative;width:420px;height:140px;background:#0f172a;border:1px solid #334155;border-radius:10px;overflow:hidden">
      <div id="tgt" style="position:absolute;width:36px;height:36px;border-radius:50%;
       background:radial-gradient(circle at center,#f8fafc 0 6px,#ef4444 6px 12px,#f8fafc 12px 18px,#3b82f6 18px 36px);display:none;"></div>
    </div>
    <button id="start">Start</button>
    <script>
      const b=document.getElementById('box'), t=document.getElementById('tgt'), h=document.getElementById('hud'), s=document.getElementById('start');
      let c=0,left=15,active=false,timer=null;
      function rnd(){ t.style.left=(Math.random()*(b.clientWidth-36))+'px'; t.style.top=(Math.random()*(b.clientHeight-36))+'px';}
      function upd(){ h.textContent=`Clicks: ${c} · Time left: ${left}s`; }
      function end(){ active=false; t.style.display='none'; if(timer) clearInterval(timer); window.parent.postMessage({mg:c}, '*'); s.disabled=true; s.textContent='Completed'; }
      function start(){ c=0; left=15; active=true; upd(); t.style.display='block'; rnd(); timer=setInterval(()=>{ left--; upd(); if(left<=0) end(); },1000); }
      t.addEventListener('click',()=>{ if(!active) return; c++; upd(); rnd();}); s.addEventListener('click',start);
    </script>
    <script>
      window.addEventListener('message', ev => { try{
        if(ev.data && typeof ev.data.mg !== 'undefined'){
          const inp = window.parent.document.querySelector('input[aria-label="MiniGameScoreInternal"]');
          if(inp){ inp.value = String(ev.data.mg); inp.dispatchEvent(new Event('input',{bubbles:true})); }
        }}catch(e){} });
    </script>
    """
    components.html(html, height=220)
    if st.button("Submit mini-game score"):
        set_minigame_score(st.session_state["team_id"], g.round, int(st.session_state.get("mg_score","0")))
        st.success("Submitted.")

elif g.stage == "scoreboard":
    st.subheader("Scoreboard (read-only)")
    by_team = fetch_answers(g.room_code, g.round)
    def score_team(entry):
        corr = sum(1 for qi in range(1,6)
                   if entry["answers"].get(qi) is not None
                   and entry["answers"][qi] == round_qs[qi-1]["answer_idx"])
        bonus = (entry["mg"] or 0)//5
        return corr + bonus, corr, bonus
    rows = []
    for tid, entry in by_team.items():
        total,corr,bonus = score_team(entry)
        rows.append((entry["name"], total, corr, bonus, entry["mg"]))
    if rows:
        rows.sort(key=lambda r: r[1], reverse=True)
        st.table({"Team":[r[0] for r in rows], "Score":[r[1] for r in rows],
                  "Correct":[r[2] for r in rows], "Bonus":[r[3] for r in rows],
                  "MiniGame":[r[4] for r in rows]})
    else:
        st.info("No data yet. Wait for other teams / host.")
else:
    st.subheader("Waiting for host…")
