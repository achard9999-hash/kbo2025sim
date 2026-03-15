from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import copy
import pandas as pd

from .config import TEAM_ALIASES, TEAMS, STARTER_ROLES, CHASE_ROLES, SETUP_ROLES, CLOSER_ROLE, PITCHER_ROLE_ORDER, USER_TEAM


@dataclass
class LoadedData:
    batting: pd.DataFrame
    pitching: pd.DataFrame
    batter_roster: pd.DataFrame
    pitcher_roster: pd.DataFrame
    schedule: pd.DataFrame
    team_hitters: Dict[str, Dict[str, List[dict]]]
    team_pitchers: Dict[str, Dict[str, dict]]
    all_dates: List[str]


def normalize_team(team: str) -> str:
    return TEAM_ALIASES.get(str(team), str(team))


def _safe_float(x, default=0.0) -> float:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def _safe_int(x, default=0) -> int:
    try:
        if pd.isna(x):
            return default
        return int(float(x))
    except Exception:
        return default


def _latest_by_team_name(df: pd.DataFrame, team_col: str, name_col: str) -> pd.DataFrame:
    if "날짜" in df.columns:
        tmp = df.copy()
        tmp["날짜"] = pd.to_datetime(tmp["날짜"], errors="coerce")
        tmp = tmp.sort_values(["날짜", team_col], ascending=[False, True])
        return tmp.drop_duplicates([team_col, name_col], keep="first")
    return df.drop_duplicates([team_col, name_col], keep="first")


def make_fallback_batter(team: str, name: str, page_id: int = 0) -> dict:
    return {
        "팀": team, "선수명": name, "page_id": page_id,
        "타석": 1, "타수": 1, "안타": 0, "볼넷": 0, "사구": 0, "삼진": 0,
        "2루타": 0, "3루타": 0, "홈런": 0, "희번": 0, "희비": 0,
        "K%": 0.18, "PA/HR": 999.0, "ST": 0, "SB": 0, "CS": 0,
        "병살비율": 0.0, "희번성공 비율": 0.0, "타율": 0.0, "출루율": 0.0, "장타율": 0.0, "OPS": 0.0, "wRAA": 0.0,
    }


def make_fallback_pitcher(team: str, name: str, role: str, page_id: int = 0) -> dict:
    return {
        "팀": team, "선수명": name, "page_id": page_id, "역할": role,
        "타자수": 1, "피안타": 0, "볼넷": 0, "삼진": 0, "실점": 0,
        "2B": 0, "3B": 0, "피홈런": 0, "K%": 0.18, "RA9": 4.50,
    }


def batter_record_from_row(stat_row: dict | pd.Series, roster_row=None) -> dict:
    rr = stat_row if isinstance(stat_row, dict) else stat_row.to_dict()
    roster = {} if roster_row is None else (roster_row.to_dict() if hasattr(roster_row, "to_dict") else dict(roster_row))
    team = normalize_team(rr.get("팀", roster.get("팀", "")))
    return {
        "team": team,
        "name": str(rr.get("선수명", roster.get("선수명", ""))),
        "page_id": _safe_int(rr.get("page_id", roster.get("page_id", 0))),
        "order": _safe_int(roster.get("타순", 0), 0),
        "pos": str(roster.get("포지션", "")),
        "foreign": str(roster.get("외국인여부", "")) == "외국인",
        "pa": max(1, _safe_int(rr.get("타석"), 1)),
        "ab": _safe_int(rr.get("타수")),
        "h": _safe_int(rr.get("안타")),
        "bb": _safe_int(rr.get("볼넷")),
        "hbp": _safe_int(rr.get("사구")),
        "k": _safe_int(rr.get("삼진")),
        "k_rate": _safe_float(rr.get("K%"), _safe_int(rr.get("삼진")) / max(1, _safe_int(rr.get("타석"), 1))),
        "doubles": _safe_int(rr.get("2루타")),
        "triples": _safe_int(rr.get("3루타")),
        "hr": _safe_int(rr.get("홈런")),
        "st": _safe_int(rr.get("ST")),
        "sb": _safe_int(rr.get("SB")),
        "cs": _safe_int(rr.get("CS")),
        "gidp_rate": _safe_float(rr.get("병살비율")) / 100.0,
        "sac_bunt_success_rate": _safe_float(rr.get("희번성공 비율")) / 100.0,
        "pa_per_hr": max(_safe_float(rr.get("PA/HR"), 999.0), 1.0),
        "avg": _safe_float(rr.get("타율")),
        "obp": _safe_float(rr.get("출루율")),
        "slg": _safe_float(rr.get("장타율")),
        "ops": _safe_float(rr.get("OPS")),
        "wraa": max(0.0, _safe_float(rr.get("wRAA"))),
    }


def pitcher_record_from_row(stat_row: dict | pd.Series, roster_row=None) -> dict:
    rr = stat_row if isinstance(stat_row, dict) else stat_row.to_dict()
    roster = {} if roster_row is None else (roster_row.to_dict() if hasattr(roster_row, "to_dict") else dict(roster_row))
    team = normalize_team(rr.get("팀", roster.get("팀", "")))
    role = str(roster.get("역할", rr.get("역할", "")))
    return {
        "team": team,
        "name": str(rr.get("선수명", roster.get("선수명", ""))),
        "page_id": _safe_int(rr.get("page_id", roster.get("page_id", 0))),
        "role": role,
        "foreign": str(roster.get("외국인여부", "")) == "외국인",
        "bf": max(1, _safe_int(rr.get("타자수"), 1)),
        "h": _safe_int(rr.get("피안타")),
        "bb": _safe_int(rr.get("볼넷")),
        "k": _safe_int(rr.get("삼진")),
        "k_rate": _safe_float(rr.get("K%"), _safe_int(rr.get("삼진")) / max(1, _safe_int(rr.get("타자수"), 1))),
        "doubles": _safe_int(rr.get("2B")),
        "triples": _safe_int(rr.get("3B")),
        "hr": _safe_int(rr.get("피홈런")),
        "runs": _safe_int(rr.get("실점")),
        "ra9": _safe_float(rr.get("RA9"), 4.5),
    }


def build_team_hitters(batting: pd.DataFrame, batter_roster: pd.DataFrame) -> Dict[str, Dict[str, List[dict]]]:
    latest = _latest_by_team_name(batting, "팀", "선수명")
    by_page = latest.set_index("page_id").to_dict("index") if "page_id" in latest.columns else {}
    by_name_team = latest.set_index(["팀", "선수명"]).to_dict("index")

    out: Dict[str, Dict[str, List[dict]]] = {}
    for team in TEAMS:
        rows = batter_roster[batter_roster["팀"] == team].copy()
        if rows.empty:
            out[team] = {"starters": [], "bench": []}
            continue
        rows["타순"] = rows["타순"].fillna(0).astype(int)
        players = []
        for _, r in rows.sort_values(["타순", "선수명"]).iterrows():
            stat = by_page.get(r["page_id"]) or by_name_team.get((team, r["선수명"])) or make_fallback_batter(team, r["선수명"], r.get("page_id", 0))
            players.append(batter_record_from_row(stat, r))
        starters = sorted([p for p in players if p["order"] > 0], key=lambda x: x["order"])[:9]
        bench = [copy.deepcopy(p) for p in players if p["order"] == 0]
        if len(starters) < 9:
            need = 9 - len(starters)
            fillers = sorted(bench, key=lambda x: (-x["ops"], -x["wraa"]))[:need]
            for idx, p in enumerate(fillers, start=len(starters) + 1):
                p["order"] = idx
                starters.append(p)
                bench = [b for b in bench if b["name"] != p["name"]]
        out[team] = {"starters": [copy.deepcopy(p) for p in sorted(starters, key=lambda x: x["order"])], "bench": bench}
    return out


def build_team_pitchers(pitching: pd.DataFrame, pitcher_roster: pd.DataFrame) -> Dict[str, Dict[str, dict]]:
    latest = _latest_by_team_name(pitching, "팀", "선수명")
    by_page = latest.set_index("page_id").to_dict("index") if "page_id" in latest.columns else {}
    by_name_team = latest.set_index(["팀", "선수명"]).to_dict("index")

    out: Dict[str, Dict[str, dict]] = {}
    for team in TEAMS:
        rows = pitcher_roster[pitcher_roster["팀"] == team].copy()
        staff: Dict[str, dict] = {}
        for role in PITCHER_ROLE_ORDER:
            match = rows[rows["역할"] == role]
            if match.empty:
                continue
            r = match.iloc[0]
            stat = by_page.get(r["page_id"]) or by_name_team.get((team, r["선수명"])) or make_fallback_pitcher(team, r["선수명"], role, r.get("page_id", 0))
            staff[role] = pitcher_record_from_row(stat, r)
        out[team] = staff
    return out


def load_csvs(data_dir: str | Path) -> LoadedData:
    data_dir = Path(data_dir)
    batting = pd.read_csv(data_dir / "2025타자 성적.csv")
    pitching = pd.read_csv(data_dir / "2025투수 성적.csv")
    batter_roster = pd.read_csv(data_dir / "roster_2026_batters_15man_no_transfer.csv")
    pitcher_roster = pd.read_csv(data_dir / "roster_2026_pitchers_13man_no_transfer.csv")
    schedule = pd.read_csv(data_dir / "KBO_2025_ELO_Result.csv")

    for df in [batting, pitching, batter_roster, pitcher_roster]:
        if "팀" in df.columns:
            df["팀"] = df["팀"].map(normalize_team)
    schedule["Away"] = schedule["Away"].map(normalize_team)
    schedule["Home"] = schedule["Home"].map(normalize_team)
    schedule["날짜"] = pd.to_datetime(schedule["날짜"], errors="coerce").dt.strftime("%Y-%m-%d")
    schedule = schedule[["날짜", "Away", "Home"]].dropna().sort_values(["날짜", "Away", "Home"]).reset_index(drop=True)

    team_hitters = build_team_hitters(batting, batter_roster)
    team_pitchers = build_team_pitchers(pitching, pitcher_roster)
    all_dates = sorted(schedule["날짜"].dropna().unique().tolist())

    return LoadedData(
        batting=batting,
        pitching=pitching,
        batter_roster=batter_roster,
        pitcher_roster=pitcher_roster,
        schedule=schedule,
        team_hitters=team_hitters,
        team_pitchers=team_pitchers,
        all_dates=all_dates,
    )


def deep_copy_team_hitters(team_hitters: Dict[str, Dict[str, List[dict]]]) -> Dict[str, Dict[str, List[dict]]]:
    return copy.deepcopy(team_hitters)


def deep_copy_team_pitchers(team_pitchers: Dict[str, Dict[str, dict]]) -> Dict[str, Dict[str, dict]]:
    return copy.deepcopy(team_pitchers)


def get_trade_candidates(data: LoadedData, team: str) -> List[dict]:
    roster = data.team_hitters.get(team, {"starters": [], "bench": []})
    all_hitters = roster["starters"] + roster["bench"]
    return [copy.deepcopy(p) for p in all_hitters if not p.get("foreign", False)]
