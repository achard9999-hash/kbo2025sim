from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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
    try:
        starters = sorted(state.team_hitters.get(USER_TEAM, {}).get("starters", []), key=lambda x: x.get("order", 0))
        bench = list(state.team_hitters.get(USER_TEAM, {}).get("bench", []))
    except Exception:
        starters = []
        bench = []

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
        standings_rows = state.standings.to_dict("records") if hasattr(state, "standings") else []
    except Exception:
        standings_rows = []
    try:
        batter_leaders_rows = state.batter_leaders.head(30).to_dict("records") if hasattr(state, "batter_leaders") else []
    except Exception:
        batter_leaders_rows = []
    try:
        pitcher_leaders_rows = state.pitcher_leaders.head(30).to_dict("records") if hasattr(state, "pitcher_leaders") else []
    except Exception:
        pitcher_leaders_rows = []

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
            },
            "hanwha_lineup": {
                "starters": [serialize_player_brief(p) for p in starters],
                "bench": [serialize_player_brief(p) for p in bench],
            },
            "trade": {
                "opponents": sorted([t for t in state.team_hitters.keys() if t != USER_TEAM]),
                "markets": trade_markets,
                "offer_pool": hanwha_offer_pool,
                "last_result": getattr(state, "_last_trade_result", None),
            },
            "standings": standings_rows,
            "leaders": {
                "batters": batter_leaders_rows,
                "pitchers": pitcher_leaders_rows,
            },
        },
    }