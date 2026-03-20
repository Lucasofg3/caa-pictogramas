from __future__ import annotations

import unicodedata
from functools import lru_cache
from typing import Any, Dict, List, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REQUEST_TIMEOUT = 12
USER_AGENT = "CAA-Studio/4.0"

ARASAAC_API_BASES = [
    "https://api.arasaac.org/api",
]

ARASAAC_STATIC_BASE = "https://static.arasaac.org/pictograms"


def strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def singularize_pt(word: str) -> str:
    w = strip_accents((word or "").strip().lower())
    if len(w) <= 3:
        return w

    if w.endswith("oes"):
        return w[:-3] + "ao"
    if w.endswith("aes"):
        return w[:-3] + "ao"
    if w.endswith("ais"):
        return w[:-3] + "al"
    if w.endswith("eis"):
        return w[:-3] + "el"
    if w.endswith("is") and not w.endswith("ais") and not w.endswith("eis"):
        return w[:-2] + "il"
    if w.endswith("ns"):
        return w[:-2] + "m"
    if w.endswith("s"):
        return w[:-1]

    return w


def build_pictogram_url(pictogram_id: int | str) -> str:
    pictogram_id = str(pictogram_id).strip()
    return f"{ARASAAC_STATIC_BASE}/{pictogram_id}/{pictogram_id}_500.png"


def _request_json(url: str) -> Optional[Any]:
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        return None
    except ValueError:
        return None
    return None


@lru_cache(maxsize=1024)
def search_arasaac_pictogram(term: str, lang: str = "pt") -> Optional[str]:
    normalized = strip_accents((term or "").strip().lower())
    if not normalized:
        return None

    safe_term = requests.utils.quote(normalized)
    url = f"https://api.arasaac.org/api/pictograms/{lang}/search/{safe_term}"

    data = _request_json(url)

    if not isinstance(data, list) or not data:
        return None

    for item in data:
        if not isinstance(item, dict):
            continue

        pictogram_id = item.get("_id") or item.get("id")
        keywords = item.get("keywords", [])

        for kw in keywords:
            if kw.get("keyword", "").lower() == normalized:
                return build_pictogram_url(pictogram_id)

        if pictogram_id:
            return build_pictogram_url(pictogram_id)

    return None


def rank_candidates(word: str, lemma: Optional[str] = None) -> List[str]:
    base = strip_accents((word or "").strip().lower())
    lemma = strip_accents((lemma or "").strip().lower())

    if not base and not lemma:
        return []

    singular_base = singularize_pt(base) if base else ""
    singular_lemma = singularize_pt(lemma) if lemma else ""

    ordered = []
    for candidate in [
        lemma,
        singular_lemma,
        base,
        singular_base,
    ]:
        if candidate and candidate not in ordered:
            ordered.append(candidate)

    return ordered


@lru_cache(maxsize=1024)
def get_pictogram_url(word: str, lemma: str = "") -> Optional[str]:
    candidates = rank_candidates(word, lemma=lemma)
    if not candidates:
        return None

    for candidate in candidates:
        for lang in ("pt", "es", "en"):
            found = search_arasaac_pictogram(candidate, lang=lang)
            if found:
                return found

    return None


def fetch_pictogram(word: str, lemma: str = "") -> Dict[str, Optional[str]]:
    url = get_pictogram_url(word, lemma=lemma)
    return {
        "word": word,
        "lemma": lemma or word,
        "image_url": url,
    }

def search_arasaac_options(term: str, lang: str = "pt", limit: int = 8) -> List[Dict[str, str]]:
    normalized = strip_accents((term or "").strip().lower())
    if not normalized:
        return []

    safe_term = requests.utils.quote(normalized)
    url = f"https://api.arasaac.org/api/pictograms/{lang}/search/{safe_term}"

    data = _request_json(url)
    if not isinstance(data, list) or not data:
        return []

    options = []
    for item in data[:limit]:
        if not isinstance(item, dict):
            continue

        pictogram_id = item.get("_id") or item.get("id")
        if not pictogram_id:
            continue

        options.append(
            {
                "id": str(pictogram_id),
                "image_url": build_pictogram_url(pictogram_id),
                "label": term,
            }
        )

    return options