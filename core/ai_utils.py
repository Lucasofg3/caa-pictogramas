# ai_utils.py

from __future__ import annotations

import os
from typing import List, Dict


def ai_rewrite_for_caa(text: str) -> str:
    """
    Camada opcional.
    Mantida isolada para que o app continue funcionando sem chave/API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return text

    # Aqui você pode reinserir a integração da versão com IA.
    # Como estabilidade é a prioridade, o fallback é sempre devolver o texto original.
    return text


def maybe_enrich_tokens(tokens: List[Dict]) -> List[Dict]:
    # ponto de extensão futuro sem quebrar o app
    return tokens