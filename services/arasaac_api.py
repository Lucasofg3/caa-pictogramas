from typing import Any, Dict, List
from urllib.parse import quote
import os

import requests
from dotenv import load_dotenv

load_dotenv()

ARASAAC_SEARCH_URL_TEMPLATE = os.getenv(
    "ARASAAC_SEARCH_URL_TEMPLATE",
    "https://api.arasaac.org/api/pictograms/{lang}/search/{query}",
)

ARASAAC_IMAGE_URL_TEMPLATE = os.getenv(
    "ARASAAC_IMAGE_URL_TEMPLATE",
    "https://api.arasaac.org/v1/pictograms/{id}",
)


def build_search_url(term: str, lang: str = "pt") -> str:
    return ARASAAC_SEARCH_URL_TEMPLATE.format(
        lang=lang,
        query=quote(term),
    )


def build_image_url(picto_id: int | str) -> str:
    return ARASAAC_IMAGE_URL_TEMPLATE.format(id=picto_id)


def fetch_pictograms(term: str, lang: str = "pt") -> List[Dict[str, Any]]:
    url = build_search_url(term, lang=lang)

    response = requests.get(url, timeout=20, verify=False)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        iterable = data
    elif isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            iterable = data["items"]
        elif "result" in data and isinstance(data["result"], list):
            iterable = data["result"]
        else:
            iterable = [data]
    else:
        iterable = []

    results: List[Dict[str, Any]] = []

    for item in iterable[:20]:
        picto_id = None
        label = term

        if isinstance(item, dict):
            picto_id = (
                item.get("_id")
                or item.get("id")
                or item.get("picto_id")
                or item.get("image_id")
            )

            keywords = item.get("keywords")
            if isinstance(keywords, list) and keywords:
                first_kw = keywords[0]
                if isinstance(first_kw, dict):
                    label = (
                        first_kw.get("keyword")
                        or first_kw.get("name")
                        or label
                    )
                elif isinstance(first_kw, str):
                    label = first_kw

            if not picto_id and "image" in item and isinstance(item["image"], dict):
                picto_id = item["image"].get("id")

        elif isinstance(item, (list, tuple)) and len(item) > 0:
            picto_id = item[0]

        if picto_id:
            results.append(
                {
                    "id": picto_id,
                    "label": label,
                    "image_url": build_image_url(picto_id),
                    "source_lang": lang,
                }
            )

    return results