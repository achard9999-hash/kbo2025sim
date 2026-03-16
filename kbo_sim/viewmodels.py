from __future__ import annotations

from typing import Any, Dict, List, Optional

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


def serialize_player_brief(player: Optional[dict]) -> Optional[dict]:
    if not player:
        return None
    return {
        "name": player.get("name", ""),
        "pos": player.get("pos", ""),
        "order": _safe_int(player.get("order", 0)),
        "avg": _safe_float(player.get("avg", 0.0)),
        "ops": _safe_float(player.get("ops", 0.0)),
        "wraa": _safe_float(player.get("wraa", 0.0)),
        "foreign": bool(player.get("foreign", False)),
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


def serialize_team_state(team_state) -> dict:
    lineup = sorted(team_state.lineup, key=lambda x: x.get("order", 0))
    bench = list(team_state.bench)

    return {
        "team": team_state.team,
        "batting_index": _safe_int(team_state.batting_index, 0),
        "current_pitcher_role": team_state.current_pitcher_role,
        "pending_force_bunt": bool(team_state.pending_force_bunt),
        "pending_manual_pitcher_role": team_state.pending_manual_pitcher_role,
        "manual_chase_changes_used": _safe_int(team_state.manual_chase_changes_used, 0),
        "lineup": [serialize_player_brief(p) for p in lineup],
        "bench": [serialize_player_brief(p) for p in bench],
        "current_pitcher": serialize_pitcher_brief(
            team_state.current_pitcher_role,
            team_state.current_pitcher() if team_state.current_pitcher_role else None,
        ),
    }


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

    bench_for_user_offense = []
    if offense.team == USER_TEAM:
        bench_for_user_offense = [serialize_player_brief(p) for p in offense.bench]

    pr_base_choices = [idx for idx, runner in enumerate(game.bases, start=1) if runner is not None]

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
            "away_team": game.away.team,
            "home_team": game.home.team,
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
            "offense": serialize_team_state(offense),
            "defense": serialize_team_state(defense),
            "current_batter": serialize_player_brief(current_batter),
            "current_pitcher": serialize_pitcher_brief(defense.current_pitcher_role, current_pitcher),
            "offense_is_user_team": offense.team == USER_TEAM,
            "defense_is_user_team": defense.team == USER_TEAM,
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
    return {
        "schema_version": "app_payload_v1",
        "season_summary": build_season_summary_payload(state),
        "live_game": build_live_game_payload(state, eligible_manual_roles=eligible_manual_roles),
    }