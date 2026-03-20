import re
import unicodedata
from typing import Dict, List, Optional

import requests

try:
    import spacy
except Exception:
    spacy = None


# =========================================================
# CORES SINTÁTICAS
# =========================================================
SYNTAX_COLORS = {
    "substantivo": {
        "label": "Substantivo",
        "bg": "#F4C542",
        "text": "#3A2B00",
        "desc": "Pessoas, lugares e objetos",
    },
    "verbo": {
        "label": "Verbo",
        "bg": "#4CD964",
        "text": "#083B12",
        "desc": "Ações ou estados",
    },
    "adjetivo": {
        "label": "Adjetivo",
        "bg": "#5B8DEF",
        "text": "#FFFFFF",
        "desc": "Características ou qualidades",
    },
    "social": {
        "label": "Social",
        "bg": "#FF9500",
        "text": "#FFFFFF",
        "desc": "Saudações e interjeições",
    },
    "pronome": {
        "label": "Pronome",
        "bg": "#E9C7E8",
        "text": "#6A2C70",
        "desc": "Pronomes",
    },
    "artigo": {
        "label": "Artigo",
        "bg": "#F5F5F5",
        "text": "#444444",
        "desc": "Artigos",
    },
    "preposicao": {
        "label": "Preposição",
        "bg": "#AF6AD8",
        "text": "#FFFFFF",
        "desc": "Preposições",
    },
    "conjuncao": {
        "label": "Conjunção",
        "bg": "#9C7A17",
        "text": "#FFFFFF",
        "desc": "Conjunções",
    },
    "adverbio": {
        "label": "Advérbio",
        "bg": "#BDBDBD",
        "text": "#2F2F2F",
        "desc": "Advérbios",
    },
    "desconhecido": {
        "label": "Palavra",
        "bg": "#EAEAEA",
        "text": "#333333",
        "desc": "Classificação não identificada",
    },
}


# =========================================================
# LÉXICO BASE
# =========================================================
PRONOMES = {
    "eu", "tu", "ele", "ela", "nos", "nós", "vos", "voces", "vocês", "voce", "você",
    "eles", "elas", "me", "mim", "te", "ti", "se", "si", "lhe", "lhes",
    "meu", "minha", "meus", "minhas", "seu", "sua", "seus", "suas",
    "nosso", "nossa", "nossos", "nossas", "isso", "isto", "aquilo",
    "este", "esta", "esse", "essa", "aquele", "aquela"
}

ARTIGOS = {"o", "a", "os", "as", "um", "uma", "uns", "umas"}

PREPOSICOES = {
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "pra", "por", "com", "sem", "sob", "sobre", "entre",
    "ate", "até", "contra", "desde", "perante", "tras", "trás", "ante",
    "apos", "após"
}

CONJUNCOES = {
    "e", "ou", "mas", "porque", "pois", "quando", "embora", "se",
    "como", "que", "porém", "todavia", "contudo", "entretanto", "nem"
}

ADVERBIOS = {
    "nao", "não", "sim", "aqui", "ali", "la", "lá", "agora", "depois",
    "antes", "sempre", "nunca", "muito", "pouco", "bem", "mal", "ontem",
    "hoje", "amanha", "amanhã"
}

SOCIAIS = {
    "oi", "olá", "ola", "tchau", "obrigado", "obrigada", "desculpa",
    "desculpe", "socorro"
}

ADJETIVOS_COMUNS = {
    "feliz", "triste", "grande", "pequeno", "pequena", "bom", "boa",
    "ruim", "cansado", "cansada", "frio", "quente", "rápido", "rapido",
    "lento", "forte", "fraco", "fraca", "bonito", "bonita", "alto", "alta",
    "baixo", "baixa"
}

VERBOS_BASE = {
    "ser", "estar", "ter", "ir", "vir", "querer", "precisar", "comer", "beber",
    "brincar", "ajudar", "gostar", "sentir", "ver", "olhar", "falar", "pedir",
    "andar", "correr", "dormir", "estudar", "escrever", "ler", "abrir", "fechar",
    "ligar", "desligar", "tomar", "lavar", "usar", "jogar", "escutar", "ouvir",
    "dar", "pegar", "colocar", "tirar", "amar", "pensar", "fazer", "trabalhar",
    "esperar", "comprar", "voltar", "sair", "entrar", "parar", "iniciar", "terminar"
}

COMMON_VERB_FORMS = {
    "quero": "querer",
    "quer": "querer",
    "queria": "querer",
    "preciso": "precisar",
    "precisa": "precisar",
    "gosto": "gostar",
    "gosta": "gostar",
    "comendo": "comer",
    "come": "comer",
    "comi": "comer",
    "bebendo": "beber",
    "bebe": "beber",
    "bebi": "beber",
    "brincando": "brincar",
    "brinca": "brincar",
    "falando": "falar",
    "fala": "falar",
    "vendo": "ver",
    "ve": "ver",
    "vê": "ver",
    "olhando": "olhar",
    "olha": "olhar",
    "sentindo": "sentir",
    "sente": "sentir",
    "correndo": "correr",
    "corre": "correr",
    "dormindo": "dormir",
    "dorme": "dormir",
    "estudando": "estudar",
    "estuda": "estudar",
    "lendo": "ler",
    "le": "ler",
    "lê": "ler",
    "escrevendo": "escrever",
    "escreve": "escrever",
    "abrindo": "abrir",
    "abre": "abrir",
    "fechando": "fechar",
    "fecha": "fechar",
    "ajudando": "ajudar",
    "ajuda": "ajudar",
    "usando": "usar",
    "usa": "usar",
    "tomando": "tomar",
    "toma": "tomar",
    "lavando": "lavar",
    "lava": "lavar",
    "indo": "ir",
    "vai": "ir",
    "estou": "estar",
    "esta": "estar",
    "está": "estar",
    "to": "estar",
    "tô": "estar",
    "sou": "ser",
    "é": "ser",
    "eh": "ser",
    "tenho": "ter",
    "tem": "ter",
    "faz": "fazer",
    "fazendo": "fazer",
}


# =========================================================
# SPACY
# =========================================================
_NLP = None


def get_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP

    if spacy is None:
        _NLP = False
        return _NLP

    try:
        _NLP = spacy.load("pt_core_news_sm")
    except Exception:
        _NLP = False

    return _NLP


# =========================================================
# TEXTO
# =========================================================
def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[,;:.!?/\\\\|()\\[\\]{}\"“”'’`´]", " ", text)
    text = re.sub(r"[^a-zA-ZÀ-ÿ0-9\\s-]", " ", text)
    return normalize_spaces(text)


def split_phrase(text: str) -> List[str]:
    return [tok for tok in text.split() if tok.strip()]


def looks_like_infinitive(word: str) -> bool:
    w = strip_accents(word.lower())
    return w.endswith(("ar", "er", "ir"))


def lemma_word(word: str) -> str:
    base = word.lower().strip()
    if base in COMMON_VERB_FORMS:
        return COMMON_VERB_FORMS[base]

    nlp = get_nlp()
    if nlp:
        try:
            doc = nlp(base)
            if doc and len(doc) > 0:
                lemma = doc[0].lemma_.lower().strip()
                if lemma:
                    return lemma
        except Exception:
            pass

    return base


def classify_word(word: str) -> str:
    w = word.lower().strip()
    wa = strip_accents(w)

    if w in ARTIGOS or wa in ARTIGOS:
        return "artigo"
    if w in PRONOMES or wa in PRONOMES:
        return "pronome"
    if w in PREPOSICOES or wa in PREPOSICOES:
        return "preposicao"
    if w in CONJUNCOES or wa in CONJUNCOES:
        return "conjuncao"
    if w in ADVERBIOS or wa in ADVERBIOS:
        return "adverbio"
    if w in ADJETIVOS_COMUNS or wa in ADJETIVOS_COMUNS:
        return "adjetivo"
    if w in SOCIAIS or wa in {strip_accents(x) for x in SOCIAIS}:
        return "social"
    if w in VERBOS_BASE or wa in {strip_accents(v) for v in VERBOS_BASE}:
        return "verbo"
    if wa in COMMON_VERB_FORMS:
        return "verbo"

    nlp = get_nlp()
    if nlp:
        try:
            doc = nlp(w)
            if doc and len(doc) > 0:
                pos = doc[0].pos_
                if pos == "VERB" or pos == "AUX":
                    return "verbo"
                if pos == "ADJ":
                    return "adjetivo"
                if pos == "ADV":
                    return "adverbio"
                if pos == "PRON":
                    return "pronome"
                if pos == "ADP":
                    return "preposicao"
                if pos == "CCONJ" or pos == "SCONJ":
                    return "conjuncao"
                if pos == "DET":
                    return "artigo"
                if pos == "NOUN" or pos == "PROPN":
                    return "substantivo"
        except Exception:
            pass

    if looks_like_infinitive(w):
        return "verbo"

    return "substantivo"


def simplify_phrase_rules(text: str) -> str:
    text = clean_text(text)
    tokens = split_phrase(text)

    simplified = []
    for tok in tokens:
        lemma = lemma_word(tok)

        # remove algumas cortesias/excessos muito comuns
        if lemma in {"por", "favor"}:
            continue
        if lemma in {"gostaria"}:
            lemma = "querer"

        if classify_word(lemma) == "verbo" and not looks_like_infinitive(lemma):
            converted = COMMON_VERB_FORMS.get(lemma, lemma)
            lemma = converted

        simplified.append(lemma)

    simplified = [t for t in simplified if t]
    return normalize_spaces(" ".join(simplified))


def generate_guidance(raw_text: str, final_text: str, words: List[str]) -> List[str]:
    messages = []

    if "," in raw_text:
        messages.append("Vírgulas foram removidas para deixar a mensagem mais direta.")

    if clean_text(raw_text) != final_text:
        messages.append("A frase foi simplificada para favorecer uma comunicação mais clara e visual.")

    if len(words) > 8:
        messages.append("Frases mais curtas costumam funcionar melhor em CAA. Considere dividir a mensagem.")

    verbos = [w for w in words if classify_word(w) == "verbo"]
    if any(not looks_like_infinitive(v) for v in verbos):
        messages.append("Sempre que possível, use verbos no infinitivo.")

    return messages


def build_alternative_suggestions(final_phrase: str) -> List[str]:
    words = split_phrase(final_phrase)
    if not words:
        return []

    suggestions = [final_phrase]

    joined = " ".join(words)
    if "querer" in words and "água" in words:
        suggestions.append("eu querer beber água")
    if "precisar" in words and "banheiro" in words:
        suggestions.append("eu querer ir banheiro")
    if "sentir" in words and "dor" in words:
        suggestions.append("eu sentir dor agora")
    if len(words) >= 4:
        suggestions.append(" ".join(words[:4]))

    # remove duplicadas preservando ordem
    seen = set()
    result = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            result.append(s)

    return result[:4]


# =========================================================
# ARASAAC
# =========================================================
def search_arasaac_pictogram(term: str) -> Optional[str]:
    safe_term = requests.utils.quote(term.lower())
    endpoints = [
        f"https://api.arasaac.org/api/pictograms/pt/search/{safe_term}",
        f"https://api.arasaac.org/api/pictograms/br/search/{safe_term}",
        f"https://api.arasaac.org/api/pictograms/search/{safe_term}",
    ]

    for url in endpoints:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and "_id" in data[0]:
                    pict_id = data[0]["_id"]
                    return f"https://static.arasaac.org/pictograms/{pict_id}/{pict_id}_500.png"
        except Exception:
            continue

    return None


def get_pictogram_url(word: str) -> Optional[str]:
    direct = search_arasaac_pictogram(word)
    if direct:
        return direct

    no_accent = strip_accents(word)
    if no_accent != word:
        return search_arasaac_pictogram(no_accent)

    lemma = lemma_word(word)
    if lemma != word:
        return search_arasaac_pictogram(lemma)

    return None