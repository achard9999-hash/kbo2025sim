from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import copy
import hashlib
import pandas as pd

from .config import (
    USER_TEAM,
    TEAMS,
    STARTER_ROLES,
    CHASE_ROLES,
    SETUP_ROLES,
    CLOSER_ROLE,
    MANUAL_CHASE_CHANGES_PER_GAME,
    MANUAL_SETUP_CHANGES_PER_MONTH,
)
from .data import load_csvs, deep_copy_team_hitters, deep_copy_team_pitchers, get_trade_candidates, LoadedData
from .game import GameSimulator


@dataclass
class SeasonState:
    data: LoadedData
    current_date_idx: int = 0
    selected_hanwha_game_idx: int = 0
    completed_game_keys: set = field(default_factory=set)
    game_results: List[dict] = field(default_factory=list)
    standings: pd.DataFrame = field(default_factory=pd.DataFrame)
    batter_leaders: pd.DataFrame = field(default_factory=pd.DataFrame)
    pitcher_leaders: pd.DataFrame = field(default_factory=pd.DataFrame)
    latest_game_result: Optional[dict] = None

    team_hitters: Dict[str, Dict[str, List[dict]]] = field(default_factory=dict)
    team_pitchers: Dict[str, Dict[str, dict]] = field(default_factory=dict)
    team_games_played: Dict[str, int] = field(default_factory=dict)

    live_game: Optional[GameSimulator] = None
    live_game_meta: Optional[dict] = None

    manual_setup_monthly_usage: Dict[Tuple[str, str], int] = field(default_factory=dict)

    def month_key(self) -> str:
        return current_date(self)[:7]


def initialize_season_state(data_dir=".") -> SeasonState:
    data = load_csvs(data_dir=data_dir)
    state = SeasonState(
        data=data,
        team_hitters=deep_copy_team_hitters(data.team_hitters),
        team_pitchers=deep_copy_team_pitchers(data.team_pitchers),
        team_games_played={team: 0 for team in TEAMS},
    )
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


def current_hanwha_game_row(state: SeasonState) -> Optional[pd.Series]:
    hg = hanwha_games_for_current_date(state)
    if hg.empty:
        return None
    idx = min(state.selected_hanwha_game_idx, len(hg) - 1)
    return hg.iloc[idx]


def selected_game_started(state: SeasonState) -> bool:
    if state.live_game_meta is None:
        return False
    row = current_hanwha_game_row(state)
    if row is None:
        return False
    return state.live_game_meta["key"] == make_game_key(row["날짜"], row["Away"], row["Home"])


def get_rotation_role(state: SeasonState, team: str) -> str:
    staff = state.team_pitchers[team]
    idx = state.team_games_played[team] % 5
    preferred = STARTER_ROLES[idx]
    if preferred in staff:
        return preferred
    for role in STARTER_ROLES:
        if role in staff:
            return role
    return next(iter(staff.keys()))


def start_selected_game(state: SeasonState) -> bool:
    row = current_hanwha_game_row(state)
    if row is None:
        return False
    date, away, home = row["날짜"], row["Away"], row["Home"]
    key = make_game_key(date, away, home)
    if state.live_game is not None and state.live_game_meta and state.live_game_meta.get("key") == key:
        return True
    if key in state.completed_game_keys:
        return False
    state.live_game = GameSimulator(
        away_team=away,
        home_team=home,
        away_roster=state.team_hitters[away],
        home_roster=state.team_hitters[home],
        away_staff=state.team_pitchers[away],
        home_staff=state.team_pitchers[home],
        away_starter_role=get_rotation_role(state, away),
        home_starter_role=get_rotation_role(state, home),
        seed=make_seed(date, away, home),
    )
    state.live_game_meta = {"date": date, "away": away, "home": home, "key": key}
    return True


def simulate_live_pa(state: SeasonState):
    if state.live_game is None:
        start_selected_game(state)
    if state.live_game is None:
        return
    state.live_game.play_plate_appearance()
    if state.live_game.finished:
        _commit_live_game(state)


def simulate_live_half(state: SeasonState):
    if state.live_game is None:
        start_selected_game(state)
    if state.live_game is None:
        return
    state.live_game.play_half_inning()
    if state.live_game.finished:
        _commit_live_game(state)


def simulate_selected_game(state: SeasonState):
    if state.live_game is None:
        start_selected_game(state)
    if state.live_game is None:
        return
    state.live_game.play_to_end()
    _commit_live_game(state)
    _simulate_other_games_today(state)
    _advance_date_if_done(state)
    _refresh_aggregates(state)


def simulate_next_day(state: SeasonState):
    day = current_day_schedule(state)
    hanwha_row = current_hanwha_game_row(state)
    for _, g in day.iterrows():
        key = make_game_key(g["날짜"], g["Away"], g["Home"])
        if key in state.completed_game_keys:
            continue
        if hanwha_row is not None and g["Away"] == hanwha_row["Away"] and g["Home"] == hanwha_row["Home"]:
            temp = GameSimulator(
                away_team=g["Away"], home_team=g["Home"],
                away_roster=state.team_hitters[g["Away"]], home_roster=state.team_hitters[g["Home"]],
                away_staff=state.team_pitchers[g["Away"]], home_staff=state.team_pitchers[g["Home"]],
                away_starter_role=get_rotation_role(state, g["Away"]),
                home_starter_role=get_rotation_role(state, g["Home"]),
                seed=make_seed(g["날짜"], g["Away"], g["Home"]),
            )
            temp.play_to_end()
            _commit_game_result(state, g["날짜"], g["Away"], g["Home"], temp.result())
        else:
            temp = GameSimulator(
                away_team=g["Away"], home_team=g["Home"],
                away_roster=state.team_hitters[g["Away"]], home_roster=state.team_hitters[g["Home"]],
                away_staff=state.team_pitchers[g["Away"]], home_staff=state.team_pitchers[g["Home"]],
                away_starter_role=get_rotation_role(state, g["Away"]),
                home_starter_role=get_rotation_role(state, g["Home"]),
                seed=make_seed(g["날짜"], g["Away"], g["Home"]),
            )
            temp.play_to_end()
            _commit_game_result(state, g["날짜"], g["Away"], g["Home"], temp.result())
    state.live_game = None
    state.live_game_meta = None
    _advance_date_if_done(state)
    _refresh_aggregates(state)


def _simulate_other_games_today(state: SeasonState):
    day = current_day_schedule(state)
    for _, g in day.iterrows():
        key = make_game_key(g["날짜"], g["Away"], g["Home"])
        if key in state.completed_game_keys:
            continue
        temp = GameSimulator(
            away_team=g["Away"], home_team=g["Home"],
            away_roster=state.team_hitters[g["Away"]], home_roster=state.team_hitters[g["Home"]],
            away_staff=state.team_pitchers[g["Away"]], home_staff=state.team_pitchers[g["Home"]],
            away_starter_role=get_rotation_role(state, g["Away"]),
            home_starter_role=get_rotation_role(state, g["Home"]),
            seed=make_seed(g["날짜"], g["Away"], g["Home"]),
        )
        temp.play_to_end()
        _commit_game_result(state, g["날짜"], g["Away"], g["Home"], temp.result())


def _commit_live_game(state: SeasonState):
    if state.live_game is None or state.live_game_meta is None:
        return
    result = state.live_game.result()
    _commit_game_result(state, state.live_game_meta["date"], state.live_game_meta["away"], state.live_game_meta["home"], result)
    state.live_game = None
    state.live_game_meta = None
    _refresh_aggregates(state)


def _commit_game_result(state: SeasonState, date: str, away: str, home: str, result):
    key = make_game_key(date, away, home)
    if key in state.completed_game_keys:
        return

    state.completed_game_keys.add(key)
    state.team_games_played[away] += 1
    state.team_games_played[home] += 1

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
        "line_away": result.line_score_away,
        "line_home": result.line_score_home,
        "feed": result.feed,
        "batter_box": result.batter_box,
        "pitcher_box": result.pitcher_box,
        "ended_in_tie": result.ended_in_tie,
    }
    state.game_results.append(game_record)
    state.latest_game_result = game_record


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


def build_standings(game_results: List[dict]) -> pd.DataFrame:
    rows = {team: {"팀": team, "경기": 0, "승": 0, "패": 0, "무": 0, "득점": 0, "실점": 0} for team in TEAMS}
    for g in game_results:
        away, home = g["Away"], g["Home"]
        ar, hr = int(g["Away_R"]), int(g["Home_R"])
        for team, r, a in [(away, ar, hr), (home, hr, ar)]:
            rows[team]["경기"] += 1
            rows[team]["득점"] += r
            rows[team]["실점"] += a
        if ar > hr:
            rows[away]["승"] += 1
            rows[home]["패"] += 1
        elif hr > ar:
            rows[home]["승"] += 1
            rows[away]["패"] += 1
        else:
            rows[away]["무"] += 1
            rows[home]["무"] += 1
    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    df["승률"] = df.apply(lambda r: r["승"] / max(1, r["승"] + r["패"]), axis=1)
    df["득실차"] = df["득점"] - df["실점"]
    df = df.sort_values(["승률", "득실차", "득점"], ascending=[False, False, False]).reset_index(drop=True)
    df.insert(0, "순위", range(1, len(df) + 1))
    return df


def build_batter_leaders(game_results: List[dict]) -> pd.DataFrame:
    rows: Dict[tuple, dict] = {}
    for g in game_results:
        for event in g["batter_box"]:
            key = (event["team"], event["name"])
            if key not in rows:
                rows[key] = {
                    "팀": event["team"], "선수명": event["name"], "타석": 0, "타수": 0, "안타": 0, "홈런": 0,
                    "1루타": 0, "2루타": 0, "3루타": 0, "볼넷": 0, "희생번트성공": 0, "희생플라이성공": 0,
                }
            rows[key]["타석"] += event.get("PA", 0)
            rows[key]["타수"] += event.get("AB", 0)
            rows[key]["안타"] += event.get("H", 0)
            rows[key]["홈런"] += event.get("HR", 0)
            rows[key]["1루타"] += event.get("1B", 0)
            rows[key]["2루타"] += event.get("2B", 0)
            rows[key]["3루타"] += event.get("3B", 0)
            rows[key]["볼넷"] += event.get("BB", 0)
            rows[key]["희생번트성공"] += event.get("SACB", 0)
            rows[key]["희생플라이성공"] += event.get("SACF", 0)

    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    df["타수"] = df["타석"] - df["볼넷"] - df["희생번트성공"] - df["희생플라이성공"]
    df["타수"] = df["타수"].clip(lower=0)
    df["타율"] = df["안타"] / df["타수"].clip(lower=1)
    df["출루율"] = (df["안타"] + df["볼넷"]) / df["타석"].clip(lower=1)
    df["장타율"] = (df["1루타"] + 2 * df["2루타"] + 3 * df["3루타"] + 4 * df["홈런"]) / df["타수"].clip(lower=1)
    df["OPS"] = df["출루율"] + df["장타율"]
    return df[["팀", "선수명", "타석", "타수", "안타", "홈런", "타율", "출루율", "장타율", "OPS"]].sort_values(
        ["OPS", "홈런", "안타"], ascending=[False, False, False]
    ).reset_index(drop=True)


def build_pitcher_leaders(game_results: List[dict]) -> pd.DataFrame:
    rows: Dict[tuple, dict] = {}
    for g in game_results:
        for pb in g["pitcher_box"]:
            key = (pb["team"], pb["name"])
            if key not in rows:
                rows[key] = {
                    "팀": pb["team"], "선수명": pb["name"], "아웃": 0, "볼넷": 0, "삼진": 0, "실점": 0, "피안타": 0,
                }
            rows[key]["아웃"] += pb["outs"]
            rows[key]["볼넷"] += pb["walks"]
            rows[key]["삼진"] += pb["strikeouts"]
            rows[key]["실점"] += pb["runs"]
            rows[key]["피안타"] += pb["hits"]
    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    df["이닝"] = df["아웃"] / 3.0
    df["ERA"] = df["실점"] * 9 / df["이닝"].clip(lower=1/3)
    df["WHIP"] = (df["피안타"] + df["볼넷"]) / df["이닝"].clip(lower=1/3)
    return df[["팀", "선수명", "이닝", "볼넷", "삼진", "ERA", "WHIP"]].sort_values(
        ["ERA", "WHIP", "이닝"], ascending=[True, True, False]
    ).reset_index(drop=True)


def _refresh_aggregates(state: SeasonState):
    state.standings = build_standings(state.game_results)
    state.batter_leaders = build_batter_leaders(state.game_results)
    state.pitcher_leaders = build_pitcher_leaders(state.game_results)


def get_trade_market(state: SeasonState, opponent_team: str) -> List[dict]:
    return get_trade_candidates(state.data, opponent_team)


def execute_trade(state: SeasonState, opponent_team: str, target_name: str, offered_names: List[str]) -> tuple[bool, str]:
    if opponent_team == USER_TEAM:
        return False, "상대 팀을 선택하세요."
    opponent = state.team_hitters[opponent_team]
    hanwha = state.team_hitters[USER_TEAM]

    target = None
    target_bucket = None
    for bucket in ("starters", "bench"):
        for p in opponent[bucket]:
            if p["name"] == target_name and not p.get("foreign", False):
                target = p
                target_bucket = bucket
                break
        if target:
            break
    if target is None:
        return False, "트레이드 대상 선수를 찾지 못했습니다."

    offers = []
    for name in offered_names:
        found = None
        bucket_name = None
        for bucket in ("starters", "bench"):
            for p in hanwha[bucket]:
                if p["name"] == name and not p.get("foreign", False):
                    found = p
                    bucket_name = bucket
                    break
            if found:
                break
        if found:
            offers.append((bucket_name, found))
    if not offers:
        return False, "제안할 한화 선수를 선택하세요."

    target_wraa = max(0.0, target.get("wraa", 0.0))
    offer_wraa = sum(max(0.0, p.get("wraa", 0.0)) for _, p in offers)
    diff = abs(offer_wraa - target_wraa)
    chance = max(0.10, min(0.90, 0.75 - diff / 50.0))
    seed = int(hashlib.md5((current_date(state) + target_name + "".join(sorted(offered_names))).encode()).hexdigest()[:8], 16)
    import random
    rng = random.Random(seed)
    success = rng.random() < chance

    if not success:
        return False, f"트레이드 실패 (성공확률 {chance:.1%})"

    for bucket_name, p in offers:
        state.team_hitters[USER_TEAM][bucket_name] = [x for x in state.team_hitters[USER_TEAM][bucket_name] if x["name"] != p["name"]]
        p_copy = copy.deepcopy(p)
        p_copy["order"] = 0
        state.team_hitters[opponent_team]["bench"].append(p_copy)

    state.team_hitters[opponent_team][target_bucket] = [x for x in state.team_hitters[opponent_team][target_bucket] if x["name"] != target["name"]]
    target_copy = copy.deepcopy(target)
    target_copy["order"] = 0
    state.team_hitters[USER_TEAM]["bench"].append(target_copy)
    _normalize_hanwha_lineup(state)
    return True, f"트레이드 성공: {target_name} 영입 (성공확률 {chance:.1%})"


def _normalize_hanwha_lineup(state: SeasonState):
    starters = state.team_hitters[USER_TEAM]["starters"]
    starters = sorted(starters, key=lambda x: x["order"])[:9]
    for idx, p in enumerate(starters, start=1):
        p["order"] = idx
    state.team_hitters[USER_TEAM]["starters"] = starters


def reorder_hanwha_lineup(state: SeasonState, player_name: str, direction: int):
    starters = state.team_hitters[USER_TEAM]["starters"]
    starters = sorted(starters, key=lambda x: x["order"])
    idx = next((i for i, p in enumerate(starters) if p["name"] == player_name), None)
    if idx is None:
        return
    nxt = idx + direction
    if nxt < 0 or nxt >= len(starters):
        return
    starters[idx]["order"], starters[nxt]["order"] = starters[nxt]["order"], starters[idx]["order"]
    state.team_hitters[USER_TEAM]["starters"] = sorted(starters, key=lambda x: x["order"])


def bench_to_lineup(state: SeasonState, bench_name: str):
    bench = state.team_hitters[USER_TEAM]["bench"]
    starters = state.team_hitters[USER_TEAM]["starters"]
    selected = next((b for b in bench if b["name"] == bench_name), None)
    if selected is None or not starters:
        return
    weakest = min(starters, key=lambda x: x.get("wraa", 0.0))
    weakest_order = weakest["order"]
    bench.remove(selected)
    starters.remove(weakest)
    weakest["order"] = 0
    selected["order"] = weakest_order
    starters.append(selected)
    bench.append(weakest)
    starters = sorted(starters, key=lambda x: x["order"])
    for idx, p in enumerate(starters, start=1):
        p["order"] = idx
    state.team_hitters[USER_TEAM]["starters"] = starters


def live_force_bunt(state: SeasonState):
    if state.live_game:
        state.live_game.force_bunt_next(USER_TEAM)


def live_apply_pinch_hitter(state: SeasonState, bench_name: str) -> tuple[bool, str]:
    if state.live_game is None:
        return False, "진행 중인 한화 경기가 없습니다."
    ok = state.live_game.apply_pinch_hitter(USER_TEAM, bench_name)
    return ok, "대타 적용" if ok else "대타 적용 실패"


def live_apply_pinch_runner(state: SeasonState, base_number: int, bench_name: str) -> tuple[bool, str]:
    if state.live_game is None:
        return False, "진행 중인 한화 경기가 없습니다."
    ok = state.live_game.apply_pinch_runner(USER_TEAM, base_number, bench_name)
    return ok, "대주자 적용" if ok else "대주자 적용 실패"


def get_eligible_manual_pitchers(state: SeasonState) -> List[str]:
    if state.live_game is None:
        return []
    game = state.live_game
    defense = game.defense()
    if defense.team != USER_TEAM:
        return []
    month = state.month_key()
    eligible = []
    for role in CHASE_ROLES:
        if role in defense.staff and defense.current_pitcher_role != role and defense.manual_chase_changes_used < MANUAL_CHASE_CHANGES_PER_GAME:
            eligible.append(role)
    for role in SETUP_ROLES:
        used = state.manual_setup_monthly_usage.get((month, role), 0)
        if role in defense.staff and defense.current_pitcher_role != role and used < MANUAL_SETUP_CHANGES_PER_MONTH:
            eligible.append(role)
    return eligible


def live_apply_manual_pitcher(state: SeasonState, role: str) -> tuple[bool, str]:
    if state.live_game is None:
        return False, "진행 중인 한화 경기가 없습니다."
    game = state.live_game
    defense = game.defense()
    if defense.team != USER_TEAM:
        return False, "지금은 한화 수비 이닝이 아닙니다."
    if role == CLOSER_ROLE or role in STARTER_ROLES:
        return False, "선발/마무리는 직접 교체 불가입니다."
    if role in CHASE_ROLES:
        if defense.manual_chase_changes_used >= MANUAL_CHASE_CHANGES_PER_GAME:
            return False, "이번 경기 추격조 직접 교체 한도를 초과했습니다."
        defense.manual_chase_changes_used += 1
    if role in SETUP_ROLES:
        month = state.month_key()
        used = state.manual_setup_monthly_usage.get((month, role), 0)
        if used >= MANUAL_SETUP_CHANGES_PER_MONTH:
            return False, f"{role} 월간 직접 교체 한도를 초과했습니다."
        state.manual_setup_monthly_usage[(month, role)] = used + 1
    ok = game.apply_manual_pitcher_change(USER_TEAM, role)
    return ok, "투수 교체 예약" if ok else "투수 교체 실패"
