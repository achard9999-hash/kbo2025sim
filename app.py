import streamlit as st
from kbo_sim.season import initialize_season_state, simulate_selected_game, simulate_next_day
from kbo_sim.ui import render_app

st.set_page_config(page_title="효진부터 시작되는 한화의 KS 우승!", layout="wide")

if "season" not in st.session_state:
    st.session_state["season"] = initialize_season_state(data_dir=".")

season = st.session_state["season"]

action = render_app(season)

if action == "simulate_selected":
    simulate_selected_game(season)
    st.rerun()
elif action == "simulate_day":
    simulate_next_day(season)
    st.rerun()
elif action == "reset":
    st.session_state["season"] = initialize_season_state(data_dir=".")
    st.rerun()
