# lib/db.py
import json, time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

@dataclass
class Game:
    room_code: str
    round: int
    stage: str

def upsert_game(room_code: str) -> Game:
    sb = get_client()
    sb.table("games").upsert({"room_code": room_code}).execute()
    data = sb.table("games").select("*").eq("room_code", room_code).single().execute().data
    return Game(room_code=data["room_code"], round=data["round"], stage=data["stage"])

def set_stage(room_code: str, round_: int, stage: str):
    sb = get_client()
    sb.table("games").update({"round": round_, "stage": stage}).eq("room_code", room_code).execute()

def get_game(room_code: str) -> Optional[Game]:
    sb = get_client()
    res = sb.table("games").select("*").eq("room_code", room_code).maybe_single().execute()
    if not res.data: return None
    d = res.data
    return Game(room_code=d["room_code"], round=d["round"], stage=d["stage"])

def add_team(room_code: str, name: str) -> Tuple[str,str]:
    sb = get_client()
    d = sb.table("teams").insert({"room_code": room_code, "name": name}).execute().data[0]
    return d["id"], d["name"]

def list_teams(room_code: str):
    sb = get_client()
    return sb.table("teams").select("*").eq("room_code", room_code).order("created_at").execute().data

def save_answer(team_id: str, round_: int, q_index: int, choice: int):
    sb = get_client()
    sb.table("answers").upsert({
        "team_id": team_id, "round": round_, "q_index": q_index, "choice": choice
    }).execute()

def set_minigame_score(team_id: str, round_: int, score: int):
    sb = get_client()
    sb.table("minigames").upsert({"team_id": team_id, "round": round_, "score": score}).execute()

def fetch_answers(room_code: str, round_: int):
    sb = get_client()
    # join teams -> answers
    teams = list_teams(room_code)
    if not teams: return {}
    ids = [t["id"] for t in teams]
    ans = sb.table("answers").select("*").in_("team_id", ids).eq("round", round_).execute().data
    mg  = sb.table("minigames").select("*").in_("team_id", ids).eq("round", round_).execute().data
    by_team = {t["id"]: {"name": t["name"], "answers": {}, "mg": 0} for t in teams}
    for a in ans:
        by_team[a["team_id"]]["answers"][a["q_index"]] = a["choice"]
    for m in mg:
        by_team[m["team_id"]]["mg"] = m["score"]
    return by_team
