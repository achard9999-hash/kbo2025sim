import streamlit as st
from kbo_sim.season import (
    initialize_season_state, start_selected_game, simulate_live_pa, simulate_live_half, simulate_selected_game, simulate_next_day,
    live_force_bunt, live_apply_pinch_hitter, live_apply_pinch_runner, live_apply_manual_pitcher, apply_trade_action
)
from kbo_sim.ui import render_app

st.set_page_config(page_title="효진부터 시작되는 한화의 KS 우승!", layout="wide")

if "season" not in st.session_state:
    st.session_state["season"] = initialize_season_state(data_dir=".")

season = st.session_state["season"]
action = render_app(season)

if action == "start_or_resume":
    try:
        start_selected_game(season)
    except Exception as e:
        season._last_error = f"start_or_resume 오류: {e}"
    st.rerun()
elif action == "live_pa":
    try:
        simulate_live_pa(season)
    except Exception as e:
        season._last_error = f"live_pa 오류: {e}"
    st.rerun()
elif action == "live_half":
    try:
        simulate_live_half(season)
    except Exception as e:
        season._last_error = f"live_half 오류: {e}"
    st.rerun()
elif action == "simulate_selected":
    try:
        simulate_selected_game(season)
    except Exception as e:
        season._last_error = f"simulate_selected 오류: {e}"
    st.rerun()
elif action == "simulate_day":
    try:
        simulate_next_day(season)
    except Exception as e:
        season._last_error = f"simulate_day 오류: {e}"
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
elif action == "execute_trade":
    opp = getattr(season, "_last_trade_opp", "")
    target = getattr(season, "_last_trade_target", "")
    offered = getattr(season, "_last_trade_offered", []) or []
    if opp and target:
        try:
            apply_trade_action(season, opp, target, offered)
        except Exception as e:
            season._last_error = f"execute_trade 오류: {e}"
    st.rerun()
elif action == "set_hanwha_game_idx":
    try:
        idx = int(getattr(season, "_last_hanwha_game_idx", 0) or 0)
        season.selected_hanwha_game_idx = max(0, idx)
    except Exception as e:
        season._last_error = f"set_hanwha_game_idx 오류: {e}"
    st.rerun()
