import streamlit as st
import json
from kbo_sim.season import (
    initialize_season_state, start_selected_game, simulate_live_pa, simulate_live_half, simulate_selected_game, simulate_next_day,
    live_force_bunt, live_apply_pinch_hitter, live_apply_pinch_runner, live_apply_manual_pitcher, apply_trade_action
)
from kbo_sim.ui import render_app

st.set_page_config(page_title="효진부터 시작되는 한화의 KS 우승!", layout="wide")

if "season" not in st.session_state:
    st.session_state["season"] = initialize_season_state(data_dir=".")

if "_last_processed_action" not in st.session_state:
    st.session_state["_last_processed_action"] = None

season = st.session_state["season"]

# 구 세션 호환: 런타임 필드 보정
if not hasattr(season, "starter_stamina"):
    season.starter_stamina = {}
if not hasattr(season, "trade_attempts_monthly"):
    season.trade_attempts_monthly = {}

action = render_app(season)

# region agent log
try:
    with open("debug-0290f3.log", "a", encoding="utf-8") as _f:
        _f.write(json.dumps({
            "sessionId": "0290f3",
            "runId": "pre-fix",
            "hypothesisId": "H2",
            "location": "app.py:action_dispatch",
            "message": "dispatch_action",
            "data": {"action": action},
            "timestamp": __import__("time").time(),
        }) + "\n")
except Exception:
    pass
# endregion agent log

# 중복 실행 방지
if action and action == st.session_state.get("_last_processed_action"):
    action = None

if action == "start_or_resume":
    try:
        start_selected_game(season)
    except Exception as e:
        season._last_error = f"start_or_resume 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "live_pa":
    try:
        simulate_live_pa(season)
    except Exception as e:
        season._last_error = f"live_pa 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "live_half":
    try:
        simulate_live_half(season)
    except Exception as e:
        season._last_error = f"live_half 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "simulate_selected":
    try:
        simulate_selected_game(season)
    except Exception as e:
        season._last_error = f"simulate_selected 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "simulate_day":
    try:
        simulate_next_day(season)
    except Exception as e:
        season._last_error = f"simulate_day 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "force_bunt":
    live_force_bunt(season)
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "apply_ph":
    name = getattr(season, "_last_ph_name", "")
    if name:
        live_apply_pinch_hitter(season, name)
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "apply_pr":
    name = getattr(season, "_last_pr_name", "")
    base_number = getattr(season, "_last_pr_base", 1)
    if name:
        live_apply_pinch_runner(season, base_number, name)
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "apply_manual_pitcher":
    role = getattr(season, "_last_manual_role", "")
    if role:
        live_apply_manual_pitcher(season, role)
    st.session_state["_last_processed_action"] = action
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
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "set_hanwha_game_idx":
    try:
        idx = int(getattr(season, "_last_hanwha_game_idx", 0) or 0)
        season.selected_hanwha_game_idx = max(0, idx)
    except Exception as e:
        season._last_error = f"set_hanwha_game_idx 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "update_batting_order":
    try:
        new_order = getattr(season, "_last_batting_order", [])
        if new_order:
            # 새로운 타순으로 스타터 업데이트
            from kbo_sim.config import USER_TEAM
            starters = season.team_hitters.get(USER_TEAM, {}).get("starters", [])
            # 이름 순서대로 정렬
            name_to_player = {p.get("name"): p for p in starters}
            reordered = [name_to_player.get(name) for name in new_order if name in name_to_player]
            # 타순 업데이트
            for idx, player in enumerate(reordered):
                if player:
                    player["order"] = idx + 1
            season.team_hitters[USER_TEAM]["starters"] = reordered
    except Exception as e:
        season._last_error = f"update_batting_order 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
elif action == "update_pitcher_rotation":
    try:
        new_order = getattr(season, "_last_pitcher_order", [])
        if new_order:
            from kbo_sim.config import USER_TEAM, STARTER_ROLES
            import copy

            pitchers = season.team_pitchers.get(USER_TEAM, {})
            role_to_pitcher = {role: copy.deepcopy(pitchers.get(role)) for role in STARTER_ROLES}

            # UI 순서(new_order)의 n번째 투수를 선발 n번 슬롯으로 배치
            for idx, target_role in enumerate(STARTER_ROLES):
                if idx < len(new_order):
                    source_role = new_order[idx]
                    src_pitcher = role_to_pitcher.get(source_role)
                    if src_pitcher is not None:
                        pitchers[target_role] = src_pitcher

            season.team_pitchers[USER_TEAM] = pitchers
    except Exception as e:
        season._last_error = f"update_pitcher_rotation 오류: {e}"
    st.session_state["_last_processed_action"] = action
    st.rerun()
