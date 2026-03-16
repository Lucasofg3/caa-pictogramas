import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TEMPLATES_FILE = DATA_DIR / "templates.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
SEARCH_HISTORY_FILE = DATA_DIR / "search_history.json"


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, payload: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_templates() -> List[Dict[str, Any]]:
    return _read_json(TEMPLATES_FILE, [])


def save_template(template: Dict[str, Any]):
    templates = load_templates()
    templates.append(template)
    _write_json(TEMPLATES_FILE, templates)


def load_favorites() -> List[Dict[str, Any]]:
    return _read_json(FAVORITES_FILE, [])


def save_favorite(item: Dict[str, Any]):
    favorites = load_favorites()
    existing_ids = {fav.get("id") for fav in favorites}
    if item.get("id") not in existing_ids:
        favorites.append(item)
        _write_json(FAVORITES_FILE, favorites)


def remove_favorite(picto_id: int | str):
    favorites = load_favorites()
    favorites = [fav for fav in favorites if fav.get("id") != picto_id]
    _write_json(FAVORITES_FILE, favorites)


def load_search_history() -> List[Dict[str, Any]]:
    return _read_json(SEARCH_HISTORY_FILE, [])


def add_search_history(record: Dict[str, Any]):
    history = load_search_history()
    history.insert(0, record)
    history = history[:200]
    _write_json(SEARCH_HISTORY_FILE, history)