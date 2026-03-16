import re
from typing import List

STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos",
    "e", "em", "no", "na", "nos", "nas", "um", "uma", "uns", "umas",
    "para", "por", "com", "sem", "que", "se", "ao", "aos", "à", "às",
    "depois", "antes", "muito", "mais", "menos", "ser", "estar",
    "foi", "são", "é", "era", "como", "ou", "dos", "das", "lhe", "lhes",
    "me", "te", "nos", "vos", "isso", "isto", "aquele", "aquela", "aquilo"
}

CUSTOM_MAP = {
    "escute": "escutar",
    "ouça": "ouvir",
    "guarde": "guardar",
    "sente": "sentar",
    "sente-se": "sentar",
    "professora": "professor",
    "professoras": "professor",
    "alunos": "aluno",
    "alunas": "aluno",
    "materiais": "material",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\sáàâãéèêíïóôõöúçñ-]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text



def extract_keywords(text: str) -> List[str]:
    text = normalize_text(text)
    tokens = text.split()

    filtered = []
    for token in tokens:
        token = CUSTOM_MAP.get(token, token)
        if len(token) <= 2:
            continue
        if token in STOPWORDS:
            continue
        filtered.append(token)

    unique = []
    seen = set()
    for token in filtered:
        if token not in seen:
            seen.add(token)
            unique.append(token)

    return unique
