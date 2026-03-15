from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math
import random

from .config import FIELDING_CLEAN_RATE, HIGH_LEVERAGE_BY_INNING, LEAGUE_BASE_ONBASE, LEAGUE_BASE_K, MAX_STEAL_ATTEMPT_RATE


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def normalized_shares(values: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, v) for v in values.values())
    if total <= 0:
        n = len(values)
        return {k: 1.0 / n for k in values}
    return {k: max(0.0, v) / total for k, v in values.items()}


def combine_onbase(batter_on: float, pitcher_allow: float) -> float:
    # log5 고집 대신 과도한 극단값을 줄이기 위한 평균+리그보정 혼합
    avg = 0.5 * batter_on + 0.5 * pitcher_allow
    geo = math.sqrt(max(batter_on, 1e-9) * max(pitcher_allow, 1e-9))
    value = 0.65 * avg + 0.35 * geo
    return clamp(value, 0.18, 0.52)


def combine_k(batter_k: float, pitcher_k: float) -> float:
    avg = 0.55 * batter_k + 0.45 * pitcher_k
    geo = math.sqrt(max(batter_k, 1e-9) * max(pitcher_k, 1e-9))
    return clamp(0.5 * avg + 0.5 * geo, 0.05, 0.5)


def batter_rates(b: dict) -> dict:
    pa = max(int(b["pa"]), 1)
    single = max(0, int(b["h"]) - int(b["doubles"]) - int(b["triples"]) - int(b["hr"])) / pa
    double = int(b["doubles"]) / pa
    triple = int(b["triples"]) / pa
    homer = int(b["hr"]) / pa
    walk = (int(b["bb"]) + int(b["hbp"])) / pa
    onbase = single + double + triple + homer + walk
    out = max(0.0, 1.0 - onbase)
    return {"single": single, "double": double, "triple": triple, "homer": homer, "walk": walk, "onbase": onbase, "out": out, "k": float(b["k_rate"])}


def pitcher_rates(p: dict) -> dict:
    bf = max(int(p["bf"]), 1)
    allowed = max(int(p["h"]) + int(p["bb"]), 1)
    single = max(0, int(p["h"]) - int(p["doubles"]) - int(p["triples"]) - int(p["hr"])) / allowed
    double = int(p["doubles"]) / allowed
    triple = int(p["triples"]) / allowed
    homer = int(p["hr"]) / allowed
    walk = int(p["bb"]) / allowed
    allow = allowed / bf
    out = max(0.0, 1.0 - allow)
    return {"single": single, "double": double, "triple": triple, "homer": homer, "walk": walk, "onbase": allow, "out": out, "k": float(p["k_rate"])}


def combine_event_probs(batter: dict, pitcher: dict) -> dict:
    br = batter_rates(batter)
    pr = pitcher_rates(pitcher)

    onbase = combine_onbase(br["onbase"], pr["onbase"])

    batter_shares = normalized_shares({
        "single": br["single"], "double": br["double"], "triple": br["triple"], "homer": br["homer"], "walk": br["walk"]
    })
    pitcher_shares = normalized_shares({
        "single": pr["single"], "double": pr["double"], "triple": pr["triple"], "homer": pr["homer"], "walk": pr["walk"]
    })

    mixed = {}
    for k in batter_shares:
        mixed[k] = math.sqrt(max(batter_shares[k], 1e-9) * max(pitcher_shares[k], 1e-9))
    mixed = normalized_shares(mixed)

    probs = {k: onbase * mixed[k] for k in mixed}
    probs["out"] = max(0.0, 1.0 - onbase)
    probs["k_on_out"] = clamp(combine_k(br["k"], pr["k"]) / max(probs["out"], 1e-9), 0.05, 0.95)
    return probs


def base_key(bases: list) -> str:
    return "".join("1" if x else "0" for x in bases)


def advance_walk(bases: list, batter: str) -> tuple[list, int]:
    b = bases[:]
    runs = 0
    if b[0] and b[1] and b[2]:
        runs += 1
    if b[1] and b[0]:
        b[2] = b[1]
    if b[0]:
        b[1] = b[0]
    b[0] = batter
    return b, runs


def advance_single(bases: list, batter: str, rng: random.Random) -> tuple[list, int]:
    out = [None, None, None]
    runs = 0
    if bases[2]:
        runs += 1
    if bases[1]:
        if rng.random() < 0.5:
            runs += 1
        else:
            out[2] = bases[1]
    if bases[0]:
        out[1] = bases[0]
    out[0] = batter
    return out, runs


def advance_double(bases: list, batter: str, rng: random.Random) -> tuple[list, int]:
    out = [None, None, None]
    runs = 0
    if bases[2]:
        runs += 1
    if bases[1]:
        runs += 1
    if bases[0]:
        if rng.random() < 0.5:
            runs += 1
        else:
            out[2] = bases[0]
    out[1] = batter
    return out, runs


def advance_triple(bases: list, batter: str) -> tuple[list, int]:
    return [None, None, batter], sum(1 for x in bases if x)


def advance_homer(bases: list) -> tuple[list, int]:
    return [None, None, None], sum(1 for x in bases if x) + 1


def should_bunt(inning: int, outs: int, score_diff: int, batter_order: int) -> bool:
    if inning not in (7, 8, 9):
        return False
    if outs != 0:
        return False
    if score_diff not in (-1, -2, -3):
        return False
    if batter_order in (3, 4, 5):
        return False
    return batter_order in (1, 2, 6, 7, 8, 9)


def try_bunt(batter: dict, bases: list, rng: random.Random) -> Optional[dict]:
    success = rng.random() < float(batter["sac_bunt_success_rate"])
    b = bases[:]
    if success:
        if b[1]:
            b[2] = b[1]
        if b[0]:
            b[1] = b[0]
        b[0] = None
        return {"event": "희생번트", "bases": b, "runs": 0, "outs": 1, "strikeout": False, "error": False}
    return {"event": "번트 실패", "bases": b, "runs": 0, "outs": 1, "strikeout": False, "error": False}


def try_double_play(batter: dict, bases: list, outs: int, rng: random.Random) -> Optional[dict]:
    if outs >= 2 or not bases[0]:
        return None
    if rng.random() >= float(batter["gidp_rate"]):
        return None

    key = base_key(bases)
    if key == "100":
        return {"event": "병살타", "bases": [None, None, None], "runs": 0, "outs": 2, "strikeout": False, "error": False}
    if key == "110":
        return {"event": "병살타", "bases": [None, None, bases[1]], "runs": 0, "outs": 2, "strikeout": False, "error": False}
    if key == "101":
        if rng.random() < 0.5:
            return {"event": "병살타", "bases": [None, bases[2], None], "runs": 0, "outs": 2, "strikeout": False, "error": False}
        return {"event": "병살타(1득점)", "bases": [None, None, None], "runs": 1, "outs": 2, "strikeout": False, "error": False}
    if key == "111":
        roll = rng.randint(0, 2)
        if roll == 0:
            return {"event": "병살타", "bases": [None, bases[1], bases[2]], "runs": 0, "outs": 2, "strikeout": False, "error": False}
        if roll == 1:
            return {"event": "병살타(1득점)", "bases": [None, bases[1], None], "runs": 1, "outs": 2, "strikeout": False, "error": False}
        return {"event": "병살타(1득점)", "bases": [None, None, bases[2]], "runs": 1, "outs": 2, "strikeout": False, "error": False}
    return None


def try_sac_fly(batter: dict, bases: list, outs: int, rng: random.Random) -> Optional[dict]:
    if outs >= 2 or not bases[2]:
        return None
    chance = clamp((100.0 - float(batter["pa_per_hr"])) / 100.0, 0.0, 0.95)
    if rng.random() >= chance:
        return None

    key = base_key(bases)
    if key == "001":
        return {"event": "희생플라이", "bases": [None, None, None], "runs": 1, "outs": 1, "strikeout": False, "error": False}
    if key == "011":
        return {"event": "희생플라이", "bases": [None, None, bases[1]], "runs": 1, "outs": 1, "strikeout": False, "error": False}
    if key == "010":
        return {"event": "뜬공 진루", "bases": [None, None, bases[1]], "runs": 0, "outs": 1, "strikeout": False, "error": False}
    if key == "101":
        return {"event": "희생플라이", "bases": [bases[0], None, None], "runs": 1, "outs": 1, "strikeout": False, "error": False}
    if key == "110":
        return {"event": "뜬공 진루", "bases": [bases[0], None, bases[1]], "runs": 0, "outs": 1, "strikeout": False, "error": False}
    if key == "111":
        return {"event": "희생플라이", "bases": [bases[0], None, bases[1]], "runs": 1, "outs": 1, "strikeout": False, "error": False}
    return None


def steal_attempt_result(runner: dict, rng: random.Random) -> Optional[bool]:
    denom = max(1, runner["h"] + runner["bb"] + runner["hbp"] - runner["doubles"] - runner["triples"] - runner["hr"])
    attempt_rate = min(MAX_STEAL_ATTEMPT_RATE, float(runner["st"]) / denom)
    if rng.random() >= attempt_rate:
        return None
    if int(runner["st"]) <= 0:
        return False
    success_rate = clamp(float(runner["sb"]) / max(int(runner["st"]), 1), 0.0, 1.0)
    return rng.random() < success_rate


@dataclass
class PitcherUsage:
    role: str
    pitcher: dict
    outs_recorded: int = 0
    runs_allowed: int = 0

    @property
    def innings_pitched(self) -> float:
        return self.outs_recorded / 3.0


@dataclass
class TeamGameState:
    team: str
    lineup: List[dict]
    staff: Dict[str, dict]
    batting_index: int = 0
    current_pitcher_role: str = ""
    pitcher_usage: Dict[str, PitcherUsage] = field(default_factory=dict)

    def current_pitcher(self) -> dict:
        return self.pitcher_usage[self.current_pitcher_role].pitcher

    def next_batter(self) -> dict:
        batter = self.lineup[self.batting_index % len(self.lineup)]
        self.batting_index += 1
        return batter

    def use_pitcher(self, role: str):
        if role not in self.pitcher_usage:
            self.pitcher_usage[role] = PitcherUsage(role=role, pitcher=self.staff[role])
        self.current_pitcher_role = role


@dataclass
class GameResult:
    away: str
    home: str
    away_runs: int
    home_runs: int
    away_hits: int
    home_hits: int
    away_errors: int
    home_errors: int
    line_score_away: List[int]
    line_score_home: List[int]
    feed: List[str]
    batter_box: List[dict]
    pitcher_box: List[dict]


class GameSimulator:
    def __init__(self, away_team: str, home_team: str, away_lineup: list, home_lineup: list, away_staff: dict, home_staff: dict, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.away = TeamGameState(away_team, away_lineup, away_staff)
        self.home = TeamGameState(home_team, home_lineup, home_staff)

        away_sp = self._rotation_starter(away_staff)
        home_sp = self._rotation_starter(home_staff)
        self.away.use_pitcher(away_sp)
        self.home.use_pitcher(home_sp)

        self.inning = 1
        self.half = "top"
        self.outs = 0
        self.bases = [None, None, None]
        self.score = {"away": 0, "home": 0}
        self.hits = {"away": 0, "home": 0}
        self.errors = {"away": 0, "home": 0}
        self.line_score = {"away": [], "home": []}
        self.feed: List[str] = []
        self.batter_box: List[dict] = []
        self.pitcher_box: List[dict] = []

    def _rotation_starter(self, staff: dict) -> str:
        for role in ("선발1", "선발2", "선발3", "선발4", "선발5"):
            if role in staff:
                return role
        return next(iter(staff.keys()))

    def offense(self) -> TeamGameState:
        return self.away if self.half == "top" else self.home

    def defense(self) -> TeamGameState:
        return self.home if self.half == "top" else self.away

    def offense_key(self) -> str:
        return "away" if self.half == "top" else "home"

    def defense_key(self) -> str:
        return "home" if self.half == "top" else "away"

    def play_game(self) -> GameResult:
        while True:
            self.play_plate_appearance()
            if self.half == "top" and self.inning >= 10 and self.score["away"] != self.score["home"] and self.outs == 0 and self.bases == [None, None, None]:
                break
            if self.half == "top" and self.inning == 10 and self.score["home"] > self.score["away"]:
                break
            if self.half == "top" and self.inning > 9 and self.score["away"] != self.score["home"] and self.score["home"] > self.score["away"] and self.outs == 0:
                break
            if self.inning > 9 and self.score["away"] != self.score["home"] and self.half == "top" and self.outs == 0 and self.bases == [None, None, None]:
                break
            if self.inning > 9 and self.score["away"] != self.score["home"] and self.half == "bottom" and self.outs == 3:
                break
            if self.inning == 9 and self.half == "bottom" and self.score["home"] > self.score["away"] and self.outs == 3:
                break
            if self.inning > 15:
                break

        self._finalize_line_score()
        self._build_pitcher_box()
        return GameResult(
            away=self.away.team,
            home=self.home.team,
            away_runs=self.score["away"],
            home_runs=self.score["home"],
            away_hits=self.hits["away"],
            home_hits=self.hits["home"],
            away_errors=self.errors["away"],
            home_errors=self.errors["home"],
            line_score_away=self.line_score["away"],
            line_score_home=self.line_score["home"],
            feed=self.feed,
            batter_box=self.batter_box,
            pitcher_box=self.pitcher_box,
        )

    def _score_diff_for_offense(self) -> int:
        key = self.offense_key()
        other = self.defense_key()
        return self.score[key] - self.score[other]

    def play_plate_appearance(self):
        offense = self.offense()
        defense = self.defense()
        batter = offense.next_batter()
        pitcher = defense.current_pitcher()

        # 도루: 1루에만 있을 때만 자동 확인
        if self.bases[0] and not self.bases[1]:
            runner = self.bases[0]
            steal = steal_attempt_result(runner, self.rng)
            if steal is not None:
                if steal:
                    self.bases = [None, runner, self.bases[2]]
                    self.feed.append(f"{self.inning}회 {offense.team} {runner['name']} 도루 성공")
                else:
                    self.bases = [None, self.bases[1], self.bases[2]]
                    self.outs += 1
                    self.feed.append(f"{self.inning}회 {offense.team} {runner['name']} 도루 실패")
                    defense.pitcher_usage[defense.current_pitcher_role].outs_recorded += 1
                    if self.outs >= 3:
                        self.end_half_inning()
                    return

        if should_bunt(self.inning, self.outs, self._score_diff_for_offense(), batter["order"]):
            result = try_bunt(batter, self.bases, self.rng)
            self.apply_result(batter, result)
            return

        probs = combine_event_probs(batter, pitcher)
        roll = self.rng.random()

        if roll < probs["walk"]:
            new_bases, runs = advance_walk(self.bases, batter)
            self.apply_result(batter, {"event": "볼넷", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False})
            return
        roll -= probs["walk"]

        if roll < probs["single"]:
            new_bases, runs = advance_single(self.bases, batter, self.rng)
            self.hits[self.offense_key()] += 1
            self.apply_result(batter, {"event": "안타", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False})
            return
        roll -= probs["single"]

        if roll < probs["double"]:
            new_bases, runs = advance_double(self.bases, batter, self.rng)
            self.hits[self.offense_key()] += 1
            self.apply_result(batter, {"event": "2루타", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False})
            return
        roll -= probs["double"]

        if roll < probs["triple"]:
            new_bases, runs = advance_triple(self.bases, batter)
            self.hits[self.offense_key()] += 1
            self.apply_result(batter, {"event": "3루타", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False})
            return
        roll -= probs["triple"]

        if roll < probs["homer"]:
            new_bases, runs = advance_homer(self.bases)
            self.hits[self.offense_key()] += 1
            self.apply_result(batter, {"event": "홈런", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False})
            return

        strikeout = self.rng.random() < probs["k_on_out"]
        if not strikeout:
            dp = try_double_play(batter, self.bases, self.outs, self.rng)
            if dp is not None:
                self.apply_result(batter, dp)
                return

            sf = try_sac_fly(batter, self.bases, self.outs, self.rng)
            if sf is not None:
                self.apply_result(batter, sf)
                return

            clean_rate = FIELDING_CLEAN_RATE[defense.team]
            error_rate = 1.0 - clean_rate
            if self.rng.random() < error_rate:
                new_bases, runs = advance_walk(self.bases, batter)
                self.errors[self.defense_key()] += 1
                self.apply_result(batter, {"event": "실책 출루", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": True})
                return

        self.apply_result(batter, {"event": "삼진" if strikeout else "범타", "bases": self.bases[:], "runs": 0, "outs": 1, "strikeout": strikeout, "error": False})

    def apply_result(self, batter: dict, result: dict):
        offense = self.offense()
        defense = self.defense()
        off_key = self.offense_key()

        self.bases = result["bases"]
        self.score[off_key] += result["runs"]
        self.outs += result["outs"]

        usage = defense.pitcher_usage[defense.current_pitcher_role]
        usage.outs_recorded += result["outs"]
        usage.runs_allowed += result["runs"]

        self.batter_box.append({
            "team": offense.team,
            "name": batter["name"],
            "event": result["event"],
            "inning": self.inning,
            "half": self.half,
            "runs_batted": result["runs"],
        })
        self.feed.append(f"{self.inning}회{'초' if self.half=='top' else '말'} {offense.team} {batter['name']} {result['event']}")

        self._maybe_replace_pitcher_mid_inning()

        if self.outs >= 3:
            self.end_half_inning()

    def _should_high_leverage_reliever(self, team_state: TeamGameState) -> Optional[str]:
        if self.inning not in HIGH_LEVERAGE_BY_INNING:
            return None
        if self.half == "top":
            lead = self.score["home"] - self.score["away"] if team_state.team == self.home.team else self.score["away"] - self.score["home"]
        else:
            lead = self.score["home"] - self.score["away"] if team_state.team == self.home.team else self.score["away"] - self.score["home"]
        if 1 <= lead <= 3:
            desired = HIGH_LEVERAGE_BY_INNING[self.inning]
            if desired in team_state.staff and team_state.current_pitcher_role != desired:
                return desired
        return None

    def _maybe_replace_pitcher_mid_inning(self):
        defense = self.defense()
        usage = defense.pitcher_usage[defense.current_pitcher_role]
        role = defense.current_pitcher_role

        high_lev = self._should_high_leverage_reliever(defense)
        if high_lev is not None and role != high_lev:
            defense.use_pitcher(high_lev)
            self.feed.append(f"{defense.team} 투수교체: {high_lev}")
            return

        if role.startswith("선발"):
            innings = usage.innings_pitched
            runs = usage.runs_allowed

            limit = None
            if runs <= 0:
                limit = 9
            elif runs <= 1:
                limit = 8
            elif runs <= 2:
                limit = 7
            elif runs <= 3:
                limit = 6
            elif runs == 4:
                limit = 5
            elif runs == 5:
                limit = 4
            else:
                limit = innings

            if innings >= limit:
                next_role = self._first_available_followup_role(defense)
                if next_role:
                    defense.use_pitcher(next_role)
                    self.feed.append(f"{defense.team} 선발 강판 → {next_role}")
            return

        if role.startswith("추격조"):
            if usage.runs_allowed >= 1 or usage.outs_recorded >= 3:
                next_role = self._next_chase_role(defense, role)
                if next_role:
                    defense.use_pitcher(next_role)
                    self.feed.append(f"{defense.team} 투수교체: {next_role}")
            return

        if role.startswith("셋업맨") or role == "마무리":
            if usage.outs_recorded >= 3:
                nxt = self._next_high_leverage_chain(defense, role)
                if nxt:
                    defense.use_pitcher(nxt)
                    self.feed.append(f"{defense.team} 투수교체: {nxt}")
            return

    def _first_available_followup_role(self, team_state: TeamGameState) -> Optional[str]:
        for role in ("추격조1", "추격조2", "추격조3", "추격조4", "추격조5", "셋업맨2", "셋업맨1", "마무리"):
            if role in team_state.staff:
                if role not in team_state.pitcher_usage or team_state.pitcher_usage[role].outs_recorded < 3:
                    return role
        return None

    def _next_chase_role(self, team_state: TeamGameState, current_role: str) -> Optional[str]:
        chase_order = ["추격조1", "추격조2", "추격조3", "추격조4", "추격조5", "셋업맨2", "셋업맨1", "마무리"]
        idx = chase_order.index(current_role)
        for role in chase_order[idx + 1:]:
            if role in team_state.staff:
                return role
        return None

    def _next_high_leverage_chain(self, team_state: TeamGameState, current_role: str) -> Optional[str]:
        order = ["셋업맨2", "셋업맨1", "마무리"]
        if current_role not in order:
            return None
        idx = order.index(current_role)
        for role in order[idx + 1:]:
            if role in team_state.staff:
                return role
        return None

    def end_half_inning(self):
        key = self.offense_key()
        current_total = self.score[key]
        line = self.line_score[key]
        previous = sum(line)
        line.append(current_total - previous)

        self.outs = 0
        self.bases = [None, None, None]
        if self.half == "top":
            self.half = "bottom"
        else:
            self.half = "top"
            self.inning += 1

    def _finalize_line_score(self):
        while len(self.line_score["away"]) < len(self.line_score["home"]):
            self.line_score["away"].append(0)
        while len(self.line_score["home"]) < len(self.line_score["away"]):
            self.line_score["home"].append(0)
        if len(self.line_score["away"]) == 0:
            self.line_score["away"].append(self.score["away"])
        if len(self.line_score["home"]) == 0:
            self.line_score["home"].append(self.score["home"])

    def _build_pitcher_box(self):
        for side in (self.away, self.home):
            for role, usage in side.pitcher_usage.items():
                self.pitcher_box.append({
                    "team": side.team,
                    "name": usage.pitcher["name"],
                    "role": role,
                    "outs": usage.outs_recorded,
                    "ip": usage.outs_recorded / 3.0,
                    "runs": usage.runs_allowed,
                })
