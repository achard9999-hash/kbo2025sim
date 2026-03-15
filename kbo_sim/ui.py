from __future__ import annotations

import pandas as pd
import streamlit as st

from .config import USER_TEAM
from .season import (
    current_date, current_day_schedule, hanwha_games_for_current_date, current_hanwha_game_row,
    start_selected_game, simulate_live_pa, simulate_live_half, simulate_selected_game, simulate_next_day,
    reorder_hanwha_lineup, bench_to_lineup, get_trade_market, execute_trade,
    live_force_bunt, live_apply_pinch_hitter, live_apply_pinch_runner, get_eligible_manual_pitchers, live_apply_manual_pitcher,
)


def _bases_text(game) -> str:
    arr = []
    for idx, b in enumerate(game.bases, start=1):
        if b:
            arr.append(f"{idx}루:{b['name']}")
    return " / ".join(arr) if arr else "주자 없음"


def render_app(season) -> str | None:
    st.title("효진부터 시작되는 한화의 KS 우승!")
    st.caption("한화 수동 운영 + 타 팀 자동 시뮬 + 날짜별 순위/리더보드")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.4])
    with c1:
        st.metric("현재 날짜", current_date(season))
    with c2:
        row = season.standings[season.standings["팀"] == USER_TEAM]
        st.metric("한화 순위", "-" if row.empty else f"{int(row.iloc[0]['순위'])}위")
    with c3:
        st.metric("완료 경기 수", len(season.game_results))
    with c4:
        latest = season.latest_game_result
        text = "-" if latest is None else f"{latest['Away']} {latest['Away_R']} : {latest['Home_R']} {latest['Home']}"
        st.metric("최근 결과", text)

    tabs = st.tabs(["오늘 일정", "실시간 경기", "한화 라인업", "트레이드", "순위", "리더보드"])

    action = None

    with tabs[0]:
        st.subheader("오늘 전체 일정")
        st.dataframe(current_day_schedule(season), use_container_width=True, hide_index=True)

        hg = hanwha_games_for_current_date(season)
        st.subheader("오늘 한화 경기")
        if hg.empty:
            st.info("오늘 한화 경기가 없습니다.")
        else:
            labels = [f"{r['Away']} vs {r['Home']}" for _, r in hg.iterrows()]
            idx = st.selectbox("진행할 한화 경기", range(len(labels)), index=min(season.selected_hanwha_game_idx, len(labels) - 1), format_func=lambda i: labels[i])
            season.selected_hanwha_game_idx = idx

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("한화 경기 시작/이어서 진행", use_container_width=True):
                action = "start_or_resume"
        with b2:
            if st.button("한화 경기 끝까지 + 나머지 자동", use_container_width=True):
                action = "simulate_selected"
        with b3:
            if st.button("오늘 경기 전부 자동", use_container_width=True):
                action = "simulate_day"

    with tabs[1]:
        row = current_hanwha_game_row(season)
        if season.live_game is None:
            if row is None:
                st.info("오늘 한화 경기가 없습니다.")
            else:
                st.info("아직 시작한 한화 경기가 없습니다. '한화 경기 시작/이어서 진행' 버튼을 누르세요.")
        else:
            game = season.live_game
            score_away = game.score["away"]
            score_home = game.score["home"]
            st.markdown(f"### {game.away.team} {score_away} : {score_home} {game.home.team}")
            st.write(f"**{game.inning}회 {'초' if game.half == 'top' else '말'} · {game.outs}아웃 · {_bases_text(game)}**")
            st.write(f"공격 팀: **{game.offense().team}** / 수비 팀: **{game.defense().team}**")
            st.write(f"다음 타자: **{game.current_batter_preview()['name']}** / 현재 투수: **{game.current_pitcher_preview()['name']}({game.defense().current_pitcher_role})**")

            cpa1, cpa2, cpa3 = st.columns(3)
            with cpa1:
                if st.button("1타석 진행", use_container_width=True):
                    action = "live_pa"
            with cpa2:
                if st.button("반이닝 진행", use_container_width=True):
                    action = "live_half"
            with cpa3:
                if st.button("경기 끝까지 진행", use_container_width=True):
                    action = "simulate_selected"

            st.markdown("#### 감독 개입")
            m1, m2 = st.columns(2)
            with m1:
                if st.button("다음 타석 강제 번트", use_container_width=True):
                    action = "force_bunt"
                bench_names = [p["name"] for p in game.offense().bench] if game.offense().team == USER_TEAM else []
                if bench_names:
                    ph_name = st.selectbox("대타", [""] + bench_names, key="ph_name")
                    if st.button("대타 적용", use_container_width=True):
                        season._last_ph_name = ph_name
                        action = "apply_ph"
            with m2:
                bench_names_run = [p["name"] for p in game.offense().bench] if game.offense().team == USER_TEAM else []
                base_choices = []
                for i, b in enumerate(game.bases, start=1):
                    if b is not None:
                        base_choices.append(i)
                pr_name = st.selectbox("대주자", [""] + bench_names_run, key="pr_name")
                pr_base = st.selectbox("대주자 투입 베이스", base_choices if base_choices else [1], key="pr_base")
                if st.button("대주자 적용", use_container_width=True):
                    season._last_pr_name = pr_name
                    season._last_pr_base = pr_base
                    action = "apply_pr"

            eligible_roles = get_eligible_manual_pitchers(season)
            if eligible_roles:
                manual_role = st.selectbox("강제 투수 교체", [""] + eligible_roles, key="manual_role")
                if st.button("강제 투수 교체 적용", use_container_width=True):
                    season._last_manual_role = manual_role
                    action = "apply_manual_pitcher"

            st.markdown("#### 최근 플레이 로그")
            st.dataframe(pd.DataFrame({"로그": game.feed[-30:][::-1]}), use_container_width=True, hide_index=True)

    with tabs[2]:
        starters = season.team_hitters[USER_TEAM]["starters"]
        bench = season.team_hitters[USER_TEAM]["bench"]
        st.subheader("한화 선발 라인업")
        for p in sorted(starters, key=lambda x: x["order"]):
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.write(f"{p['order']}번 {p['name']} / {p['pos']} / OPS {p['ops']:.3f} / wRAA {p['wraa']:.1f}")
            with c2:
                if st.button("▲", key=f"up_{p['name']}"):
                    reorder_hanwha_lineup(season, p["name"], -1)
                    st.rerun()
            with c3:
                if st.button("▼", key=f"dn_{p['name']}"):
                    reorder_hanwha_lineup(season, p["name"], 1)
                    st.rerun()

        st.subheader("벤치 -> 선발 교체")
        bench_names = [p["name"] for p in bench]
        if bench_names:
            chosen = st.selectbox("벤치 선수", [""] + bench_names, key="bench_to_lineup")
            if st.button("선발 기용", use_container_width=True):
                if chosen:
                    bench_to_lineup(season, chosen)
                    st.rerun()
        else:
            st.info("벤치 선수가 없습니다.")

    with tabs[3]:
        teams = [t for t in season.team_hitters.keys() if t != USER_TEAM]
        opp = st.selectbox("상대 팀", teams, key="trade_opp")
        market = get_trade_market(season, opp)
        target_names = [p["name"] for p in market]
        target = st.selectbox("영입 대상", [""] + target_names, key="trade_target")
        offer_names = [p["name"] for p in season.team_hitters[USER_TEAM]["bench"] if not p.get("foreign", False)]
        offered = st.multiselect("제안 선수(한화 벤치)", offer_names, key="trade_offer")
        if st.button("트레이드 제안", use_container_width=True):
            ok, msg = execute_trade(season, opp, target, offered)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)
        st.dataframe(pd.DataFrame(market)[["name", "pos", "ops", "wraa"]].rename(columns={"name":"선수명","pos":"포지션","ops":"OPS","wraa":"wRAA"}), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.dataframe(season.standings, use_container_width=True, hide_index=True)

    with tabs[5]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("타자 리더보드")
            st.dataframe(season.batter_leaders.head(30), use_container_width=True, hide_index=True)
        with c2:
            st.subheader("투수 리더보드 (RA9)")
            st.dataframe(season.pitcher_leaders.head(30), use_container_width=True, hide_index=True)

    return action
