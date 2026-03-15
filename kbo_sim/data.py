from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

from .config import TEAM_ALIASES, TEAMS, PITCHER_ROLE_ORDER


@dataclass
class LoadedData:
    batting: pd.DataFrame
    pitching: pd.DataFrame
    batter_roster: pd.DataFrame
    pitcher_roster: pd.DataFrame
    schedule: pd.DataFrame
    team_lineups: Dict[str, List[dict]]
    team_pitchers: Dict[str, Dict[str, dict]]
    all_dates: List[str]


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


def normalize_team(team: str) -> str:
    return TEAM_ALIASES.get(str(team), str(team))


def load_csvs(data_dir: str | Path) -> LoadedData:
    data_dir = Path(data_dir)

    batting = pd.read_csv(data_dir / "2025타자 성적.csv")
    pitching = pd.read_csv(data_dir / "2025투수 성적.csv")
    batter_roster = pd.read_csv(data_dir / "roster_2026_batters_15man_no_transfer.csv")
    pitcher_roster = pd.read_csv(data_dir / "roster_2026_pitchers_13man_no_transfer.csv")
    schedule = pd.read_csv(data_dir / "KBO_2025_ELO_Result.csv")

    for df in [batting, pitching, batter_roster, pitcher_roster, schedule]:
        if "팀" in df.columns:
            df["팀"] = df["팀"].map(normalize_team)
    if "Away" in schedule.columns:
        schedule["Away"] = schedule["Away"].map(normalize_team)
    if "Home" in schedule.columns:
        schedule["Home"] = schedule["Home"].map(normalize_team)

    batting["team"] = batting["팀"].map(normalize_team)
    pitching["team"] = pitching["팀"].map(normalize_team)

    team_lineups = build_team_lineups(batting, batter_roster)
    team_pitchers = build_team_pitching_staff(pitching, pitcher_roster)

    keep_cols = ["날짜", "Away", "Home"]
    schedule = schedule[keep_cols].copy()
    schedule["날짜"] = pd.to_datetime(schedule["날짜"]).dt.strftime("%Y-%m-%d")
    schedule = schedule.sort_values(["날짜", "Away", "Home"]).reset_index(drop=True)
    all_dates = sorted(schedule["날짜"].unique().tolist())

    return LoadedData(
        batting=batting,
        pitching=pitching,
        batter_roster=batter_roster,
        pitcher_roster=pitcher_roster,
        schedule=schedule,
        team_lineups=team_lineups,
        team_pitchers=team_pitchers,
        all_dates=all_dates,
    )


def build_team_lineups(batting: pd.DataFrame, batter_roster: pd.DataFrame) -> Dict[str, List[dict]]:
    latest = batting.sort_values(["팀", "타석"], ascending=[True, False]).drop_duplicates(["팀", "page_id"], keep="first")
    batting_by_page = latest.set_index("page_id").to_dict("index")
    batting_by_name_team = latest.groupby(["팀", "선수명"]).head(1).set_index(["팀", "선수명"]).to_dict("index")

    team_lineups: Dict[str, List[dict]] = {}
    for team in TEAMS:
        rows = batter_roster[batter_roster["팀"] == team].copy()
        rows["타순"] = rows["타순"].fillna(0).astype(int)

        selected: List[dict] = []
        for _, r in rows.sort_values(["타순", "선수명"], ascending=[True, True]).iterrows():
            page_id = r["page_id"]
            stat = batting_by_page.get(page_id)
            if stat is None:
                stat = batting_by_name_team.get((team, r["선수명"]))
            if stat is None:
                stat = make_fallback_batter(team, r["선수명"])

            player = batter_record_from_row(stat, roster_row=r)
            selected.append(player)

        starters = [p for p in selected if p["order"] > 0]
        starters = sorted(starters, key=lambda x: x["order"])[:9]

        if len(starters) < 9:
            bench = [p for p in selected if p["order"] == 0]
            for idx, p in enumerate(bench, start=len(starters) + 1):
                p = dict(p)
                p["order"] = idx
                starters.append(p)
                if len(starters) == 9:
                    break

        team_lineups[team] = sorted(starters, key=lambda x: x["order"])
    return team_lineups


def build_team_pitching_staff(pitching: pd.DataFrame, pitcher_roster: pd.DataFrame) -> Dict[str, Dict[str, dict]]:
    latest = pitching.sort_values(["팀", "타자수"], ascending=[True, False]).drop_duplicates(["팀", "page_id"], keep="first")
    by_page = latest.set_index("page_id").to_dict("index")
    by_name_team = latest.groupby(["팀", "선수명"]).head(1).set_index(["팀", "선수명"]).to_dict("index")

    out: Dict[str, Dict[str, dict]] = {}
    for team in TEAMS:
        rows = pitcher_roster[pitcher_roster["팀"] == team].copy()
        staff: Dict[str, dict] = {}
        for role in PITCHER_ROLE_ORDER:
            match = rows[rows["역할"] == role]
            if match.empty:
                continue
            r = match.iloc[0]
            stat = by_page.get(r["page_id"])
            if stat is None:
                stat = by_name_team.get((team, r["선수명"]))
            if stat is None:
                stat = make_fallback_pitcher(team, r["선수명"], role)
            staff[role] = pitcher_record_from_row(stat, roster_row=r)
        out[team] = staff
    return out


def batter_record_from_row(row: dict | pd.Series, roster_row=None) -> dict:
    rr = row if isinstance(row, dict) else row.to_dict()
    order = _safe_int(getattr(roster_row, "타순", None) if roster_row is not None else rr.get("타순", 0), 0)
    pos = str(getattr(roster_row, "포지션", None) if roster_row is not None else rr.get("포지션", ""))
    return {
        "team": normalize_team(rr.get("팀", rr.get("team", ""))),
        "name": str(rr.get("선수명")),
        "page_id": _safe_int(rr.get("page_id")),
        "order": order,
        "pos": pos,
        "pa": _safe_int(rr.get("타석"), 1),
        "h": _safe_int(rr.get("안타")),
        "bb": _safe_int(rr.get("볼넷")),
        "hbp": _safe_int(rr.get("사구")),
        "k_rate": _safe_float(rr.get("K%")),
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
        "wraa": _safe_float(rr.get("wRAA")),
        "foreign": str(getattr(roster_row, "외국인여부", "") if roster_row is not None else rr.get("외국인여부", "")) == "외국인",
    }


def pitcher_record_from_row(row: dict | pd.Series, roster_row=None) -> dict:
    rr = row if isinstance(row, dict) else row.to_dict()
    role = str(getattr(roster_row, "역할", None) if roster_row is not None else rr.get("역할", ""))
    return {
        "team": normalize_team(rr.get("팀", rr.get("team", ""))),
        "name": str(rr.get("선수명")),
        "page_id": _safe_int(rr.get("page_id")),
        "role": role,
        "bf": max(_safe_int(rr.get("타자수"), 1), 1),
        "h": _safe_int(rr.get("피안타")),
        "bb": _safe_int(rr.get("볼넷")),
        "k_rate": _safe_float(rr.get("K%")),
        "doubles": _safe_int(rr.get("2B")),
        "triples": _safe_int(rr.get("3B")),
        "hr": _safe_int(rr.get("피홈런")),
        "ra9": _safe_float(rr.get("RA9")),
        "whip": _safe_float(rr.get("WHIP")),
        "foreign": str(getattr(roster_row, "외국인여부", "") if roster_row is not None else rr.get("외국인여부", "")) == "외국인",
    }


def make_fallback_batter(team: str, name: str) -> dict:
    return {
        "팀": team, "선수명": name, "page_id": -1, "타석": 100, "안타": 25, "볼넷": 8, "사구": 1,
        "K%": 0.18, "2루타": 4, "3루타": 1, "홈런": 2, "ST": 3, "SB": 2, "CS": 1,
        "병살비율": 0.07, "희번성공 비율": 0.6, "PA/HR": 50, "타율": 0.250, "출루율": 0.320,
        "장타율": 0.360, "OPS": 0.680, "wRAA": 0.0
    }


def make_fallback_pitcher(team: str, name: str, role: str) -> dict:
    return {
        "팀": team, "선수명": name, "page_id": -1, "타자수": 120, "피안타": 25, "볼넷": 10, "K%": 0.22,
        "2B": 4, "3B": 0, "피홈런": 3, "RA9": 4.5, "WHIP": 1.35, "역할": role
    }
