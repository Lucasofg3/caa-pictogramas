from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Dict, List

try:
    import spacy
except Exception:
    spacy = None


@dataclass
class TokenData:
    text: str
    normalized: str
    lemma: str
    pos: str
    sintax_color: str
    emoji_fallback: str


PRONOUNS = {
    "eu", "tu", "ele", "ela", "nos", "nós", "vos", "vós", "eles", "elas",
    "me", "te", "se", "lhe", "lhes", "mim", "comigo", "contigo", "si"
}

ARTICLES = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas"
}

PREPOSITIONS = {
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "pra", "por", "com", "sem", "sobre", "entre", "ate", "até", "desde"
}

CONJUNCTIONS = {
    "e", "ou", "mas", "porque", "porem", "porém", "entao", "então", "que", "se"
}

COMMON_VERBS = {
    "ser", "estar", "ter", "haver", "ir", "vir", "fazer", "querer", "poder",
    "gostar", "comer", "beber", "ver", "dar", "pegar", "precisar", "ajudar",
    "brincar", "estudar", "ler", "escrever", "falar", "guardar", "escutar",
    "ouvir", "sentar", "abrir", "fechar", "levar", "colocar", "tirar", "deixar",
    "lavar", "andar", "correr", "buscar", "usar", "jogar", "dormir", "levantar",
    "vestir", "calcar", "arrumar", "organizar", "tomar", "comer", "beber"
}

# Formas comuns no imperativo, flexões e mapeamentos úteis para CAA
CUSTOM_LEMMA_MAP = {
    "escute": "escutar",
    "escutem": "escutar",
    "ouca": "ouvir",
    "oucam": "ouvir",
    "guarde": "guardar",
    "guardem": "guardar",
    "pegue": "pegar",
    "peguem": "pegar",
    "leve": "levar",
    "levem": "levar",
    "abra": "abrir",
    "abram": "abrir",
    "feche": "fechar",
    "fechem": "fechar",
    "coloque": "colocar",
    "coloquem": "colocar",
    "tire": "tirar",
    "tirem": "tirar",
    "deixe": "deixar",
    "deixem": "deixar",
    "sente": "sentar",
    "sentem": "sentar",
    "levante": "levantar",
    "levantem": "levantar",
    "lave": "lavar",
    "lavem": "lavar",
    "ande": "andar",
    "andem": "andar",
    "corra": "correr",
    "corram": "correr",
    "brinque": "brincar",
    "brinquem": "brincar",
    "use": "usar",
    "usem": "usar",
    "jogue": "jogar",
    "joguem": "jogar",
    "durma": "dormir",
    "durmam": "dormir",
    "vista": "vestir",
    "vistam": "vestir",
    "calce": "calcar",
    "calcem": "calcar",
    "arrume": "arrumar",
    "arrumem": "arrumar",
    "organize": "organizar",
    "organizem": "organizar",
    "tome": "tomar",
    "tomem": "tomar",
    "coma": "comer",
    "comam": "comer",
    "beba": "beber",
    "bebam": "beber",
    "professora": "professor",
    "professoras": "professor",
    "alunos": "aluno",
    "alunas": "aluna",
    "materiais": "material",
    "brinquedos": "brinquedo",
}

POS_STYLE = {
    "PRON": {"color": "#FFE8A3", "emoji": "👤"},
    "VERB": {"color": "#FFC2D1", "emoji": "⚙️"},
    "NOUN": {"color": "#BDE0FE", "emoji": "📘"},
    "ADJ": {"color": "#CDEAC0", "emoji": "✨"},
    "ADP": {"color": "#E9D5FF", "emoji": "🔗"},
    "CCONJ": {"color": "#FDE68A", "emoji": "➕"},
    "DET": {"color": "#FBCFE8", "emoji": "🏷️"},
    "ADV": {"color": "#D1FAE5", "emoji": "⏱️"},
    "PUNCT": {"color": "#E5E7EB", "emoji": "•"},
    "X": {"color": "#D1FAE5", "emoji": "🧩"},
}


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text or "")
        if unicodedata.category(ch) != "Mn"
    )


def normalize_word(text: str) -> str:
    clean = (text or "").strip().lower()
    clean = strip_accents(clean)
    return clean


@lru_cache(maxsize=1)
def get_nlp():
    if spacy is None:
        return None

    for model in ("pt_core_news_sm", "pt_core_news_md"):
        try:
            return spacy.load(model)
        except Exception:
            continue
    return None


def tokenize_text(text: str) -> List[str]:
    return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)


def mapped_lemma(token: str) -> str:
    norm = normalize_word(token)
    return CUSTOM_LEMMA_MAP.get(norm, norm)


def is_likely_imperative_or_finite_verb(token: str) -> bool:
    norm = normalize_word(token)
    lemma = mapped_lemma(token)

    if lemma in COMMON_VERBS and norm != lemma:
        return True

    verb_like_suffixes = (
        "ei", "ou", "am", "em", "ava", "avam", "ia", "iam",
        "arei", "era", "eram", "ira", "iram",
        "ando", "endo", "indo"
    )
    if norm.endswith(verb_like_suffixes):
        return True

    return False


def guess_pos(token: str) -> str:
    raw = token or ""
    norm = normalize_word(raw)
    lemma = mapped_lemma(raw)

    if not raw:
        return "X"

    if re.fullmatch(r"[^\w\s]", raw):
        return "PUNCT"

    if norm in PRONOUNS:
        return "PRON"
    if norm in ARTICLES:
        return "DET"
    if norm in PREPOSITIONS:
        return "ADP"
    if norm in CONJUNCTIONS:
        return "CCONJ"

    # Advérbios comuns relevantes em comandos/frases simples
    if norm in {"agora", "depois", "antes", "ontem", "hoje", "amanha", "amanhã"}:
        return "ADV"

    if lemma in COMMON_VERBS:
        return "VERB"

    if norm.endswith(("ar", "er", "ir")):
        return "VERB"

    if is_likely_imperative_or_finite_verb(raw):
        return "VERB"

    if norm.endswith(("vel", "nte", "oso", "osa", "ico", "ica")):
        return "ADJ"

    return "NOUN"


def color_for_pos(pos: str) -> str:
    return POS_STYLE.get(pos, POS_STYLE["X"])["color"]


def emoji_for_pos(pos: str) -> str:
    return POS_STYLE.get(pos, POS_STYLE["X"])["emoji"]


def lemma_word(token: str) -> str:
    norm = normalize_word(token)
    if not norm:
        return ""

    if norm in CUSTOM_LEMMA_MAP:
        return CUSTOM_LEMMA_MAP[norm]

    nlp = get_nlp()
    if nlp is not None:
        try:
            doc = nlp(token)
            if doc and doc[0].lemma_:
                lemma = normalize_word(doc[0].lemma_)
                if lemma:
                    return CUSTOM_LEMMA_MAP.get(lemma, lemma)
        except Exception:
            pass

    return norm


def analyze_text(text: str) -> List[Dict]:
    tokens = tokenize_text(text)
    if not tokens:
        return []

    nlp = get_nlp()
    results: List[TokenData] = []

    if nlp is not None:
        try:
            doc = nlp(text)
            for tok in doc:
                token_text = tok.text
                lemma = lemma_word(token_text)
                pos = tok.pos_ or guess_pos(token_text)

                heuristic_pos = guess_pos(token_text)
                mapped = mapped_lemma(token_text)

                if mapped in COMMON_VERBS:
                    pos = "VERB"
                elif pos not in POS_STYLE:
                    pos = heuristic_pos
                elif pos in {"NOUN", "ADJ", "X"} and heuristic_pos == "VERB":
                    pos = "VERB"

                results.append(
                    TokenData(
                        text=token_text,
                        normalized=normalize_word(token_text),
                        lemma=lemma,
                        pos=pos,
                        sintax_color=color_for_pos(pos),
                        emoji_fallback=emoji_for_pos(pos),
                    )
                )
            return [asdict(item) for item in results]
        except Exception:
            pass

    for token in tokens:
        pos = guess_pos(token)
        results.append(
            TokenData(
                text=token,
                normalized=normalize_word(token),
                lemma=lemma_word(token),
                pos=pos,
                sintax_color=color_for_pos(pos),
                emoji_fallback=emoji_for_pos(pos),
            )
        )

    return [asdict(item) for item in results]


def extract_keywords(text: str) -> List[str]:
    analyzed = analyze_text(text)
    keywords = []

    for item in analyzed:
        if item["pos"] in {"NOUN", "VERB", "ADJ", "ADV"} and item["text"].strip():
            lemma = item["lemma"]
            if lemma not in keywords:
                keywords.append(lemma)

    return keywords