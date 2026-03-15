TEAM_ALIASES = {
    "KIA": "KIA",
    "기아": "KIA",
    "두산": "두산",
    "롯데": "롯데",
    "삼성": "삼성",
    "한화": "한화",
    "KT": "KT",
    "kt": "KT",
    "NC": "NC",
    "SSG": "SSG",
    "키움": "키움",
    "LG": "LG",
    "WO": "키움",
    "OB": "두산",
    "LT": "롯데",
    "SS": "삼성",
    "SK": "SSG",
    "HH": "한화",
}

TEAMS = ["KIA", "두산", "롯데", "삼성", "한화", "KT", "NC", "SSG", "키움", "LG"]
USER_TEAM = "한화"

FIELDING_CLEAN_RATE = {
    "삼성": 0.984,
    "LG": 0.983,
    "두산": 0.977,
    "SSG": 0.980,
    "한화": 0.984,
    "KT": 0.981,
    "NC": 0.978,
    "KIA": 0.977,
    "롯데": 0.979,
    "키움": 0.977,
}

STARTER_ROLES = ["선발1", "선발2", "선발3", "선발4", "선발5"]
CHASE_ROLES = ["추격조1", "추격조2", "추격조3", "추격조4", "추격조5"]
SETUP_ROLES = ["셋업맨2", "셋업맨1"]
CLOSER_ROLE = "마무리"
PITCHER_ROLE_ORDER = STARTER_ROLES + CHASE_ROLES + SETUP_ROLES + [CLOSER_ROLE]

HIGH_LEVERAGE_BY_INNING = {
    7: "셋업맨2",
    8: "셋업맨1",
    9: "마무리",
}

LEAGUE_BASE_ONBASE = 0.340
LEAGUE_BASE_K = 0.22
MAX_STEAL_ATTEMPT_RATE = 0.36
MAX_EXTRA_INNING = 11
MANUAL_CHASE_CHANGES_PER_GAME = 2
MANUAL_SETUP_CHANGES_PER_MONTH = 4
