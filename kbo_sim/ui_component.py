from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit.components.v1 as components

_COMPONENT_NAME = "hanwha_dashboard"
_DEV_URL = os.getenv("HANWHA_COMPONENT_URL", "http://localhost:5173")
_DEV_MODE = os.getenv("HANWHA_COMPONENT_DEV", "0") == "1"
_DIST_DIR = Path(__file__).resolve().parent / "frontend" / "dist"

_component_func = None

if _DEV_MODE:
    _component_func = components.declare_component(
        _COMPONENT_NAME,
        url=_DEV_URL,
    )
elif _DIST_DIR.exists():
    _component_func = components.declare_component(
        _COMPONENT_NAME,
        path=str(_DIST_DIR),
    )


def component_is_ready() -> bool:
    return _component_func is not None


def render_hanwha_dashboard_component(
    app_payload: Dict[str, Any],
    key: str = "hanwha_dashboard_component",
    default: Optional[dict] = None,
) -> Optional[dict]:
    if _component_func is None:
        return None

    return _component_func(
        appPayload=app_payload,
        key=key,
        default=default,
    )
