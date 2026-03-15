from __future__ import annotations

import pandas as pd
import streamlit as st

from .season import current_date, current_day_schedule, hanwha_games_for_current_date
from .config import USER_TEAM


def render_app(season) -> str | None:
    st.title("효진부터 시작되는 한화의 KS 우승!")
    st.caption("한화 수동 운영 + 타 팀 자동 시뮬 + 날짜별 순위/리더보드 반영")

    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 1.5])
    with col1:
        st.metric("현재 날짜", current_date(season))
    with col2:
        standings = season.standings
        hanwha_row = standings[standings["팀"] == USER_TEAM]
        if not hanwha_row.empty:
            st.metric("한화 순위", f"{int(hanwha_row.iloc[0]['순위'])}위")
        else:
            st.metric("한화 순위", "-")
    with col3:
        st.metric("완료 경기 수", len(season.game_results))
    with col4:
        latest = season.latest_game_result
        st.metric("최근 결과", f"{latest['Away']} {latest['Away_R']} : {latest['Home_R']} {latest['Home']}" if latest else "-")

    tab1, tab2, tab3, tab4 = st.tabs(["오늘 일정", "시뮬레이션 결과", "순위", "리더보드"])

    action = None

    with tab1:
        day = current_day_schedule(season)
        st.subheader("오늘 전체 일정")
        st.dataframe(day, use_container_width=True, hide_index=True)

        hg = hanwha_games_for_current_date(season)
        st.subheader("오늘 한화 경기")
        if hg.empty:
            st.info("오늘 한화 경기가 없습니다. '하루 자동 진행'을 누르세요.")
        else:
            labels = [f"{r['Away']} vs {r['Home']}" for _, r in hg.iterrows()]
            selected = st.selectbox("진행할 한화 경기", range(len(labels)), format_func=lambda i: labels[i], index=min(season.selected_hanwha_game_idx, len(labels)-1))
            season.selected_hanwha_game_idx = selected

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("선택한 한화 경기 진행", use_container_width=True):
                action = "simulate_selected"
        with c2:
            if st.button("오늘 경기 전부 진행", use_container_width=True):
                action = "simulate_day"
        with c3:
            if st.button("시즌 초기화", use_container_width=True):
                action = "reset"

    with tab2:
        st.subheader("최근 시뮬레이션 결과")
        latest = season.latest_game_result
        if latest is None:
            st.info("아직 시뮬레이션한 경기가 없습니다.")
        else:
            st.markdown(f"**{latest['날짜']} | {latest['Away']} {latest['Away_R']} : {latest['Home_R']} {latest['Home']}**")
            c1, c2 = st.columns(2)
            with c1:
                st.write("최근 플레이 로그")
                st.dataframe(pd.DataFrame({"로그": latest["feed"][-50:][::-1]}), use_container_width=True, hide_index=True)
            with c2:
                st.write("투수 사용")
                st.dataframe(pd.DataFrame(latest["pitcher_box"]), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("날짜 기준 순위")
        st.dataframe(season.standings, use_container_width=True, hide_index=True)

    with tab4:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("타자 리더보드")
            st.dataframe(season.batter_leaders.head(20), use_container_width=True, hide_index=True)
        with c2:
            st.subheader("투수 리더보드 (RA9)")
            st.dataframe(season.pitcher_leaders.head(20), use_container_width=True, hide_index=True)

    return action
