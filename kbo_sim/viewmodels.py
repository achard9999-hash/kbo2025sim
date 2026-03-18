from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .config import USER_TEAM


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _format_innings(innings: float) -> str:
    """Format innings as 'X' or 'X 1/3' or 'X 2/3' format."""
    if not isinstance(innings, (int, float)):
        try:
            innings = float(innings)
        except Exception:
            return "0"
    
    whole = int(innings)
    frac = innings - whole
    
    if frac < 0.15:  # 0.0-0.15 범위는 0 또는 반올림 오차
        return str(whole)
    elif frac < 0.5:  # 0.15-0.5 범위는 1/3
        return f"{whole} 1/3"
    elif frac < 0.85:  # 0.5-0.85 범위는 2/3
        return f"{whole} 2/3"
    else:  # 0.85 이상은 올림
        return str(whole + 1)


def _format_stat(value: float, decimal_places: int = 3) -> str:
    """Format stat value to specified decimal places."""
    if not isinstance(value, (int, float)):
        try:
            value = float(value)
        except Exception:
            return "0"
    
    if decimal_places == 0:
        return str(int(round(value)))
    elif decimal_places == 2:
        return f"{value:.2f}"
    elif decimal_places == 3:
        return f"{value:.3f}"
    else:
        return f"{value:.{decimal_places}f}"


def serialize_player_brief(player: Optional[dict], today_stats: Optional[Dict[Tuple[str, str], dict]] = None) -> Optional[dict]:
    if not player:
        return None
    team = str(player.get("team", ""))
    name = str(player.get("name", ""))
    key = (team, name)
    today = today_stats.get(key) if today_stats else None
    today_avg = today.get("avg") if today is not None else None

    return {
        "name": player.get("name", ""),
        "pos": player.get("pos", ""),
        "order": _safe_int(player.get("order", 0)),
        "avg": _safe_float(player.get("avg", 0.0)),
        "ops": _safe_float(player.get("ops", 0.0)),
        "wraa": _safe_float(player.get("wraa", 0.0)),
        "foreign": bool(player.get("foreign", False)),
        "today_avg": today_avg,
    }


def serialize_pitcher_brief(role: str, pitcher: Optional[dict]) -> Optional[dict]:
    if not pitcher:
        return None
    return {
        "name": pitcher.get("name", ""),
        "role": role or "",
        "era": _safe_float(pitcher.get("era", 0.0)),
        "whip": _safe_float(pitcher.get("whip", 0.0)),
        "k_rate": _safe_float(pitcher.get("k_rate", 0.0)),
        "foreign": bool(pitcher.get("foreign", False)),
    }


def serialize_bases(bases: List[Optional[dict]]) -> List[Optional[dict]]:
    out: List[Optional[dict]] = []
    for idx, runner in enumerate(bases, start=1):
        if runner is None:
            out.append(None)
        else:
            out.append(
                {
                    "base": idx,
                    "name": runner.get("name", ""),
                    "pos": runner.get("pos", ""),
                    "order": _safe_int(runner.get("order", 0)),
                }
            )
    return out


def serialize_line_score(line_score: dict) -> dict:
    away = list(line_score.get("away", []))
    home = list(line_score.get("home", []))
    return {
        "away": away,
        "home": home,
        "away_display": [str(x) for x in away] + [""] * max(0, 9 - len(away)),
        "home_display": [str(x) for x in home] + [""] * max(0, 9 - len(home)),
    }


def serialize_team_state(team_state, today_stats: Optional[Dict[Tuple[str, str], dict]] = None) -> dict:
    lineup = sorted(team_state.lineup, key=lambda x: x.get("order", 0))
    bench = list(team_state.bench)

    return {
        "team": team_state.team,
        "batting_index": _safe_int(team_state.batting_index, 0),
        "current_pitcher_role": team_state.current_pitcher_role,
        "pending_force_bunt": bool(team_state.pending_force_bunt),
        "pending_manual_pitcher_role": team_state.pending_manual_pitcher_role,
        "manual_chase_changes_used": _safe_int(team_state.manual_chase_changes_used, 0),
        "lineup": [serialize_player_brief(p, today_stats=today_stats) for p in lineup],
        "bench": [serialize_player_brief(p, today_stats=today_stats) for p in bench],
        "current_pitcher": serialize_pitcher_brief(
            team_state.current_pitcher_role,
            team_state.current_pitcher() if team_state.current_pitcher_role else None,
        ),
    }


def _build_today_batting_stats(game) -> Dict[Tuple[str, str], dict]:
    stats: Dict[Tuple[str, str], dict] = {}
    for row in game.batter_box:
        team = str(row.get("team", ""))
        name = str(row.get("name", ""))
        key = (team, name)
        if key not in stats:
            stats[key] = {"ab": 0, "h": 0, "bb": 0}
        stats[key]["ab"] += _safe_int(row.get("AB", 0), 0)
        stats[key]["h"] += _safe_int(row.get("H", 0), 0)
        stats[key]["bb"] += _safe_int(row.get("BB", 0), 0)

    for key, s in stats.items():
        ab = max(1, s["ab"]) if s["ab"] > 0 else 0
        if ab > 0:
            s["avg"] = s["h"] / float(ab)
        else:
            s["avg"] = None
    return stats


def _build_team_walk_totals(today_stats: Dict[Tuple[str, str], dict]) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    for (team, _), s in today_stats.items():
        totals[team] = totals.get(team, 0) + _safe_int(s.get("bb", 0), 0)
    return totals


def build_live_game_payload(state, eligible_manual_roles: Optional[List[str]] = None) -> dict:
    row = None
    try:
        row = state.data.schedule[
            (state.data.schedule["날짜"] == state.data.all_dates[state.current_date_idx])
            & ((state.data.schedule["Away"] == USER_TEAM) | (state.data.schedule["Home"] == USER_TEAM))
        ]
    except Exception:
        row = None

    game = state.live_game
    meta = state.live_game_meta or {}

    if game is None:
        return {
            "schema_version": "live_game_v1",
            "has_live_game": False,
            "selected_game": {
                "date": meta.get("date"),
                "away": meta.get("away"),
                "home": meta.get("home"),
                "key": meta.get("key"),
            },
            "game_state": None,
            "manager_actions": {
                "can_force_bunt": False,
                "bench_for_ph": [],
                "bench_for_pr": [],
                "pr_base_choices": [],
                "eligible_manual_pitchers": eligible_manual_roles or [],
            },
        }

    offense = game.offense()
    defense = game.defense()
    current_batter = game.current_batter_preview()
    current_pitcher = game.current_pitcher_preview()
    bases = serialize_bases(game.bases)

    today_stats = _build_today_batting_stats(game)
    walk_totals = _build_team_walk_totals(today_stats)

    bench_for_user_offense = []
    if offense.team == USER_TEAM:
        bench_for_user_offense = [serialize_player_brief(p) for p in offense.bench]

    pr_base_choices = [idx for idx, runner in enumerate(game.bases, start=1) if runner is not None]

    away_team = game.away.team
    home_team = game.home.team

    payload = {
        "schema_version": "live_game_v1",
        "has_live_game": True,
        "selected_game": {
            "date": meta.get("date"),
            "away": meta.get("away"),
            "home": meta.get("home"),
            "key": meta.get("key"),
        },
        "game_state": {
            "away_team": away_team,
            "home_team": home_team,
            "score": {
                "away": _safe_int(game.score.get("away", 0)),
                "home": _safe_int(game.score.get("home", 0)),
            },
            "hits": {
                "away": _safe_int(game.hits.get("away", 0)),
                "home": _safe_int(game.hits.get("home", 0)),
            },
            "errors": {
                "away": _safe_int(game.errors.get("away", 0)),
                "home": _safe_int(game.errors.get("home", 0)),
            },
            "inning": _safe_int(game.inning, 1),
            "half": game.half,
            "half_kor": "초" if game.half == "top" else "말",
            "outs": _safe_int(game.outs, 0),
            "bases": bases,
            "bases_text": " / ".join([f"{b['base']}루:{b['name']}" for b in bases if b]) if any(bases) else "주자 없음",
            "finished": bool(game.finished),
            "line_score": serialize_line_score(game.line_score),
            "feed": list(game.feed[-30:]),
            "feed_display": list(game.feed[-30:][::-1]),
            "offense_team": offense.team,
            "defense_team": defense.team,
            "offense": serialize_team_state(offense, today_stats=today_stats),
            "defense": serialize_team_state(defense, today_stats=today_stats),
            "away_state": serialize_team_state(game.away, today_stats=today_stats),
            "home_state": serialize_team_state(game.home, today_stats=today_stats),
            "current_batter": serialize_player_brief(current_batter, today_stats=today_stats),
            "current_pitcher": serialize_pitcher_brief(defense.current_pitcher_role, current_pitcher),
            "offense_is_user_team": offense.team == USER_TEAM,
            "defense_is_user_team": defense.team == USER_TEAM,
            "totals": {
                "away": {
                    "R": _safe_int(game.score.get("away", 0)),
                    "H": _safe_int(game.hits.get("away", 0)),
                    "E": _safe_int(game.errors.get("away", 0)),
                    "B": _safe_int(walk_totals.get(away_team, 0)),
                },
                "home": {
                    "R": _safe_int(game.score.get("home", 0)),
                    "H": _safe_int(game.hits.get("home", 0)),
                    "E": _safe_int(game.errors.get("home", 0)),
                    "B": _safe_int(walk_totals.get(home_team, 0)),
                },
            },
        },
        "manager_actions": {
            "can_force_bunt": offense.team == USER_TEAM,
            "bench_for_ph": bench_for_user_offense,
            "bench_for_pr": bench_for_user_offense,
            "pr_base_choices": pr_base_choices,
            "eligible_manual_pitchers": eligible_manual_roles or [],
        },
    }
    return payload


def build_season_summary_payload(state) -> dict:
    standings_row = state.standings[state.standings["팀"] == USER_TEAM]
    rank_text = "-" if standings_row.empty else f"{int(standings_row.iloc[0]['순위'])}위"

    latest = state.latest_game_result
    latest_text = "-"
    latest_payload = None
    if latest is not None:
        latest_text = f"{latest['Away']} {latest['Away_R']} : {latest['Home_R']} {latest['Home']}"
        latest_payload = {
            "date": latest.get("날짜"),
            "away": latest.get("Away"),
            "home": latest.get("Home"),
            "away_r": _safe_int(latest.get("Away_R", 0)),
            "home_r": _safe_int(latest.get("Home_R", 0)),
        }

    return {
        "schema_version": "season_summary_v1",
        "current_date": state.data.all_dates[state.current_date_idx],
        "hanwha_rank_text": rank_text,
        "completed_game_count": len(state.game_results),
        "latest_result_text": latest_text,
        "latest_result": latest_payload,
        "selected_hanwha_game_idx": _safe_int(state.selected_hanwha_game_idx, 0),
        "has_live_game": state.live_game is not None,
    }


def build_app_payload(state, eligible_manual_roles: Optional[List[str]] = None) -> dict:
    # Serialize a few UI screens so React can render "home hub" navigation
    try:
        today_schedule = state.data.schedule[state.data.schedule["날짜"] == state.data.all_dates[state.current_date_idx]].reset_index(drop=True)
        today_schedule_rows = today_schedule.to_dict("records")
    except Exception:
        today_schedule_rows = []

    try:
        hanwha_games = state.data.schedule[
            (state.data.schedule["날짜"] == state.data.all_dates[state.current_date_idx])
            & ((state.data.schedule["Away"] == USER_TEAM) | (state.data.schedule["Home"] == USER_TEAM))
        ].reset_index(drop=True)
        hanwha_games_rows = hanwha_games.to_dict("records")
    except Exception:
        hanwha_games_rows = []

    starters = []
    bench = []
    schedule_detail = {}
    projected_hanwha_starter_role = None
    try:
        starters = sorted(state.team_hitters.get(USER_TEAM, {}).get("starters", []), key=lambda x: x.get("order", 0))
        bench = list(state.team_hitters.get(USER_TEAM, {}).get("bench", []))

        # 오늘 일정 상세: 한화 vs 상대 상세 정보
        if len(hanwha_games_rows) > 0:
            selected_idx = _safe_int(getattr(state, "selected_hanwha_game_idx", 0), 0)
            selected_idx = min(max(selected_idx, 0), len(hanwha_games_rows) - 1)
            selected_game = hanwha_games_rows[selected_idx]

            away_team = str(selected_game.get("Away", ""))
            home_team = str(selected_game.get("Home", ""))
            opponent_team = home_team if away_team == USER_TEAM else away_team

            opponent_lineup = sorted(
                state.team_hitters.get(opponent_team, {}).get("starters", []),
                key=lambda x: x.get("order", 0),
            )

            from .config import STARTER_ROLES

            def _pick_projected_starter_role(team: str):
                staff = state.team_pitchers.get(team, {})
                if not staff:
                    return None
                games = _safe_int(getattr(state, "team_games_played", {}).get(team, 0), 0)
                preferred = STARTER_ROLES[games % 5]
                stamina_map = getattr(state, "starter_stamina", {}).get(team, {})

                if preferred in staff and _safe_int(stamina_map.get(preferred, 100), 100) >= 100:
                    return preferred
                for role in STARTER_ROLES:
                    if role in staff and _safe_int(stamina_map.get(role, 100), 100) >= 100:
                        return role
                if preferred in staff:
                    return preferred
                for role in STARTER_ROLES:
                    if role in staff:
                        return role
                return next(iter(staff.keys())) if staff else None

            projected_hanwha_starter_role = _pick_projected_starter_role(USER_TEAM)
            projected_opp_starter_role = _pick_projected_starter_role(opponent_team)

            hanwha_starter = state.team_pitchers.get(USER_TEAM, {}).get(projected_hanwha_starter_role or "", {})
            opp_starter = state.team_pitchers.get(opponent_team, {}).get(projected_opp_starter_role or "", {})

            hanwha_stamina = _safe_int(
                getattr(state, "starter_stamina", {}).get(USER_TEAM, {}).get(projected_hanwha_starter_role or "", 100),
                100,
            )
            opp_stamina = _safe_int(
                getattr(state, "starter_stamina", {}).get(opponent_team, {}).get(projected_opp_starter_role or "", 100),
                100,
            )

            schedule_detail = {
                "selected_game": {
                    "date": str(selected_game.get("날짜", "")),
                    "away": away_team,
                    "home": home_team,
                    "opponent": opponent_team,
                    "hanwha_is_home": home_team == USER_TEAM,
                },
                "hanwha_lineup": [serialize_player_brief(p) for p in starters],
                "opponent_lineup": [serialize_player_brief(p) for p in opponent_lineup],
                "hanwha_starter": {
                    "name": hanwha_starter.get("name", "정보 없음"),
                    "role": projected_hanwha_starter_role or "선발",
                    "era": _safe_float(hanwha_starter.get("era", 0.0)),
                    "whip": _safe_float(hanwha_starter.get("whip", 0.0)),
                    "stamina": hanwha_stamina,
                },
                "opponent_starter": {
                    "name": opp_starter.get("name", "정보 없음"),
                    "role": projected_opp_starter_role or "선발",
                    "era": _safe_float(opp_starter.get("era", 0.0)),
                    "whip": _safe_float(opp_starter.get("whip", 0.0)),
                    "stamina": opp_stamina,
                },
            }
    except Exception:
        starters = []
        bench = []
        schedule_detail = {}
        projected_hanwha_starter_role = None

    # 투수 정보 추가
    starting_pitchers = []
    bullpen_pitchers = []
    try:
        from .config import STARTER_ROLES, CHASE_ROLES, SETUP_ROLES, CLOSER_ROLE
        pitchers_dict = state.team_pitchers.get(USER_TEAM, {})
        
        # 선발 투수 (1~5번)
        for role in STARTER_ROLES:
            pitcher = pitchers_dict.get(role)
            if pitcher:
                starting_pitchers.append({
                    "name": pitcher.get("name", ""),
                    "role": role,
                    "era": _safe_float(pitcher.get("era", 0.0)),
                    "whip": _safe_float(pitcher.get("whip", 0.0)),
                    "k_rate": _safe_float(pitcher.get("k_rate", 0.0)),
                })
        
        # 불펜 투수 (추격조, 셋업맨, 마무리)
        all_bullpen_roles = CHASE_ROLES + SETUP_ROLES + [CLOSER_ROLE]
        for role in all_bullpen_roles:
            pitcher = pitchers_dict.get(role)
            if pitcher:
                bullpen_pitchers.append({
                    "name": pitcher.get("name", ""),
                    "role": role,
                    "era": _safe_float(pitcher.get("era", 0.0)),
                    "whip": _safe_float(pitcher.get("whip", 0.0)),
                    "k_rate": _safe_float(pitcher.get("k_rate", 0.0)),
                })
    except Exception as e:
        starting_pitchers = []
        bullpen_pitchers = []

    trade_markets: Dict[str, List[dict]] = {}
    try:
        for team in state.team_hitters.keys():
            if team == USER_TEAM:
                continue
            roster = state.team_hitters.get(team, {"starters": [], "bench": []})
            players = roster.get("starters", []) + roster.get("bench", [])
            trade_markets[team] = [
                {
                    "team": p.get("team", team),
                    "name": p.get("name", ""),
                    "pos": p.get("pos", ""),
                    "ops": _safe_float(p.get("ops", 0.0)),
                    "wraa": _safe_float(p.get("wraa", 0.0)),
                    "foreign": bool(p.get("foreign", False)),
                }
                for p in players
                if not bool(p.get("foreign", False))
            ]
    except Exception:
        trade_markets = {}

    hanwha_offer_pool = []
    try:
        hanwha_offer_pool = [
            {
                "name": p.get("name", ""),
                "pos": p.get("pos", ""),
                "ops": _safe_float(p.get("ops", 0.0)),
                "wraa": _safe_float(p.get("wraa", 0.0)),
            }
            for p in bench
            if not bool(p.get("foreign", False))
        ]
    except Exception:
        hanwha_offer_pool = []

    standings_rows = []
    batter_leaders_rows = []
    pitcher_leaders_rows = []
    try:
        standings_df = state.standings.copy() if hasattr(state, "standings") else None
        if standings_df is not None:
            # 승률 컬럼 포매팅
            if '승률' in standings_df.columns:
                standings_df['승률'] = standings_df['승률'].apply(lambda x: f"{float(x):.3f}" if pd.notna(x) else "-")
            standings_rows = standings_df.to_dict("records")
        else:
            standings_rows = []
    except Exception:
        standings_rows = []
    
    # 타자 리더보드: OPS 순 TOP20
    try:
        if hasattr(state, "batter_leaders") and not state.batter_leaders.empty:
            df = state.batter_leaders.copy()
            # OPS 순으로 정렬하여 TOP20 추출
            if "OPS" in df.columns:
                df_sorted = df.nlargest(20, "OPS").reset_index(drop=True)
                # 순위, 소숫점 포매팅 추가
                rows = []
                for idx, row in df_sorted.iterrows():
                    formatted_row = dict(row)
                    formatted_row["순위"] = idx + 1
                    # 소숫점 3자리 포매팅
                    if "타율" in formatted_row:
                        formatted_row["타율"] = f"{_safe_float(formatted_row['타율']):.3f}"
                    if "출루율" in formatted_row:
                        formatted_row["출루율"] = f"{_safe_float(formatted_row['출루율']):.3f}"
                    if "장타율" in formatted_row:
                        formatted_row["장타율"] = f"{_safe_float(formatted_row['장타율']):.3f}"
                    if "OPS" in formatted_row:
                        formatted_row["OPS"] = f"{_safe_float(formatted_row['OPS']):.3f}"
                    rows.append(formatted_row)
                batter_leaders_rows = rows
            else:
                batter_leaders_rows = []
        else:
            batter_leaders_rows = []
    except Exception:
        batter_leaders_rows = []
    
    # 주요 기록별 리더보드 (타자)
    batter_highlights = {}
    try:
        if hasattr(state, "batter_leaders") and not state.batter_leaders.empty:
            df = state.batter_leaders.copy()
            # 홈런 TOP3
            if "홈런" in df.columns:
                batter_highlights["홈런"] = df.nlargest(3, "홈런")[["이름", "팀", "홈런"]].to_dict("records")
            # 안타 TOP3
            if "안타" in df.columns:
                batter_highlights["안타"] = df.nlargest(3, "안타")[["이름", "팀", "안타"]].to_dict("records")
            # 타율 TOP3
            if "타율" in df.columns:
                batter_highlights["타율"] = df.nlargest(3, "타율")[["이름", "팀", "타율"]].to_dict("records")
            # 출루율 TOP3
            if "출루율" in df.columns:
                batter_highlights["출루율"] = df.nlargest(3, "출루율")[["이름", "팀", "출루율"]].to_dict("records")
            # OPS TOP3
            if "OPS" in df.columns:
                batter_highlights["OPS"] = df.nlargest(3, "OPS")[["이름", "팀", "OPS"]].to_dict("records")
    except Exception:
        batter_highlights = {}
    
    # 투수 리더보드: 규정이닝 필터 + ERA 순 TOP20
    try:
        if hasattr(state, "pitcher_leaders") and not state.pitcher_leaders.empty:
            df = state.pitcher_leaders.copy()
            
            # 규정이닝 적용 (경기수 * 1)
            if "경기" in df.columns and "이닝" in df.columns:
                games_played = _safe_int(df["경기"].iloc[0]) if len(df) > 0 else 0
                min_innings = games_played * 1.0 if games_played > 0 else 1.0
                df = df[_safe_float(df["이닝"]) >= min_innings]
            
            # ERA 순으로 정렬하여 TOP20 추출
            if "방어율" in df.columns:
                df_sorted = df.nsmallest(20, "방어율").reset_index(drop=True)
                # 순위, 소숫점 포매팅, 이닝 변환 추가
                rows = []
                for idx, row in df_sorted.iterrows():
                    formatted_row = dict(row)
                    formatted_row["순위"] = idx + 1
                    # 방어율, WHIP: 소숫점 2자리
                    if "방어율" in formatted_row:
                        formatted_row["방어율"] = f"{_safe_float(formatted_row['방어율']):.2f}"
                    if "WHIP" in formatted_row:
                        formatted_row["WHIP"] = f"{_safe_float(formatted_row['WHIP']):.2f}"
                    # 이닝: 분수 표기 (180.6777777 → "180 2/3")
                    if "이닝" in formatted_row:
                        formatted_row["이닝"] = _format_innings(_safe_float(formatted_row['이닝']))
                    rows.append(formatted_row)
                pitcher_leaders_rows = rows
            else:
                pitcher_leaders_rows = []
        else:
            pitcher_leaders_rows = []
    except Exception:
        pitcher_leaders_rows = []
    
    # 투수 주요 기록별 리더보드
    pitcher_highlights = {}
    try:
        if hasattr(state, "pitcher_leaders") and not state.pitcher_leaders.empty:
            df = state.pitcher_leaders.copy()
            
            # 규정이닝 필터 적용
            if "경기" in df.columns and "이닝" in df.columns:
                games_played = _safe_int(df["경기"].iloc[0]) if len(df) > 0 else 0
                min_innings = games_played * 1.0 if games_played > 0 else 1.0
                df = df[_safe_float(df["이닝"]) >= min_innings]
            
            # ERA TOP3 (낮을수록 좋음)
            if "방어율" in df.columns:
                pitcher_highlights["ERA"] = df.nsmallest(3, "방어율")[["이름", "팀", "방어율"]].to_dict("records")
            # WHIP TOP3
            if "WHIP" in df.columns:
                pitcher_highlights["WHIP"] = df.nsmallest(3, "WHIP")[["이름", "팀", "WHIP"]].to_dict("records")
            # 이닝 TOP3
            if "이닝" in df.columns:
                pitcher_highlights["이닝"] = df.nlargest(3, "이닝")[["이름", "팀", "이닝"]].to_dict("records")
            # 삼진 TOP3
            if "탈삼진" in df.columns:
                pitcher_highlights["삼진"] = df.nlargest(3, "탈삼진")[["이름", "팀", "탈삼진"]].to_dict("records")
            # 볼넷 TOP3
            if "볼넷" in df.columns:
                pitcher_highlights["볼넷"] = df.nlargest(3, "볼넷")[["이름", "팀", "볼넷"]].to_dict("records")
    except Exception:
        pitcher_highlights = {}

    return {
        "schema_version": "app_payload_v1",
        "season_summary": build_season_summary_payload(state),
        "live_game": build_live_game_payload(state, eligible_manual_roles=eligible_manual_roles),
        "screens": {
            "last_error": getattr(state, "_last_error", None),
            "today_schedule": {
                "date": state.data.all_dates[state.current_date_idx],
                "rows": today_schedule_rows,
            },
            "hanwha_games": {
                "selected_idx": _safe_int(getattr(state, "selected_hanwha_game_idx", 0), 0),
                "rows": hanwha_games_rows,
                "detail": schedule_detail,
            },
            "hanwha_lineup": {
                "starters": [serialize_player_brief(p) for p in starters],
                "bench": [serialize_player_brief(p) for p in bench],
                "starting_pitchers": [
                    {
                        "name": p.get("name", ""),
                        "role": p.get("role", "1번 선발") if isinstance(p, dict) else "선발",
                        "era": _safe_float(p.get("era", 0.0) if isinstance(p, dict) else 0.0),
                        "whip": _safe_float(p.get("whip", 0.0) if isinstance(p, dict) else 0.0),
                        "k_rate": _safe_float(p.get("k_rate", 0.0) if isinstance(p, dict) else 0.0),
                        "stamina": _safe_int(
                            getattr(state, "starter_stamina", {}).get(USER_TEAM, {}).get(
                                p.get("role", "") if isinstance(p, dict) else "",
                                100,
                            ),
                            100,
                        ),
                        "next_game_starter": bool(
                            projected_hanwha_starter_role and (p.get("role", "") == projected_hanwha_starter_role)
                            if isinstance(p, dict)
                            else False
                        ),
                    }
                    for p in starting_pitchers
                ],
                "bullpen_pitchers": [
                    {
                        "name": p.get("name", ""),
                        "role": p.get("role", "불펜") if isinstance(p, dict) else "불펜",
                        "era": _safe_float(p.get("era", 0.0) if isinstance(p, dict) else 0.0),
                        "whip": _safe_float(p.get("whip", 0.0) if isinstance(p, dict) else 0.0),
                        "k_rate": _safe_float(p.get("k_rate", 0.0) if isinstance(p, dict) else 0.0),
                    }
                    for p in bullpen_pitchers
                ],
            },
            "trade": {
                "opponents": sorted([t for t in state.team_hitters.keys() if t != USER_TEAM]),
                "markets": trade_markets,
                "offer_pool": hanwha_offer_pool,
                "last_result": getattr(state, "_last_trade_result", None),
                "monthly_limit": 1,
                "monthly_used": _safe_int(getattr(state, "trade_attempts_monthly", {}).get(state.month_key(), 0), 0)
                if hasattr(state, "month_key")
                else 0,
                "month": state.month_key() if hasattr(state, "month_key") else None,
            },
            "standings": standings_rows,
            "leaders": {
                "batters": batter_leaders_rows,
                "pitchers": pitcher_leaders_rows,
                "batter_highlights": batter_highlights,
                "pitcher_highlights": pitcher_highlights,
            },
        },
    }