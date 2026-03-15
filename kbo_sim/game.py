from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import copy
import math
import random

from .config import (
    FIELDING_CLEAN_RATE,
    HIGH_LEVERAGE_BY_INNING,
    LEAGUE_BASE_ONBASE,
    LEAGUE_BASE_K,
    MAX_STEAL_ATTEMPT_RATE,
    MAX_EXTRA_INNING,
    STARTER_ROLES,
    CHASE_ROLES,
    SETUP_ROLES,
    CLOSER_ROLE,
    USER_TEAM,
)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def normalized_shares(values: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, v) for v in values.values())
    if total <= 0:
        n = len(values)
        return {k: 1.0 / n for k in values}
    return {k: max(0.0, v) / total for k, v in values.items()}


def combine_onbase(batter_on: float, pitcher_allow: float) -> float:
    avg = 0.55 * batter_on + 0.45 * pitcher_allow
    geo = math.sqrt(max(batter_on, 1e-9) * max(pitcher_allow, 1e-9))
    lg_pull = 0.5 * (batter_on - LEAGUE_BASE_ONBASE) + 0.5 * (pitcher_allow - LEAGUE_BASE_ONBASE)
    value = 0.45 * avg + 0.35 * geo + 0.20 * (LEAGUE_BASE_ONBASE + lg_pull)
    return clamp(value, 0.15, 0.55)


def combine_k(batter_k: float, pitcher_k: float) -> float:
    avg = 0.5 * batter_k + 0.5 * pitcher_k
    geo = math.sqrt(max(batter_k, 1e-9) * max(pitcher_k, 1e-9))
    return clamp(0.5 * avg + 0.5 * geo, 0.04, 0.55)


def batter_rates(b: dict) -> dict:
    pa = max(int(b["pa"]), 1)
    single = max(0, int(b["h"]) - int(b["doubles"]) - int(b["triples"]) - int(b["hr"])) / pa
    double = int(b["doubles"]) / pa
    triple = int(b["triples"]) / pa
    homer = int(b["hr"]) / pa
    walk = (int(b["bb"]) + int(b["hbp"])) / pa
    onbase = single + double + triple + homer + walk
    out = max(0.0, 1.0 - onbase)
    return {
        "single": single, "double": double, "triple": triple, "homer": homer, "walk": walk,
        "onbase": onbase, "out": out, "k": float(b["k_rate"])
    }


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
    return {
        "single": single, "double": double, "triple": triple, "homer": homer, "walk": walk,
        "onbase": allow, "out": out, "k": float(p["k_rate"])
    }


def combine_event_probs(batter: dict, pitcher: dict) -> dict:
    br = batter_rates(batter)
    pr = pitcher_rates(pitcher)
    onbase = combine_onbase(br["onbase"], pr["onbase"])

    batter_shares = normalized_shares({k: br[k] for k in ("single", "double", "triple", "homer", "walk")})
    pitcher_shares = normalized_shares({k: pr[k] for k in ("single", "double", "triple", "homer", "walk")})

    mixed = {}
    for k in batter_shares:
        mixed[k] = 0.55 * batter_shares[k] + 0.45 * pitcher_shares[k]
    mixed = normalized_shares(mixed)

    probs = {k: onbase * mixed[k] for k in mixed}
    probs["out"] = max(0.0, 1.0 - onbase)
    raw_k = combine_k(br["k"], pr["k"])
    probs["k_on_out"] = clamp(raw_k / max(probs["out"], 1e-9), 0.03, 0.97)
    return probs


@dataclass
class PitcherUsage:
    role: str
    pitcher: dict
    outs_recorded: int = 0
    runs_allowed: int = 0
    hits_allowed: int = 0
    walks_allowed: int = 0
    strikeouts: int = 0
    entered_manually: bool = False

    @property
    def innings_pitched(self) -> float:
        return self.outs_recorded / 3.0


@dataclass
class TeamGameState:
    team: str
    lineup: List[dict]
    bench: List[dict]
    staff: Dict[str, dict]
    batting_index: int = 0
    current_pitcher_role: str = ""
    pitcher_usage: Dict[str, PitcherUsage] = field(default_factory=dict)
    pending_force_bunt: bool = False
    pending_manual_pitcher_role: Optional[str] = None
    manual_chase_changes_used: int = 0

    def current_pitcher(self) -> dict:
        return self.pitcher_usage[self.current_pitcher_role].pitcher

    def next_batter_slot(self) -> int:
        return self.batting_index % len(self.lineup)

    def next_batter(self) -> dict:
        batter = self.lineup[self.next_batter_slot()]
        self.batting_index += 1
        return batter

    def use_pitcher(self, role: str, manual: bool = False):
        if role not in self.pitcher_usage:
            self.pitcher_usage[role] = PitcherUsage(role=role, pitcher=copy.deepcopy(self.staff[role]), entered_manually=manual)
        elif manual:
            self.pitcher_usage[role].entered_manually = True
        self.current_pitcher_role = role

    def pop_bench_player(self, name: str) -> Optional[dict]:
        for i, p in enumerate(self.bench):
            if p["name"] == name:
                return self.bench.pop(i)
        return None


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
    ended_in_tie: bool


class GameSimulator:
    def __init__(
        self,
        away_team: str,
        home_team: str,
        away_roster: dict,
        home_roster: dict,
        away_staff: dict,
        home_staff: dict,
        away_starter_role: str,
        home_starter_role: str,
        seed: Optional[int] = None,
        user_team: str = USER_TEAM,
    ):
        self.rng = random.Random(seed)
        self.user_team = user_team
        self.away = TeamGameState(away_team, copy.deepcopy(away_roster["starters"]), copy.deepcopy(away_roster["bench"]), copy.deepcopy(away_staff))
        self.home = TeamGameState(home_team, copy.deepcopy(home_roster["starters"]), copy.deepcopy(home_roster["bench"]), copy.deepcopy(home_staff))
        self.away.use_pitcher(away_starter_role)
        self.home.use_pitcher(home_starter_role)

        self.inning = 1
        self.half = "top"
        self.outs = 0
        self.bases: List[Optional[dict]] = [None, None, None]
        self.score = {"away": 0, "home": 0}
        self.hits = {"away": 0, "home": 0}
        self.errors = {"away": 0, "home": 0}
        self.line_score = {"away": [], "home": []}
        self.feed: List[str] = []
        self.batter_box: List[dict] = []
        self.pitcher_box: List[dict] = []
        self.finished = False

    def offense(self) -> TeamGameState:
        return self.away if self.half == "top" else self.home

    def defense(self) -> TeamGameState:
        return self.home if self.half == "top" else self.away

    def offense_key(self) -> str:
        return "away" if self.half == "top" else "home"

    def defense_key(self) -> str:
        return "home" if self.half == "top" else "away"

    def batting_team_name(self) -> str:
        return self.offense().team

    def fielding_team_name(self) -> str:
        return self.defense().team

    def current_batter_preview(self) -> dict:
        return self.offense().lineup[self.offense().next_batter_slot()]

    def current_pitcher_preview(self) -> dict:
        return self.defense().current_pitcher()

    def base_state(self) -> str:
        return "".join("1" if b else "0" for b in self.bases)

    def score_diff_for_team(self, team: str) -> int:
        if team == self.home.team:
            return self.score["home"] - self.score["away"]
        return self.score["away"] - self.score["home"]

    def force_bunt_next(self, team: str):
        if team == self.offense().team:
            self.offense().pending_force_bunt = True

    def apply_pinch_hitter(self, team: str, bench_name: str) -> bool:
        offense = self.offense()
        if offense.team != team:
            return False
        bench_player = offense.pop_bench_player(bench_name)
        if bench_player is None:
            return False
        slot = offense.next_batter_slot()
        bench_player["order"] = offense.lineup[slot]["order"]
        offense.lineup[slot] = bench_player
        self.feed.append(f"{team} 대타: {bench_name}")
        return True

    def apply_pinch_runner(self, team: str, base_number: int, bench_name: str) -> bool:
        offense = self.offense()
        if offense.team != team:
            return False
        idx = base_number - 1
        if idx not in (0, 1, 2) or self.bases[idx] is None:
            return False
        bench_player = offense.pop_bench_player(bench_name)
        if bench_player is None:
            return False
        replaced = self.bases[idx]
        bench_player["order"] = replaced["order"]
        for i, p in enumerate(offense.lineup):
            if p["name"] == replaced["name"] and p["order"] == replaced["order"]:
                offense.lineup[i] = bench_player
                break
        self.bases[idx] = bench_player
        self.feed.append(f"{team} 대주자: {bench_name} (대상 {replaced['name']})")
        return True

    def apply_manual_pitcher_change(self, team: str, role: str) -> bool:
        defense = self.defense()
        if defense.team != team or role not in defense.staff:
            return False
        defense.pending_manual_pitcher_role = role
        return True

    def play_to_end(self):
        while not self.finished:
            self.play_plate_appearance()

    def play_half_inning(self):
        current_half = (self.inning, self.half)
        guard = 0
        while not self.finished and (self.inning, self.half) == current_half and guard < 100:
            self.play_plate_appearance()
            guard += 1

    def play_plate_appearance(self):
        if self.finished:
            return
        self._apply_pending_pitcher_change_if_needed(pre_plate=True)

        offense = self.offense()
        defense = self.defense()
        batter = offense.next_batter()
        pitcher = defense.current_pitcher()

        if self.bases[0] is not None and self.bases[1] is None:
            runner = self.bases[0]
            steal = self._steal_attempt_result(runner)
            if steal is not None:
                if steal:
                    self.bases = [None, runner, self.bases[2]]
                    self._append_feed(f"{runner['name']} 도루 성공")
                    self._record_batter_event(offense.team, runner["name"], "도루", 0, {"sb": 1})
                else:
                    self.bases = [None, self.bases[1], self.bases[2]]
                    self.outs += 1
                    defense.pitcher_usage[defense.current_pitcher_role].outs_recorded += 1
                    self._append_feed(f"{runner['name']} 도루 실패")
                    self._record_batter_event(offense.team, runner["name"], "도루실패", 0, {"cs": 1})
                    self._maybe_replace_pitcher_mid_inning()
                    if self.outs >= 3:
                        self._end_half_inning()
                    return

        score_diff = self.score_diff_for_team(offense.team)
        if offense.pending_force_bunt or self._should_auto_bunt(self.inning, self.outs, score_diff, batter["order"]):
            offense.pending_force_bunt = False
            result = self._try_bunt(batter)
            self._apply_result(batter, result)
            return

        probs = combine_event_probs(batter, pitcher)
        roll = self.rng.random()

        if roll < probs["walk"]:
            new_bases, runs = self._advance_walk(self.bases, batter)
            self._apply_result(batter, {"event": "볼넷", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False, "hit_type": None})
            return
        roll -= probs["walk"]

        if roll < probs["single"]:
            new_bases, runs = self._advance_single(self.bases, batter)
            self._apply_result(batter, {"event": "안타", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False, "hit_type": "1B"})
            return
        roll -= probs["single"]

        if roll < probs["double"]:
            new_bases, runs = self._advance_double(self.bases, batter)
            self._apply_result(batter, {"event": "2루타", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False, "hit_type": "2B"})
            return
        roll -= probs["double"]

        if roll < probs["triple"]:
            new_bases, runs = self._advance_triple(self.bases, batter)
            self._apply_result(batter, {"event": "3루타", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False, "hit_type": "3B"})
            return
        roll -= probs["triple"]

        if roll < probs["homer"]:
            new_bases, runs = self._advance_homer(self.bases)
            self._apply_result(batter, {"event": "홈런", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": False, "hit_type": "HR"})
            return

        strikeout = self.rng.random() < probs["k_on_out"]
        if not strikeout:
            dp = self._try_double_play(batter, self.bases, self.outs)
            if dp is not None:
                self._apply_result(batter, dp)
                return
            sf = self._try_sac_fly(batter, self.bases, self.outs)
            if sf is not None:
                self._apply_result(batter, sf)
                return
            if self.rng.random() < (1.0 - FIELDING_CLEAN_RATE[self.fielding_team_name()]):
                new_bases, runs = self._advance_walk(self.bases, batter)
                self.errors[self.defense_key()] += 1
                self._apply_result(batter, {"event": "실책 출루", "bases": new_bases, "runs": runs, "outs": 0, "strikeout": False, "error": True, "hit_type": None})
                return

        self._apply_result(batter, {"event": "삼진" if strikeout else "범타", "bases": self.bases[:], "runs": 0, "outs": 1, "strikeout": strikeout, "error": False, "hit_type": None})

    def _append_feed(self, text: str):
        self.feed.append(f"{self.inning}회{'초' if self.half == 'top' else '말'} {self.offense().team} {text}")

    def _record_batter_event(self, team: str, name: str, event: str, rbi: int, stat_delta: dict):
        row = {
            "team": team, "name": name, "event": event, "inning": self.inning, "half": self.half,
            "PA": 0, "AB": 0, "H": 0, "1B": 0, "2B": 0, "3B": 0, "HR": 0, "BB": 0,
            "K": 0, "RBI": rbi, "SB": 0, "CS": 0, "SACB": 0, "SACF": 0,
        }
        row.update({k: row.get(k, 0) + v for k, v in stat_delta.items()})
        self.batter_box.append(row)

    def _apply_result(self, batter: dict, result: dict):
        offense = self.offense()
        defense = self.defense()
        off_key = self.offense_key()
        def_usage = defense.pitcher_usage[defense.current_pitcher_role]

        if result.get("hit_type") in {"1B", "2B", "3B", "HR"}:
            self.hits[off_key] += 1
            def_usage.hits_allowed += 1
        if result["event"] == "볼넷":
            def_usage.walks_allowed += 1
        if result.get("strikeout", False):
            def_usage.strikeouts += 1

        self.bases = result["bases"]
        self.score[off_key] += result["runs"]
        self.outs += result["outs"]
        def_usage.outs_recorded += result["outs"]
        def_usage.runs_allowed += result["runs"]

        rbi = result["runs"]
        event = result["event"]
        if event == "볼넷":
            self._record_batter_event(offense.team, batter["name"], event, rbi, {"PA": 1, "BB": 1})
        elif event == "안타":
            self._record_batter_event(offense.team, batter["name"], event, rbi, {"PA": 1, "AB": 1, "H": 1, "1B": 1})
        elif event == "2루타":
            self._record_batter_event(offense.team, batter["name"], event, rbi, {"PA": 1, "AB": 1, "H": 1, "2B": 1})
        elif event == "3루타":
            self._record_batter_event(offense.team, batter["name"], event, rbi, {"PA": 1, "AB": 1, "H": 1, "3B": 1})
        elif event == "홈런":
            self._record_batter_event(offense.team, batter["name"], event, rbi, {"PA": 1, "AB": 1, "H": 1, "HR": 1})
        elif event == "희생번트":
            self._record_batter_event(offense.team, batter["name"], event, 0, {"PA": 1, "SACB": 1})
        elif event == "희생플라이":
            self._record_batter_event(offense.team, batter["name"], event, rbi, {"PA": 1, "SACF": 1})
        elif event == "삼진":
            self._record_batter_event(offense.team, batter["name"], event, 0, {"PA": 1, "AB": 1, "K": 1})
        else:
            self._record_batter_event(offense.team, batter["name"], event, 0, {"PA": 1, "AB": 1})

        self._append_feed(f"{batter['name']} {event}" + (f" ({result['runs']}득점)" if result["runs"] else ""))
        self._maybe_replace_pitcher_mid_inning()

        if self._home_walkoff_now():
            self.finished = True
            self._append_feed("끝내기")
            self._finalize_line_score(force_home_current_half=True)
            self._build_pitcher_box()
            return

        if self.outs >= 3:
            self._end_half_inning()

    def _starter_limit_by_runs(self, runs_allowed: int) -> float:
        if runs_allowed <= 0:
            return 9.0
        if runs_allowed == 1:
            return 8.0
        if runs_allowed == 2:
            return 7.0
        if runs_allowed == 3:
            return 6.0
        if runs_allowed == 4:
            return 5.0
        if runs_allowed == 5:
            return 4.0
        return 0.0

    def _high_leverage_role(self, team_state: TeamGameState) -> Optional[str]:
        desired = HIGH_LEVERAGE_BY_INNING.get(self.inning)
        if desired is None or desired not in team_state.staff:
            return None
        lead = self.score_diff_for_team(team_state.team)
        if 1 <= lead <= 3:
            return desired
        return None

    def _apply_pending_pitcher_change_if_needed(self, pre_plate: bool = False):
        defense = self.defense()
        pending = defense.pending_manual_pitcher_role
        if pending and pending in defense.staff and pending != defense.current_pitcher_role:
            defense.use_pitcher(pending, manual=True)
            defense.pending_manual_pitcher_role = None
            self.feed.append(f"{defense.team} 감독 교체: {pending}")

        high = self._high_leverage_role(defense)
        if pre_plate and high and defense.current_pitcher_role != high and defense.current_pitcher_role != CLOSER_ROLE:
            defense.use_pitcher(high)
            self.feed.append(f"{defense.team} 자동 교체: {high}")

    def _maybe_replace_pitcher_mid_inning(self):
        defense = self.defense()
        role = defense.current_pitcher_role
        usage = defense.pitcher_usage[role]

        if role in STARTER_ROLES:
            limit = self._starter_limit_by_runs(usage.runs_allowed)
            if limit == 0.0 or usage.innings_pitched >= limit:
                nxt = self._first_followup_role(defense)
                if nxt:
                    defense.use_pitcher(nxt)
                    self.feed.append(f"{defense.team} 선발 강판 → {nxt}")
            return

        if role in CHASE_ROLES:
            if usage.runs_allowed >= 1 or usage.outs_recorded >= 3:
                nxt = self._next_chase_role(defense, role)
                if nxt:
                    defense.use_pitcher(nxt)
                    self.feed.append(f"{defense.team} 투수교체 → {nxt}")
            return

        if role in SETUP_ROLES:
            if usage.runs_allowed >= 1 or usage.outs_recorded >= 3:
                nxt = self._next_after_setup(defense, role)
                if nxt:
                    defense.use_pitcher(nxt)
                    self.feed.append(f"{defense.team} 투수교체 → {nxt}")
            return

        if role == CLOSER_ROLE:
            return

    def _first_followup_role(self, team_state: TeamGameState) -> Optional[str]:
        for role in CHASE_ROLES + SETUP_ROLES + [CLOSER_ROLE]:
            if role in team_state.staff:
                return role
        return None

    def _next_chase_role(self, team_state: TeamGameState, current_role: str) -> Optional[str]:
        order = CHASE_ROLES + SETUP_ROLES + [CLOSER_ROLE]
        idx = order.index(current_role)
        for role in order[idx + 1:]:
            if role in team_state.staff:
                return role
        return None

    def _next_after_setup(self, team_state: TeamGameState, current_role: str) -> Optional[str]:
        if current_role == "셋업맨2":
            if "셋업맨1" in team_state.staff:
                return "셋업맨1"
            if CLOSER_ROLE in team_state.staff:
                return CLOSER_ROLE
        elif current_role == "셋업맨1":
            for role in CHASE_ROLES:
                if role in team_state.staff:
                    return role
            if CLOSER_ROLE in team_state.staff:
                return CLOSER_ROLE
        return None

    def _advance_walk(self, bases: list, batter: dict) -> tuple[list, int]:
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

    def _advance_single(self, bases: list, batter: dict) -> tuple[list, int]:
        out = [None, None, None]
        runs = 0
        if bases[2]:
            runs += 1
        if bases[1]:
            if self.rng.random() < 0.5:
                runs += 1
            else:
                out[2] = bases[1]
        if bases[0]:
            out[1] = bases[0]
        out[0] = batter
        return out, runs

    def _advance_double(self, bases: list, batter: dict) -> tuple[list, int]:
        out = [None, None, None]
        runs = 0
        if bases[2]:
            runs += 1
        if bases[1]:
            runs += 1
        if bases[0]:
            if self.rng.random() < 0.5:
                runs += 1
            else:
                out[2] = bases[0]
        out[1] = batter
        return out, runs

    def _advance_triple(self, bases: list, batter: dict) -> tuple[list, int]:
        return [None, None, batter], sum(1 for x in bases if x)

    def _advance_homer(self, bases: list) -> tuple[list, int]:
        return [None, None, None], sum(1 for x in bases if x) + 1

    def _should_auto_bunt(self, inning: int, outs: int, score_diff: int, batter_order: int) -> bool:
        if inning not in (7, 8, 9):
            return False
        if outs != 0:
            return False
        if score_diff not in (-1, -2, -3):
            return False
        if batter_order in (3, 4, 5):
            return False
        return batter_order in (1, 2, 6, 7, 8, 9)

    def _try_bunt(self, batter: dict) -> dict:
        success = self.rng.random() < float(batter["sac_bunt_success_rate"])
        b = self.bases[:]
        if success:
            if b[1]:
                b[2] = b[1]
            if b[0]:
                b[1] = b[0]
            b[0] = None
            return {"event": "희생번트", "bases": b, "runs": 0, "outs": 1, "strikeout": False, "error": False}
        return {"event": "번트 실패", "bases": b, "runs": 0, "outs": 1, "strikeout": False, "error": False}

    def _try_double_play(self, batter: dict, bases: list, outs: int) -> Optional[dict]:
        if outs >= 2 or bases[0] is None:
            return None
        if self.rng.random() >= float(batter["gidp_rate"]):
            return None
        key = "".join("1" if x else "0" for x in bases)
        if key == "100":
            return {"event": "병살타", "bases": [None, None, None], "runs": 0, "outs": 2, "strikeout": False, "error": False}
        if key == "110":
            return {"event": "병살타", "bases": [None, None, bases[1]], "runs": 0, "outs": 2, "strikeout": False, "error": False}
        if key == "101":
            if self.rng.random() < 0.5:
                return {"event": "병살타", "bases": [None, bases[2], None], "runs": 0, "outs": 2, "strikeout": False, "error": False}
            return {"event": "병살타", "bases": [None, None, None], "runs": 1, "outs": 2, "strikeout": False, "error": False}
        if key == "111":
            roll = self.rng.randint(0, 2)
            if roll == 0:
                return {"event": "병살타", "bases": [None, bases[1], bases[2]], "runs": 0, "outs": 2, "strikeout": False, "error": False}
            if roll == 1:
                return {"event": "병살타", "bases": [None, bases[1], None], "runs": 1, "outs": 2, "strikeout": False, "error": False}
            return {"event": "병살타", "bases": [None, None, bases[2]], "runs": 1, "outs": 2, "strikeout": False, "error": False}
        return None

    def _try_sac_fly(self, batter: dict, bases: list, outs: int) -> Optional[dict]:
        if outs >= 2 or bases[2] is None:
            return None
        chance = clamp((100.0 - float(batter["pa_per_hr"])) / 100.0, 0.0, 0.95)
        if self.rng.random() >= chance:
            return None
        key = "".join("1" if x else "0" for x in bases)
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

    def _steal_attempt_result(self, runner: dict) -> Optional[bool]:
        denom = max(1, runner["h"] + runner["bb"] + runner["hbp"] - runner["doubles"] - runner["triples"] - runner["hr"])
        attempt_rate = min(MAX_STEAL_ATTEMPT_RATE, float(runner["st"]) / denom)
        if self.rng.random() >= attempt_rate:
            return None
        if int(runner["st"]) <= 0:
            return False
        success_rate = clamp(float(runner["sb"]) / max(int(runner["st"]), 1), 0.0, 1.0)
        return self.rng.random() < success_rate

    def _home_walkoff_now(self) -> bool:
        return self.half == "bottom" and self.inning >= 9 and self.score["home"] > self.score["away"]

    def _end_half_inning(self):
        key = self.offense_key()
        current_total = self.score[key]
        previous = sum(self.line_score[key])
        self.line_score[key].append(current_total - previous)

        if self.half == "top" and self.inning >= 9 and self.score["home"] > self.score["away"]:
            self.finished = True
            self._finalize_line_score()
            self._build_pitcher_box()
            return

        self.outs = 0
        self.bases = [None, None, None]
        if self.half == "top":
            self.half = "bottom"
        else:
            if self.inning >= MAX_EXTRA_INNING:
                self.finished = True
                self._finalize_line_score()
                self._build_pitcher_box()
                return
            if self.inning >= 9 and self.score["home"] != self.score["away"]:
                self.finished = True
                self._finalize_line_score()
                self._build_pitcher_box()
                return
            self.half = "top"
            self.inning += 1

    def _finalize_line_score(self, force_home_current_half: bool = False):
        if force_home_current_half and self.half == "bottom":
            previous = sum(self.line_score["home"])
            self.line_score["home"].append(self.score["home"] - previous)
        while len(self.line_score["away"]) < len(self.line_score["home"]):
            self.line_score["away"].append(0)
        while len(self.line_score["home"]) < len(self.line_score["away"]):
            self.line_score["home"].append(0)

    def _build_pitcher_box(self):
        self.pitcher_box = []
        for side in (self.away, self.home):
            for role, usage in side.pitcher_usage.items():
                self.pitcher_box.append({
                    "team": side.team,
                    "name": usage.pitcher["name"],
                    "role": role,
                    "outs": usage.outs_recorded,
                    "ip": usage.outs_recorded / 3.0,
                    "runs": usage.runs_allowed,
                    "hits": usage.hits_allowed,
                    "walks": usage.walks_allowed,
                    "strikeouts": usage.strikeouts,
                })

    def result(self) -> GameResult:
        if not self.finished:
            self.play_to_end()
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
            ended_in_tie=self.score["away"] == self.score["home"],
        )
