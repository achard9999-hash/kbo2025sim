import streamlit as st
from kbo_sim.season import (
    initialize_season_state, start_selected_game, simulate_live_pa, simulate_live_half, simulate_selected_game, simulate_next_day,
    live_force_bunt, live_apply_pinch_hitter, live_apply_pinch_runner, live_apply_manual_pitcher
)
from kbo_sim.ui import render_app

st.set_page_config(page_title="효진부터 시작되는 한화의 KS 우승!", layout="wide")

if "season" not in st.session_state:
    st.session_state["season"] = initialize_season_state(data_dir=".")

season = st.session_state["season"]
action = render_app(season)

if action == "start_or_resume":
    start_selected_game(season)
    st.rerun()
elif action == "live_pa":
    simulate_live_pa(season)
    st.rerun()
elif action == "live_half":
    simulate_live_half(season)
    st.rerun()
elif action == "simulate_selected":
    simulate_selected_game(season)
    st.rerun()
elif action == "simulate_day":
    simulate_next_day(season)
    st.rerun()
elif action == "force_bunt":
    live_force_bunt(season)
    st.rerun()
elif action == "apply_ph":
    name = getattr(season, "_last_ph_name", "")
    if name:
        live_apply_pinch_hitter(season, name)
    st.rerun()
elif action == "apply_pr":
    name = getattr(season, "_last_pr_name", "")
    base_number = getattr(season, "_last_pr_base", 1)
    if name:
        live_apply_pinch_runner(season, base_number, name)
    st.rerun()
elif action == "apply_manual_pitcher":
    role = getattr(season, "_last_manual_role", "")
    if role:
        live_apply_manual_pitcher(season, role)
    st.rerun()
