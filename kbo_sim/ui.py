from __future__ import annotations

import pandas as pd
import streamlit as st

from .config import USER_TEAM
from .season import (
    current_day_schedule,
    hanwha_games_for_current_date,
    current_hanwha_game_row,
    reorder_hanwha_lineup,
    bench_to_lineup,
    get_trade_market,
    execute_trade,
    build_live_game_payload,
    build_season_summary_payload,
    build_app_payload,
)
from .ui_component import render_hanwha_dashboard_component, component_is_ready


def _inject_global_css():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.5rem;
            max-width: 1450px;
        }

        .ss-page-bg {
            background:
                radial-gradient(circle at top left, rgba(59,130,246,0.10), transparent 28%),
                radial-gradient(circle at top right, rgba(239,68,68,0.08), transparent 25%),
                linear-gradient(180deg, #eef4ff 0%, #f8fbff 35%, #f3f6fb 100%);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 24px;
            padding: 1rem 1rem 1.25rem 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }

        .ss-hero {
            border-radius: 24px;
            overflow: hidden;
            border: 2px solid #1e293b;
            box-shadow: 0 14px 0 #334155, 0 18px 36px rgba(15,23,42,0.16);
            background: #ffffff;
            margin-bottom: 1rem;
        }

        .ss-hero-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 55%, #0ea5e9 100%);
            color: white;
            padding: 16px 20px;
        }

        .ss-hero-title {
            font-size: 1.6rem;
            font-weight: 900;
            line-height: 1.2;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }

        .ss-hero-sub {
            font-size: 0.95rem;
            font-weight: 600;
            opacity: 0.92;
        }

        .ss-hero-badge {
            background: #bae6fd;
            color: #082f49;
            border: 2px solid rgba(255,255,255,0.65);
            border-radius: 16px;
            padding: 10px 14px;
            font-weight: 900;
            white-space: nowrap;
            box-shadow: inset 0 -2px 0 rgba(0,0,0,0.08);
        }

        .ss-hud-card {
            background: white;
            border: 2px solid #cbd5e1;
            border-radius: 20px;
            padding: 14px 16px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            min-height: 104px;
        }

        .ss-hud-label {
            font-size: 0.82rem;
            font-weight: 800;
            color: #64748b;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .ss-hud-value {
            font-size: 1.55rem;
            font-weight: 900;
            color: #0f172a;
            line-height: 1.2;
            word-break: keep-all;
        }

        .ss-hud-sub {
            margin-top: 6px;
            font-size: 0.84rem;
            color: #475569;
            font-weight: 600;
        }

        .ss-section-title {
            font-size: 1.15rem;
            font-weight: 900;
            color: white;
            background: #475569;
            border-radius: 12px;
            padding: 10px 14px;
            margin-bottom: 10px;
            display: inline-block;
        }

        .ss-card {
            background: white;
            border: 2px solid #cbd5e1;
            border-radius: 22px;
            padding: 16px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
            margin-bottom: 12px;
        }

        .ss-card-title {
            font-size: 1.02rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 10px;
        }

        .ss-soft-note {
            border-radius: 16px;
            border: 1px solid #fde68a;
            background: #fffbeb;
            color: #92400e;
            padding: 12px 14px;
            font-size: 0.92rem;
            font-weight: 700;
        }

        .ss-score-wrap {
            background: linear-gradient(180deg, #64748b 0%, #64748b 12%, #334155 12%, #334155 100%);
            border-radius: 24px;
            border: 3px solid #1e293b;
            box-shadow: 0 12px 0 #334155, 0 18px 28px rgba(15,23,42,0.18);
            padding: 14px;
            color: white;
        }

        .ss-score-head {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 12px;
            align-items: center;
            margin-bottom: 14px;
        }

        .ss-team-box {
            background: rgba(255,255,255,0.10);
            border: 2px solid rgba(255,255,255,0.18);
            border-radius: 18px;
            padding: 12px 14px;
        }

        .ss-team-label {
            font-size: 0.78rem;
            font-weight: 800;
            color: #cbd5e1;
            margin-bottom: 4px;
        }

        .ss-team-name {
            font-size: 1.45rem;
            font-weight: 900;
            line-height: 1.1;
        }

        .ss-team-score {
            font-size: 3.1rem;
            font-weight: 900;
            line-height: 1;
            text-align: center;
            min-width: 72px;
        }

        .ss-mid-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.82rem;
            font-weight: 900;
            background: #f8fafc;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        .ss-info-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 9px 0;
            border-bottom: 1px solid #e2e8f0;
        }

        .ss-info-row:last-child {
            border-bottom: none;
        }

        .ss-info-label {
            color: #64748b;
            font-weight: 700;
        }

        .ss-info-value {
            color: #0f172a;
            font-weight: 900;
            text-align: right;
        }

        .ss-lineup-row {
            background: white;
            border: 2px solid #dbe4ee;
            border-radius: 18px;
            padding: 10px 12px;
            margin-bottom: 8px;
        }

        .ss-lineup-name {
            font-size: 1rem;
            font-weight: 900;
            color: #0f172a;
        }

        .ss-lineup-meta {
            font-size: 0.88rem;
            font-weight: 700;
            color: #475569;
            margin-top: 2px;
        }

        .ss-tab-note {
            color: #64748b;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_top_banner(season_summary: dict):
    latest_text = season_summary.get("latest_result_text", "-")
    st.markdown(
        f"""
        <div class="ss-page-bg">
            <div class="ss-hero">
                <div class="ss-hero-top">
                    <div>
                        <div class="ss-hero-title">효진부터 시작되는 한화의 KS 우승!</div>
                        <div class="ss-hero-sub">한화 수동 운영 + 타 팀 자동 시뮬 + 날짜별 순위/리더보드</div>
                    </div>
                    <div class="ss-hero-badge">최근 결과 · {latest_text}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_summary_cards(season_summary: dict):
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.55])

    with c1:
        st.markdown(
            f"""
            <div class="ss-hud-card">
                <div class="ss-hud-label">현재 날짜</div>
                <div class="ss-hud-value">{season_summary.get("current_date", "-")}</div>
                <div class="ss-hud-sub">시즌 진행 기준일</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="ss-hud-card">
                <div class="ss-hud-label">한화 순위</div>
                <div class="ss-hud-value">{season_summary.get("hanwha_rank_text", "-")}</div>
                <div class="ss-hud-sub">실시간 순위 반영</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="ss-hud-card">
                <div class="ss-hud-label">완료 경기 수</div>
                <div class="ss-hud-value">{season_summary.get("completed_game_count", 0)}</div>
                <div class="ss-hud-sub">시뮬 완료 누적</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="ss-hud-card">
                <div class="ss-hud-label">최근 결과</div>
                <div class="ss-hud-value" style="font-size:1.15rem;">{season_summary.get("latest_result_text", "-")}</div>
                <div class="ss-hud-sub">가장 최근 종료 경기</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _section_title(text: str):
    st.markdown(f"""<div class="ss-section-title">{text}</div>""", unsafe_allow_html=True)


def _info_row(label: str, value: str):
    st.markdown(
        f"""
        <div class="ss-info-row">
            <div class="ss-info-label">{label}</div>
            <div class="ss-info-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _translate_component_action(season, comp_action):
    if not comp_action or not isinstance(comp_action, dict):
        return None

    action_type = comp_action.get("type", "")
    payload = comp_action.get("payload", {}) or {}

    if action_type == "apply_ph":
        season._last_ph_name = payload.get("name", "")
        return "apply_ph"

    if action_type == "apply_pr":
        season._last_pr_name = payload.get("name", "")
        season._last_pr_base = payload.get("base_number", 1)
        return "apply_pr"

    if action_type == "apply_manual_pitcher":
        season._last_manual_role = payload.get("role", "")
        return "apply_manual_pitcher"

    if action_type in {
        "start_or_resume",
        "live_pa",
        "live_half",
        "simulate_selected",
        "simulate_day",
        "force_bunt",
    }:
        return action_type

    return None


def _render_schedule_tab(season):
    action = None

    _section_title("오늘 일정")
    st.markdown('<div class="ss-tab-note">오늘 날짜 기준 전체 일정과 한화 진행 액션입니다.</div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="ss-card-title">오늘 전체 일정</div>', unsafe_allow_html=True)
    st.dataframe(current_day_schedule(season), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    hg = hanwha_games_for_current_date(season)

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="ss-card-title">오늘 한화 경기</div>', unsafe_allow_html=True)

    if hg.empty:
        st.info("오늘 한화 경기가 없습니다.")
    else:
        labels = [f"{r['Away']} vs {r['Home']}" for _, r in hg.iterrows()]
        idx = st.selectbox(
            "진행할 한화 경기",
            range(len(labels)),
            index=min(season.selected_hanwha_game_idx, len(labels) - 1),
            format_func=lambda i: labels[i],
        )
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

    st.markdown('</div>', unsafe_allow_html=True)
    return action


def _render_live_game_tab_fallback(season):
    action = None
    payload = build_live_game_payload(season)
    game_payload = payload.get("game_state")
    manager_actions = payload.get("manager_actions", {})

    if not payload.get("has_live_game", False) or game_payload is None:
        row = current_hanwha_game_row(season)
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">라이브 경기 상태</div>', unsafe_allow_html=True)
        if row is None:
            st.info("오늘 한화 경기가 없습니다.")
        else:
            st.info("아직 시작한 한화 경기가 없습니다. '한화 경기 시작/이어서 진행' 버튼을 누르세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        return action

    st.markdown(
        f"""
        <div class="ss-score-wrap">
            <div class="ss-score-head">
                <div class="ss-team-box">
                    <div class="ss-team-label">AWAY</div>
                    <div class="ss-team-name">{game_payload['away_team']}</div>
                </div>
                <div class="ss-team-score">{game_payload['score']['away']} : {game_payload['score']['home']}</div>
                <div class="ss-team-box" style="text-align:right;">
                    <div class="ss-team-label">HOME</div>
                    <div class="ss-team-name">{game_payload['home_team']}</div>
                </div>
            </div>
            <div>
                <span class="ss-mid-chip">{game_payload['inning']}회 {game_payload['half_kor']}</span>
                <span class="ss-mid-chip">{game_payload['outs']}아웃</span>
                <span class="ss-mid-chip">{game_payload['bases_text']}</span>
                <span class="ss-mid-chip">공격 {game_payload['offense_team']}</span>
                <span class="ss-mid-chip">수비 {game_payload['defense_team']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([1.05, 0.95])

    with top_left:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">현재 경기 상태</div>', unsafe_allow_html=True)

        current_batter = game_payload.get("current_batter") or {}
        current_pitcher = game_payload.get("current_pitcher") or {}

        _info_row("공격 팀", game_payload.get("offense_team", "-"))
        _info_row("수비 팀", game_payload.get("defense_team", "-"))
        _info_row("다음 타자", current_batter.get("name", "-"))
        _info_row("현재 투수", f"{current_pitcher.get('name', '-')}" + (f" ({current_pitcher.get('role', '')})" if current_pitcher.get("role") else ""))
        st.markdown('</div>', unsafe_allow_html=True)

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

    with top_right:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">감독 개입</div>', unsafe_allow_html=True)

        b1, b2 = st.columns(2)

        with b1:
            if st.button("다음 타석 강제 번트", use_container_width=True, disabled=not manager_actions.get("can_force_bunt", False)):
                action = "force_bunt"

            ph_candidates = manager_actions.get("bench_for_ph", [])
            ph_names = [p["name"] for p in ph_candidates]
            if ph_names:
                ph_name = st.selectbox("대타", [""] + ph_names, key="ph_name")
                if st.button("대타 적용", use_container_width=True):
                    season._last_ph_name = ph_name
                    action = "apply_ph"

        with b2:
            pr_candidates = manager_actions.get("bench_for_pr", [])
            pr_names = [p["name"] for p in pr_candidates]
            pr_base_choices = manager_actions.get("pr_base_choices", [])

            pr_name = st.selectbox("대주자", [""] + pr_names, key="pr_name")
            pr_base = st.selectbox("대주자 투입 베이스", pr_base_choices if pr_base_choices else [1], key="pr_base")
            if st.button("대주자 적용", use_container_width=True):
                season._last_pr_name = pr_name
                season._last_pr_base = pr_base
                action = "apply_pr"

        eligible_roles = manager_actions.get("eligible_manual_pitchers", [])
        if eligible_roles:
            manual_role = st.selectbox("강제 투수 교체", [""] + eligible_roles, key="manual_role")
            if st.button("강제 투수 교체 적용", use_container_width=True):
                season._last_manual_role = manual_role
                action = "apply_manual_pitcher"

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="ss-card-title">최근 플레이 로그</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({"로그": game_payload.get("feed_display", [])}), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    return action


def _render_live_game_tab(season):
    _section_title("실시간 경기")

    app_payload = build_app_payload(season)

    if component_is_ready():
        comp_action = render_hanwha_dashboard_component(
            app_payload=app_payload,
            key="hanwha_live_game_component",
        )
        translated = _translate_component_action(season, comp_action)
        if translated is not None:
            return translated
        st.caption("React 컴포넌트 연결됨")
        return None

    st.caption("React 빌드가 없어서 Streamlit fallback UI로 표시 중")
    return _render_live_game_tab_fallback(season)


def _render_lineup_tab(season):
    _section_title("한화 라인업")

    starters = season.team_hitters[USER_TEAM]["starters"]
    bench = season.team_hitters[USER_TEAM]["bench"]

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="ss-card-title">한화 선발 라인업</div>', unsafe_allow_html=True)

    for p in sorted(starters, key=lambda x: x["order"]):
        c1, c2, c3 = st.columns([5, 1, 1])
        with c1:
            st.markdown(
                f"""
                <div class="ss-lineup-row">
                    <div class="ss-lineup-name">{p['order']}번 {p['name']}</div>
                    <div class="ss-lineup-meta">{p['pos']} · OPS {p['ops']:.3f} · wRAA {p['wraa']:.1f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("▲", key=f"up_{p['name']}"):
                reorder_hanwha_lineup(season, p["name"], -1)
                st.rerun()
        with c3:
            if st.button("▼", key=f"dn_{p['name']}"):
                reorder_hanwha_lineup(season, p["name"], 1)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="ss-card-title">벤치 → 선발 교체</div>', unsafe_allow_html=True)

    bench_names = [p["name"] for p in bench]
    if bench_names:
        chosen = st.selectbox("벤치 선수", [""] + bench_names, key="bench_to_lineup")
        if st.button("선발 기용", use_container_width=True):
            if chosen:
                bench_to_lineup(season, chosen)
                st.rerun()
    else:
        st.info("벤치 선수가 없습니다.")

    st.markdown(
        '<div class="ss-soft-note">현재는 한화만 수동 조정하는 구조를 유지했습니다. 이후 전체 탭 컴포넌트화도 가능함.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


def _render_trade_tab(season):
    _section_title("트레이드")

    teams = [t for t in season.team_hitters.keys() if t != USER_TEAM]
    left, right = st.columns([0.95, 1.05])

    with left:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">트레이드 대상 선택</div>', unsafe_allow_html=True)

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

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">상대 팀 마켓 미리보기</div>', unsafe_allow_html=True)

        opp = st.session_state.get("trade_opp", teams[0] if teams else "")
        market = get_trade_market(season, opp) if opp else []

        if market:
            df_market = pd.DataFrame(market)[["name", "pos", "ops", "wraa"]].rename(
                columns={"name": "선수명", "pos": "포지션", "ops": "OPS", "wraa": "wRAA"}
            )
            st.dataframe(df_market, use_container_width=True, hide_index=True)
        else:
            st.info("표시할 트레이드 대상이 없습니다.")

        st.markdown('</div>', unsafe_allow_html=True)


def _render_standings_tab(season):
    _section_title("순위")
    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown('<div class="ss-card-title">현재 리그 순위</div>', unsafe_allow_html=True)
    st.dataframe(season.standings, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_leaderboard_tab(season):
    _section_title("리더보드")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">타자 리더보드</div>', unsafe_allow_html=True)
        st.dataframe(season.batter_leaders.head(30), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown('<div class="ss-card-title">투수 리더보드 (RA9)</div>', unsafe_allow_html=True)
        st.dataframe(season.pitcher_leaders.head(30), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_app(season) -> str | None:
    _inject_global_css()

    season_summary = build_season_summary_payload(season)
    _render_top_banner(season_summary)
    _render_summary_cards(season_summary)

    tabs = st.tabs(["오늘 일정", "실시간 경기", "한화 라인업", "트레이드", "순위", "리더보드"])

    action = None

    with tabs[0]:
        action = _render_schedule_tab(season)

    with tabs[1]:
        tab_action = _render_live_game_tab(season)
        if tab_action is not None:
            action = tab_action

    with tabs[2]:
        _render_lineup_tab(season)

    with tabs[3]:
        _render_trade_tab(season)

    with tabs[4]:
        _render_standings_tab(season)

    with tabs[5]:
        _render_leaderboard_tab(season)

    return action