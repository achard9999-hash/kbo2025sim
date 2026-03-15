from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import hashlib
import pandas as pd

from .config import TEAMS, USER_TEAM
from .data import LoadedData, load_csvs
from .game import GameSimulator


@dataclass
class SeasonState:
    data: LoadedData
    current_date_idx: int
    selected_hanwha_game_idx: int = 0
    completed_game_keys: set = field(default_factory=set)
    game_results: List[dict] = field(default_factory=list)
    standings: pd.DataFrame = field(default_factory=pd.DataFrame)
    batter_leaders: pd.DataFrame = field(default_factory=pd.DataFrame)
    pitcher_leaders: pd.DataFrame = field(default_factory=pd.DataFrame)
    latest_game_result: Optional[dict] = None


def initialize_season_state(data_dir=".") -> SeasonState:
    data = load_csvs(data_dir=data_dir)
    state = SeasonState(data=data, current_date_idx=0)
    _refresh_aggregates(state)
    return state


def current_date(state: SeasonState) -> str:
    return state.data.all_dates[state.current_date_idx]


def current_day_schedule(state: SeasonState) -> pd.DataFrame:
    d = current_date(state)
    return state.data.schedule[state.data.schedule["날짜"] == d].reset_index(drop=True)


def hanwha_games_for_current_date(state: SeasonState) -> pd.DataFrame:
    day = current_day_schedule(state)
    mask = (day["Away"] == USER_TEAM) | (day["Home"] == USER_TEAM)
    return day[mask].reset_index(drop=True)


def make_game_key(date: str, away: str, home: str) -> str:
    return f"{date}|{away}|{home}"


def make_seed(date: str, away: str, home: str) -> int:
    return int(hashlib.md5(make_game_key(date, away, home).encode()).hexdigest()[:8], 16)


def simulate_selected_game(state: SeasonState):
    day_hanwha = hanwha_games_for_current_date(state)
    if day_hanwha.empty:
        return
    idx = min(state.selected_hanwha_game_idx, len(day_hanwha) - 1)
    row = day_hanwha.iloc[idx]
    date, away, home = row["날짜"], row["Away"], row["Home"]
    _simulate_one_game(state, date, away, home)

    # 같은 날짜의 나머지 경기 자동 진행
    day = current_day_schedule(state)
    for _, g in day.iterrows():
        key = make_game_key(g["날짜"], g["Away"], g["Home"])
        if key not in state.completed_game_keys:
            _simulate_one_game(state, g["날짜"], g["Away"], g["Home"])

    _advance_date_if_done(state)
    _refresh_aggregates(state)


def simulate_next_day(state: SeasonState):
    day = current_day_schedule(state)
    for _, g in day.iterrows():
        key = make_game_key(g["날짜"], g["Away"], g["Home"])
        if key not in state.completed_game_keys:
            _simulate_one_game(state, g["날짜"], g["Away"], g["Home"])
    _advance_date_if_done(state)
    _refresh_aggregates(state)


def _advance_date_if_done(state: SeasonState):
    while state.current_date_idx < len(state.data.all_dates):
        day = current_day_schedule(state)
        keys = {make_game_key(r["날짜"], r["Away"], r["Home"]) for _, r in day.iterrows()}
        if keys.issubset(state.completed_game_keys):
            if state.current_date_idx < len(state.data.all_dates) - 1:
                state.current_date_idx += 1
                state.selected_hanwha_game_idx = 0
            else:
                break
        else:
            break


def _simulate_one_game(state: SeasonState, date: str, away: str, home: str):
    key = make_game_key(date, away, home)
    if key in state.completed_game_keys:
        return

    sim = GameSimulator(
        away_team=away,
        home_team=home,
        away_lineup=state.data.team_lineups[away],
        home_lineup=state.data.team_lineups[home],
        away_staff=state.data.team_pitchers[away],
        home_staff=state.data.team_pitchers[home],
        seed=make_seed(date, away, home),
    )
    result = sim.play_game()

    game_record = {
        "날짜": date,
        "Away": away,
        "Home": home,
        "Away_R": result.away_runs,
        "Home_R": result.home_runs,
        "Away_H": result.away_hits,
        "Home_H": result.home_hits,
        "Away_E": result.away_errors,
        "Home_E": result.home_errors,
        "feed": result.feed,
        "batter_box": result.batter_box,
        "pitcher_box": result.pitcher_box,
    }
    state.game_results.append(game_record)
    state.latest_game_result = game_record
    state.completed_game_keys.add(key)


def _refresh_aggregates(state: SeasonState):
    state.standings = build_standings(state.game_results)
    state.batter_leaders = build_batter_leaders(state.game_results)
    state.pitcher_leaders = build_pitcher_leaders(state.game_results)


def build_standings(game_results: List[dict]) -> pd.DataFrame:
    rows = {team: {"팀": team, "경기": 0, "승": 0, "패": 0, "무": 0, "득점": 0, "실점": 0} for team in TEAMS}
    for g in game_results:
        away, home = g["Away"], g["Home"]
        ar, hr = int(g["Away_R"]), int(g["Home_R"])
        rows[away]["경기"] += 1
        rows[home]["경기"] += 1
        rows[away]["득점"] += ar
        rows[away]["실점"] += hr
        rows[home]["득점"] += hr
        rows[home]["실점"] += ar

        if ar > hr:
            rows[away]["승"] += 1
            rows[home]["패"] += 1
        elif ar < hr:
            rows[home]["승"] += 1
            rows[away]["패"] += 1
        else:
            rows[away]["무"] += 1
            rows[home]["무"] += 1

    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    df["승률"] = df.apply(lambda r: r["승"] / max(1, (r["승"] + r["패"])), axis=1)
    df["득실차"] = df["득점"] - df["실점"]
    df = df.sort_values(["승률", "득실차", "득점"], ascending=[False, False, False]).reset_index(drop=True)
    df.index = df.index + 1
    df.insert(0, "순위", df.index)
    return df


def build_batter_leaders(game_results: List[dict]) -> pd.DataFrame:
    rows: Dict[tuple, dict] = {}
    for g in game_results:
        for event in g["batter_box"]:
            key = (event["team"], event["name"])
            if key not in rows:
                rows[key] = {"팀": event["team"], "선수명": event["name"], "타석": 0, "안타": 0, "홈런": 0, "타점": 0}
            rows[key]["타석"] += 1
            if event["event"] in ("안타", "2루타", "3루타", "홈런"):
                rows[key]["안타"] += 1
            if event["event"] == "홈런":
                rows[key]["홈런"] += 1
            rows[key]["타점"] += int(event.get("runs_batted", 0))

    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    df["타율"] = df["안타"] / df["타석"].clip(lower=1)
    return df.sort_values(["홈런", "타점", "타율"], ascending=[False, False, False]).reset_index(drop=True)


def build_pitcher_leaders(game_results: List[dict]) -> pd.DataFrame:
    rows: Dict[tuple, dict] = {}
    for g in game_results:
        for pb in g["pitcher_box"]:
            key = (pb["team"], pb["name"])
            if key not in rows:
                rows[key] = {"팀": pb["team"], "선수명": pb["name"], "IP": 0.0, "실점": 0}
            rows[key]["IP"] += float(pb["ip"])
            rows[key]["실점"] += int(pb["runs"])

    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    df["RA9"] = df["실점"] * 9 / df["IP"].clip(lower=1/3)
    return df.sort_values(["RA9", "IP"], ascending=[True, False]).reset_index(drop=True)
