import os
import json
from typing import List, Dict, Any

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH = os.path.join(_CURRENT_DIR, "seeded_projects.json")

DEFAULT_USER_10_IDS = [
    'N28000157', 'N28000122', 'N28000135', '702639', '701766',
    '702958', 'N28000058', '702637', '617225', 'N28000144'
]

DEFAULT_ADMIN_28_IDS = [
    '604795', 'N28000157', 'N28000122', 'N28000135', 'N30000002', 'N28000058',
    'N16000434', '702637', '617225', 'N28000144', 'N28000148', 'N28000086',
    '701415', 'N22000464', '705237', '82792908', 'PRJ_1913', 'N16000513',
    '701263', 'N22000463', 'N16000518', '617321', 'N22000406', '705728',
    '298178', '709798', '705429', '702668'
]

_CACHED_DATA = None

def _load_data() -> Dict[str, List[Dict[str, Any]]]:
    global _CACHED_DATA
    if _CACHED_DATA is None:
        if os.path.exists(_JSON_PATH):
            with open(_JSON_PATH, "r", encoding="utf-8") as f:
                _CACHED_DATA = json.load(f)
        else:
            _CACHED_DATA = {"user_projects": [], "admin_projects": []}
    return _CACHED_DATA

def get_seeded_admin_projects() -> List[Dict[str, Any]]:
    data = _load_data()
    return [dict(p) for p in data.get("admin_projects", [])]

def get_seeded_user_projects() -> List[Dict[str, Any]]:
    data = _load_data()
    return [dict(p) for p in data.get("user_projects", [])]

def get_all_seeded_projects() -> List[Dict[str, Any]]:
    data = _load_data()
    all_p = []
    seen = set()
    for p in data.get("admin_projects", []) + data.get("user_projects", []):
        pid = p.get("project_id")
        if pid and pid not in seen:
            seen.add(pid)
            all_p.append(dict(p))
    return all_p
