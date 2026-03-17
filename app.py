import os
import json
import re
import tempfile
import unicodedata
import textwrap
import base64
from copy import deepcopy
from typing import List, Dict, Any
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF

from services.arasaac_api import fetch_pictograms
from utils.export import generate_board_html
from utils.storage import (
    load_templates,
    save_template,
    load_favorites,
    save_favorite,
    remove_favorite,
    load_search_history,
    add_search_history,
)

load_dotenv()
APP_TITLE = os.getenv("APP_TITLE", "Gerador de Materiais com Pictogramas")

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main > div {
        padding-top: 1.2rem;
        padding-bottom: 2.2rem;
    }

    .block-container {
        max-width: 1220px;
        padding-top: 0.8rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    .hero-wrap {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 50%, #0EA5E9 100%);
        color: white;
        padding: 1.8rem 2rem;
        border-radius: 28px;
        box-shadow: 0 18px 45px rgba(29, 78, 216, 0.24);
        margin-bottom: 1rem;
    }

    .hero-logo {
        width: 78px;
        height: 78px;
        flex-shrink: 0;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 22px;
        padding: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(6px);
    }

    .hero-logo img {
        width: 100%;
        height: auto;
    }

    .hero-content {
        flex: 1;
    }

    .hero-title {
        font-size: 2.15rem;
        font-weight: 800;
        line-height: 1.05;
        margin-bottom: 0.45rem;
    }

    .hero-subtitle {
        font-size: 1rem;
        line-height: 1.5;
        max-width: 820px;
        opacity: 0.96;
    }

    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.95rem;
    }

    .hero-pill {
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.24);
        color: white;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin-bottom: 1rem;
    }

    .kpi-card {
        background: white;
        border: 1px solid #D8E5FF;
        border-radius: 22px;
        padding: 1rem 1rem 0.95rem 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }

    .kpi-label {
        color: #64748B;
        font-size: 0.84rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        color: #0F172A;
        font-size: 1.4rem;
        font-weight: 800;
        line-height: 1.05;
    }

    .kpi-desc {
        color: #64748B;
        font-size: 0.84rem;
        margin-top: 0.28rem;
    }

    .section-card {
        background: #ffffff;
        border: 1px solid #DCE8FF;
        border-radius: 24px;
        padding: 1.25rem 1.25rem 1rem 1.25rem;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.12rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.25rem;
    }

    .section-subtitle {
        font-size: 0.94rem;
        color: #475569;
        margin-bottom: 0.25rem;
    }

    .info-banner {
        background: linear-gradient(90deg, #EFF6FF 0%, #F8FBFF 100%);
        border: 1px solid #BFDBFE;
        border-radius: 18px;
        padding: 0.95rem 1rem;
        color: #1E3A8A;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }

    .segment-chip {
        display: inline-block;
        background: #DBEAFE;
        color: #1D4ED8;
        border-radius: 999px;
        padding: 0.26rem 0.62rem;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }

    .preview-panel {
        background: white;
        border: 1px solid #DCE8FF;
        border-radius: 22px;
        padding: 1rem;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);
    }

    .export-panel {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
        border: 1px solid #DCE8FF;
        border-radius: 22px;
        padding: 1rem;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);
    }

    .small-muted {
        color: #64748B;
        font-size: 0.92rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 14px !important;
        border: 1px solid #CFE0FF !important;
        min-height: 2.85rem !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 14px rgba(37, 99, 235, 0.06);
    }

    div[data-testid="stDownloadButton"] > button {
        border-radius: 14px !important;
        min-height: 2.85rem !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 14px rgba(37, 99, 235, 0.06);
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
        border-radius: 14px !important;
    }

    div[data-testid="stExpander"] details {
        border-radius: 18px !important;
        border: 1px solid #DCE8FF !important;
        background: white !important;
    }

    @media (max-width: 992px) {
        .kpi-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 768px) {
        .hero-wrap {
            flex-direction: column;
            align-items: flex-start;
            padding: 1.3rem 1.15rem;
            border-radius: 20px;
        }

        .hero-title {
            font-size: 1.7rem;
        }

        .hero-subtitle {
            font-size: 0.95rem;
        }

        .hero-logo {
            width: 64px;
            height: 64px;
            border-radius: 18px;
        }

        .kpi-grid {
            grid-template-columns: 1fr;
        }

        .section-card,
        .preview-panel,
        .export-panel {
            border-radius: 18px;
            padding: 0.95rem;
        }
    }
</style>
""", unsafe_allow_html=True)

STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos",
    "e", "em", "no", "na", "nos", "nas", "um", "uma", "uns", "umas",
    "para", "por", "com", "sem", "que", "se", "ao", "aos", "à", "às",
    "depois", "antes", "muito", "mais", "menos", "ser", "estar",
    "foi", "são", "é", "era", "como", "lhe", "lhes", "me", "te",
    "eu", "tu", "ele", "ela", "eles", "elas", "isso", "isto", "aquilo",
    "este", "esta", "esse", "essa"
}

CUSTOM_MAP = {
    "escute": "escutar",
    "ouça": "escutar",
    "guarde": "guardar",
    "pegue": "pegar",
    "professora": "professor",
    "professoras": "professor",
    "professores": "professor",
    "sente": "sentar",
    "sente-se": "sentar",
    "sentar-se": "sentar",
    "leia": "ler",
    "marque": "marcar",
    "entregue": "entregar",
    "volte": "voltar",
    "brinque": "brincar",
    "lave": "lavar",
    "mãos": "mão",
}

KNOWN_PHRASES = [
    "lavar as mãos",
    "guardar material",
    "hora do recreio",
    "hora do lanche",
    "fila do lanche",
    "fila do recreio",
    "pegar o caderno",
    "sentar na cadeira",
    "sentar em roda",
    "voltar para a sala",
]

SEARCH_HINTS = {
    "sentar": {"en": ["sit", "sit down"], "es": ["sentarse", "sentar"]},
    "lavar": {"en": ["wash"], "es": ["lavar"]},
    "mão": {"en": ["hand"], "es": ["mano"]},
    "material": {"en": ["material", "school material"], "es": ["material"]},
    "professor": {"en": ["teacher"], "es": ["profesor"]},
    "recreio": {"en": ["recess", "break"], "es": ["recreo"]},
    "roda": {"en": ["circle"], "es": ["círculo", "rueda"]},
    "cadeira": {"en": ["chair"], "es": ["silla"]},
    "caderno": {"en": ["notebook"], "es": ["cuaderno"]},
    "ler": {"en": ["read"], "es": ["leer"]},
    "marcar": {"en": ["mark"], "es": ["marcar"]},
    "entregar": {"en": ["deliver", "hand in"], "es": ["entregar"]},
    "voltar": {"en": ["return", "go back"], "es": ["volver"]},
    "brincar": {"en": ["play"], "es": ["jugar"]},
    "guardar": {"en": ["put away", "store"], "es": ["guardar"]},
    "fila": {"en": ["line", "queue"], "es": ["fila"]},
    "lanche": {"en": ["snack"], "es": ["merienda"]},
    "sala": {"en": ["classroom", "room"], "es": ["aula", "sala"]},
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def split_text_preserving_punctuation(text: str) -> List[str]:
    return re.findall(r"\w+(?:-\w+)?|[^\w\s]", text, flags=re.UNICODE)


def is_punctuation(token: str) -> bool:
    return bool(re.fullmatch(r"[^\w\s]", token))


def normalize_token(token: str) -> str:
    cleaned = token.lower().strip()
    cleaned = re.sub(r"[^\wáàâãéèêíïóôõöúçñ-]", "", cleaned, flags=re.IGNORECASE)
    cleaned = CUSTOM_MAP.get(cleaned, cleaned)
    return cleaned


def should_search_pictogram(token: str) -> bool:
    if not token:
        return False
    if is_punctuation(token):
        return False
    normalized = normalize_token(token)
    if len(normalized) <= 2:
        return False
    if normalized in STOPWORDS:
        return False
    return True


def get_language_hints(pt_term: str) -> Dict[str, List[str]]:
    base = SEARCH_HINTS.get(pt_term, {})
    return {
        "en": base.get("en", []),
        "es": base.get("es", []),
    }


def build_segments(text: str) -> List[Dict[str, Any]]:
    raw_tokens = split_text_preserving_punctuation(text)
    normalized_tokens = [normalize_token(tok) if not is_punctuation(tok) else tok for tok in raw_tokens]

    segments: List[Dict[str, Any]] = []
    i = 0

    while i < len(raw_tokens):
        matched_phrase = None
        matched_len = 0

        for size in [4, 3, 2]:
            if i + size <= len(raw_tokens):
                candidate_raw = raw_tokens[i:i + size]
                if any(is_punctuation(tok) for tok in candidate_raw):
                    continue
                candidate_norm = " ".join(normalized_tokens[i:i + size]).strip()
                if candidate_norm in KNOWN_PHRASES:
                    matched_phrase = " ".join(raw_tokens[i:i + size])
                    matched_len = size
                    break

        if matched_phrase:
            pt_term = normalize_text(" ".join(normalized_tokens[i:i + matched_len]))
            hints = get_language_hints(pt_term)
            segments.append({
                "original_text": matched_phrase,
                "display_text": matched_phrase,
                "segment_type": "text_with_pictogram",
                "search_terms": {
                    "pt": pt_term,
                    "en": hints["en"][0] if hints["en"] else "",
                    "es": hints["es"][0] if hints["es"] else "",
                },
                "active_languages": ["pt"],
                "pictogram_options": [],
                "selected_pictogram_ids": [],
                "selected_pictograms": [],
                "segment_mode": "Texto + pictograma",
                "fetch_error": "",
            })
            i += matched_len
            continue

        token = raw_tokens[i]

        if is_punctuation(token):
            segments.append({
                "original_text": token,
                "display_text": token,
                "segment_type": "text",
                "search_terms": {"pt": "", "en": "", "es": ""},
                "active_languages": [],
                "pictogram_options": [],
                "selected_pictogram_ids": [],
                "selected_pictograms": [],
                "segment_mode": "Texto apenas",
                "fetch_error": "",
            })
            i += 1
            continue

        normalized = normalize_token(token)
        if should_search_pictogram(token):
            hints = get_language_hints(normalized)
            segments.append({
                "original_text": token,
                "display_text": token,
                "segment_type": "text_with_pictogram",
                "search_terms": {
                    "pt": normalized,
                    "en": hints["en"][0] if hints["en"] else "",
                    "es": hints["es"][0] if hints["es"] else "",
                },
                "active_languages": ["pt"],
                "pictogram_options": [],
                "selected_pictogram_ids": [],
                "selected_pictograms": [],
                "segment_mode": "Texto + pictograma",
                "fetch_error": "",
            })
        else:
            segments.append({
                "original_text": token,
                "display_text": token,
                "segment_type": "text",
                "search_terms": {"pt": "", "en": "", "es": ""},
                "active_languages": [],
                "pictogram_options": [],
                "selected_pictogram_ids": [],
                "selected_pictograms": [],
                "segment_mode": "Texto apenas",
                "fetch_error": "",
            })

        i += 1

    return segments


def merge_pictogram_results(results_by_lang: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    merged = []
    seen_ids = set()

    for lang, items in results_by_lang.items():
        for item in items:
            picto_id = item.get("id")
            if picto_id in seen_ids:
                continue
            new_item = dict(item)
            new_item["source_lang"] = lang
            merged.append(new_item)
            seen_ids.add(picto_id)

    return merged


def fetch_options_for_segment(seg: Dict[str, Any]) -> Dict[str, Any]:
    if seg["segment_type"] != "text_with_pictogram":
        seg["pictogram_options"] = []
        seg["fetch_error"] = ""
        return seg

    terms = seg.get("search_terms", {})
    active_languages = seg.get("active_languages", ["pt"])

    results_by_lang: Dict[str, List[Dict[str, Any]]] = {}
    errors = []

    for lang in active_languages:
        term = terms.get(lang, "").strip()
        if not term:
            continue
        try:
            results_by_lang[lang] = fetch_pictograms(term, lang=lang)
            add_search_history({
                "term": term,
                "lang": lang,
                "segment_text": seg.get("display_text", ""),
            })
        except Exception as exc:
            results_by_lang[lang] = []
            errors.append(f"{lang}: {exc}")

    seg["pictogram_options"] = merge_pictogram_results(results_by_lang)
    seg["fetch_error"] = " | ".join(errors)
    seg["selected_pictograms"] = []
    seg["selected_pictogram_ids"] = []

    return seg


def fetch_options_for_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [fetch_options_for_segment(dict(seg)) for seg in segments]


def segment_mode_to_flags(mode: str) -> tuple[bool, bool]:
    if mode == "Texto apenas":
        return True, True
    if mode == "Texto + pictograma":
        return True, True
    if mode == "Pictograma apenas":
        return False, True
    if mode == "Ocultar":
        return False, False
    return True, True


def render_phrase_preview(segments: List[Dict[str, Any]]) -> str:
    parts = []

    for seg in segments:
        keep_text, visible = segment_mode_to_flags(seg.get("segment_mode", "Texto apenas"))
        if not visible:
            continue

        text = seg.get("display_text", "")

        if seg.get("selected_pictograms"):
            if keep_text:
                parts.append(f"[PIC] {text}")
            else:
                labels = " + ".join(p["label"] for p in seg["selected_pictograms"])
                parts.append(f"[PIC] {labels}")
        else:
            if keep_text:
                parts.append(text)

    sentence = ""
    for idx, part in enumerate(parts):
        if idx == 0:
            sentence += part
        elif re.fullmatch(r"[,.!?;:]", part):
            sentence += part
        else:
            sentence += " " + part

    return sentence.strip()


def build_hybrid_html(title: str, original_text: str, segments: List[Dict[str, Any]]) -> str:
    blocks = []

    for seg in segments:
        keep_text, visible = segment_mode_to_flags(seg.get("segment_mode", "Texto apenas"))
        if not visible:
            continue

        text = seg.get("display_text", "")
        selected = seg.get("selected_pictograms", [])

        if selected:
            pictos_html = "".join(
                f"""
                <div class="picto-item">
                    <img src="{p['image_url']}" alt="{p['label']}">
                    <div class="picto-label">{p['label']} ({p.get('source_lang', '')})</div>
                </div>
                """
                for p in selected
            )
            text_html = f'<div class="segment-text">{text}</div>' if keep_text else ""
            block = f"""
            <div class="segment with-picto">
                <div class="picto-group">{pictos_html}</div>
                {text_html}
            </div>
            """
        else:
            if keep_text:
                block = f"""
                <div class="segment text-only">
                    <div class="segment-text">{text}</div>
                </div>
                """
            else:
                continue

        blocks.append(block)

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8">
      <title>{title}</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          padding: 20px;
          background: #ffffff;
          color: #222;
        }}
        h1 {{ margin-bottom: 8px; }}
        .subtitle {{ color: #555; margin-bottom: 20px; }}
        .sentence {{
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          align-items: flex-end;
        }}
        .segment {{
          border: 1px solid #ddd;
          border-radius: 14px;
          padding: 10px;
          min-height: 70px;
          background: #fafafa;
        }}
        .with-picto {{ background: #f8fbff; }}
        .text-only {{ background: #fffdf7; }}
        .picto-group {{
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: center;
          margin-bottom: 6px;
        }}
        .picto-item {{
          text-align: center;
          min-width: 80px;
        }}
        .picto-item img {{
          width: 72px;
          height: 72px;
          object-fit: contain;
        }}
        .picto-label {{
          font-size: 12px;
          color: #444;
        }}
        .segment-text {{
          text-align: center;
          font-size: 16px;
          font-weight: 600;
        }}
        .original {{
          margin-bottom: 18px;
          padding: 12px;
          border-radius: 12px;
          background: #f4f4f4;
        }}
      </style>
    </head>
    <body>
      <h1>{title}</h1>
      <div class="subtitle">Saída híbrida com texto e pictogramas</div>
      <div class="original">
        <strong>Texto original:</strong><br>
        {original_text}
      </div>
      <div class="sentence">
        {''.join(blocks)}
      </div>
    </body>
    </html>
    """


def build_output_json(title: str, original_text: str, segments: List[Dict[str, Any]]) -> str:
    payload = {
        "title": title,
        "original_text": original_text,
        "preview_text": render_phrase_preview(segments),
        "segments": segments,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def move_segment(segments: List[Dict[str, Any]], idx: int, direction: int) -> List[Dict[str, Any]]:
    new_segments = deepcopy(segments)
    new_idx = idx + direction
    if 0 <= new_idx < len(new_segments):
        new_segments[idx], new_segments[new_idx] = new_segments[new_idx], new_segments[idx]
    return new_segments


def duplicate_segment(segments: List[Dict[str, Any]], idx: int) -> List[Dict[str, Any]]:
    new_segments = deepcopy(segments)
    new_segments.insert(idx + 1, deepcopy(new_segments[idx]))
    return new_segments


def remove_segment(segments: List[Dict[str, Any]], idx: int) -> List[Dict[str, Any]]:
    new_segments = deepcopy(segments)
    if 0 <= idx < len(new_segments):
        new_segments.pop(idx)
    return new_segments


def sanitize_pdf_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).replace("\r", " ").replace("\t", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("latin-1", "ignore").decode("latin-1")
    return text.strip()


def download_image_tempfile(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=20, verify=False)
        response.raise_for_status()

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.write(response.content)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception:
        return None


def generate_simple_pdf(title: str, original_text: str, preview_text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    usable_width = pdf.w - pdf.l_margin - pdf.r_margin

    title = sanitize_pdf_text(title)
    original_text = sanitize_pdf_text(original_text)
    preview_text = sanitize_pdf_text(preview_text) or "Sem conteudo visivel."

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(usable_width, 10, title)

    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(usable_width, 8, "Texto original:")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(usable_width, 8, original_text)

    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(usable_width, 8, "Previa da saida final:")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(usable_width, 8, preview_text[:3000])

    return bytes(pdf.output())


def generate_visual_pdf(title: str, original_text: str, segments: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    card_gap = 6
    cols = 2
    card_width = (page_width - card_gap) / cols
    card_height = 52

    title = sanitize_pdf_text(title)
    original_text = sanitize_pdf_text(original_text)

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, title)

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"Texto original: {original_text}")

    pdf.ln(4)

    visible_segments = []
    for seg in segments:
        keep_text, visible = segment_mode_to_flags(seg.get("segment_mode", "Texto apenas"))
        if visible:
            visible_segments.append((seg, keep_text))

    x_start = pdf.l_margin
    y = pdf.get_y()
    col_idx = 0

    temp_files = []

    try:
        for seg, keep_text in visible_segments:
            if y + card_height > pdf.h - pdf.b_margin:
                pdf.add_page()
                y = pdf.t_margin
                col_idx = 0

            x = x_start + col_idx * (card_width + card_gap)

            pdf.set_draw_color(180, 180, 180)
            pdf.set_fill_color(248, 250, 252)
            pdf.rect(x, y, card_width, card_height, style="DF")

            inner_x = x + 3
            inner_y = y + 3
            inner_w = card_width - 6

            selected = seg.get("selected_pictograms", [])
            display_text = sanitize_pdf_text(seg.get("display_text", ""))

            if selected:
                max_images = min(len(selected), 2)
                img_w = 18
                img_h = 18
                spacing = 3
                total_img_width = (img_w * max_images) + (spacing * (max_images - 1))
                img_x = inner_x + max((inner_w - total_img_width) / 2, 0)
                img_y = inner_y + 1

                for i, pic in enumerate(selected[:2]):
                    tmp_path = download_image_tempfile(pic["image_url"])
                    if tmp_path:
                        temp_files.append(tmp_path)
                        try:
                            pdf.image(tmp_path, x=img_x + i * (img_w + spacing), y=img_y, w=img_w, h=img_h)
                        except Exception:
                            pass

                text_y = inner_y + 24
            else:
                text_y = inner_y + 8

            pdf.set_xy(inner_x, text_y)
            pdf.set_font("Helvetica", "B", 10)

            if keep_text:
                pdf.multi_cell(inner_w, 5, display_text, align="C")
            elif selected:
                labels = " + ".join(
                    sanitize_pdf_text(pic.get("label", ""))
                    for pic in selected[:2]
                )
                pdf.multi_cell(inner_w, 5, labels, align="C")
            else:
                pdf.multi_cell(inner_w, 5, "", align="C")

            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                y += card_height + card_gap

        return bytes(pdf.output())

    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass


def generate_board_pdf(title: str, selected_pictograms: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    title = sanitize_pdf_text(title)

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, title)
    pdf.ln(3)

    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    cols = 3
    gap = 6
    cell_w = (page_width - gap * (cols - 1)) / cols
    cell_h = 62

    x_start = pdf.l_margin
    y = pdf.get_y()
    col_idx = 0

    temp_files = []

    try:
        for pic in selected_pictograms:
            if y + cell_h > pdf.h - pdf.b_margin:
                pdf.add_page()
                y = pdf.t_margin
                col_idx = 0

            x = x_start + col_idx * (cell_w + gap)

            pdf.set_draw_color(170, 170, 170)
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(x, y, cell_w, cell_h, style="DF")

            label = sanitize_pdf_text(pic.get("label", ""))
            tmp_path = download_image_tempfile(pic["image_url"])

            if tmp_path:
                temp_files.append(tmp_path)
                try:
                    img_w = 28
                    img_h = 28
                    img_x = x + (cell_w - img_w) / 2
                    img_y = y + 6
                    pdf.image(tmp_path, x=img_x, y=img_y, w=img_w, h=img_h)
                except Exception:
                    pass

            pdf.set_xy(x + 4, y + 38)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(cell_w - 8, 5, label, align="C")

            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                y += cell_h + gap

        return bytes(pdf.output())

    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass

import base64

def render_hero():
    logo_html = ""
    logo_path = Path("assets/logo.svg")

    if logo_path.exists():
        svg_content = logo_path.read_bytes()
        b64 = base64.b64encode(svg_content).decode("utf-8")
        logo_html = (
            '<div class="hero-logo">'
            f'<img src="data:image/svg+xml;base64,{b64}" alt="Logo">'
            '</div>'
        )

    html = (
        '<div class="hero-wrap">'
        f'{logo_html}'
        '<div class="hero-content">'
        f'<div class="hero-title">{APP_TITLE}</div>'
        '<div class="hero-subtitle">'
        'Crie materiais acessíveis com pictogramas de forma inteligente, mantendo a estrutura da frase, '
        'ampliando a compreensão e preservando a autonomia pedagógica do professor.'
        '</div>'
        '<div class="hero-pills">'
        '<div class="hero-pill">CAA</div>'
        '<div class="hero-pill">Pictogramas</div>'
        '<div class="hero-pill">Português + Inglês + Espanhol</div>'
        '<div class="hero-pill">PDF / HTML / JSON</div>'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def render_kpis(templates, favorites, history):
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Modelos salvos</div>
            <div class="kpi-value">{len(templates)}</div>
            <div class="kpi-desc">Estruturas prontas para reutilização</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Favoritos</div>
            <div class="kpi-value">{len(favorites)}</div>
            <div class="kpi-desc">Pictogramas priorizados</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Histórico</div>
            <div class="kpi-value">{len(history)}</div>
            <div class="kpi-desc">Buscas recentes registradas</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Idiomas de busca</div>
            <div class="kpi-value">3</div>
            <div class="kpi-desc">Português, inglês e espanhol</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# INTERFACE
# =========================

render_hero()
templates = load_templates()
favorites = load_favorites()
history = load_search_history()
render_kpis(templates, favorites, history)

templates = load_templates()
favorites = load_favorites()
history = load_search_history()

with st.expander("Guia rápido de uso"):
    st.markdown("""
**Fluxo sugerido**

1. Escreva a frase.  
2. Clique em **Gerar sugestões**.  
3. Revise os segmentos.  
4. Escolha o modo de cada segmento.  
5. Se precisar, abra **Ajustes avançados**.  
6. Exporte em HTML, JSON ou PDF.  
""")

with st.expander("Biblioteca do projeto"):
    tab1, tab2, tab3 = st.tabs(["Modelos", "Favoritos", "Histórico"])

    with tab1:
        if templates:
            template_names = [tpl.get("title", "Sem título") for tpl in templates]
            selected_template_name = st.selectbox("Carregar modelo", [""] + template_names)
            if selected_template_name:
                selected_template = next(t for t in templates if t.get("title") == selected_template_name)
                if st.button("Carregar modelo selecionado", use_container_width=True):
                    st.session_state["material_title"] = selected_template.get("title", "")
                    st.session_state["original_text"] = selected_template.get("original_text", "")
                    st.session_state["segments"] = selected_template.get("segments", [])
                    st.rerun()
        else:
            st.caption("Nenhum modelo salvo ainda.")

    with tab2:
        if favorites:
            for fav in favorites:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.write(f"{fav.get('label')} — ID {fav.get('id')} ({fav.get('source_lang', '-')})")
                with c2:
                    if st.button("Remover", key=f"remove_fav_{fav.get('id')}"):
                        remove_favorite(fav.get("id"))
                        st.rerun()
        else:
            st.caption("Nenhum pictograma favorito ainda.")

    with tab3:
        if history:
            for item in history[:20]:
                st.write(f"{item.get('segment_text', '')} → {item.get('term', '')} [{item.get('lang', '')}]")
        else:
            st.caption("Nenhum histórico ainda.")

st.divider()

st.markdown("""
<div class="section-card">
    <div class="section-title">1. Entrada</div>
    <div class="section-subtitle">
        Escreva o conteúdo base que será transformado em material acessível com apoio pictográfico.
    </div>
</div>
""")

material_title = st.text_input(
    "Título do material",
    value=st.session_state.get("material_title", "Material acessível com pictogramas"),
)

input_text = st.text_area(
    "Texto do professor",
    height=160,
    value=st.session_state.get("original_text", ""),
    placeholder="Ex.: Depois do recreio, guarde o material e sente-se em roda.",
)

st.markdown(
    '<div class="section-card">'
    '<div class="section-title">1. Entrada</div>'
    '<div class="section-subtitle">Escreva o conteúdo base que será transformado em material acessível com apoio pictográfico.</div>'
    '</div>',
    unsafe_allow_html=True
)
if st.button("Gerar sugestões", use_container_width=True):
    if not input_text.strip():
        st.error("Digite um texto primeiro.")
        st.stop()

    segments = build_segments(input_text)
    segments = fetch_options_for_segments(segments)

    st.session_state["segments"] = segments
    st.session_state["original_text"] = input_text
    st.session_state["material_title"] = material_title
    st.rerun()

if "segments" in st.session_state:
    st.divider()
    st.markdown("""
    <div class="section-card">
        <div class="section-title">2. Revisão dos segmentos</div>
        <div class="section-subtitle">
            Revise cada segmento, escolha o modo de exibição e refine a busca apenas quando precisar.
        </div>
    </div>
    """)

    segments = st.session_state["segments"]
    edited_segments = []

    for idx, seg in enumerate(segments):
        with st.container(border=True):
            st.markdown(f"<div class='segment-chip'>Segmento {idx + 1}</div>", unsafe_allow_html=True)
            st.markdown(f"### {seg.get('display_text', seg['original_text'])}")
            st.caption(f"Original: {seg['original_text']}")

            display_text = st.text_input(
                "Texto exibido",
                value=seg.get("display_text", seg["original_text"]),
                key=f"display_text_{idx}",
            )

            mode_options = ["Texto apenas", "Texto + pictograma", "Pictograma apenas", "Ocultar"]
            default_mode = seg.get(
                "segment_mode",
                "Texto + pictograma" if seg["segment_type"] == "text_with_pictogram" else "Texto apenas"
            )
            segment_mode = st.selectbox(
                "Modo do segmento",
                options=mode_options,
                index=mode_options.index(default_mode) if default_mode in mode_options else 0,
                key=f"segment_mode_{idx}",
            )

            seg["display_text"] = display_text
            seg["segment_mode"] = segment_mode

            if seg["segment_type"] == "text":
                edited_segments.append(seg)
                continue

            options = seg.get("pictogram_options", [])
            option_labels = [
                f"{opt['label']} (ID {opt['id']}, {opt.get('source_lang', '-')})"
                for opt in options
            ]

            previous_selected_ids = set(seg.get("selected_pictogram_ids", []))
            default_selected_labels = []
            for opt, label in zip(options, option_labels):
                if opt["id"] in previous_selected_ids:
                    default_selected_labels.append(label)

            selected_labels = st.multiselect(
                "Pictogramas selecionados",
                options=option_labels,
                default=default_selected_labels,
                key=f"multi_{idx}",
            )

            selected_pictograms = [
                opt for opt, label in zip(options, option_labels) if label in selected_labels
            ]

            seg["selected_pictograms"] = selected_pictograms
            seg["selected_pictogram_ids"] = [p["id"] for p in selected_pictograms]

            if selected_pictograms:
                cols = st.columns(min(len(selected_pictograms), 3))
                for pic_idx, pic in enumerate(selected_pictograms[:3]):
                    with cols[pic_idx]:
                        st.image(pic["image_url"], width=110)
                        st.caption(f"{pic['label']} ({pic.get('source_lang', '-')})")
                        if st.button("⭐", key=f"fav_{idx}_{pic['id']}", help="Favoritar"):
                            save_favorite(pic)
                            st.rerun()

            with st.expander("Ajustes avançados"):
                lang_cols = st.columns(3)
                with lang_cols[0]:
                    term_pt = st.text_input(
                        "Busca em português",
                        value=seg.get("search_terms", {}).get("pt", ""),
                        key=f"search_pt_{idx}",
                    )
                with lang_cols[1]:
                    term_en = st.text_input(
                        "Busca em inglês",
                        value=seg.get("search_terms", {}).get("en", ""),
                        key=f"search_en_{idx}",
                    )
                with lang_cols[2]:
                    term_es = st.text_input(
                        "Busca em espanhol",
                        value=seg.get("search_terms", {}).get("es", ""),
                        key=f"search_es_{idx}",
                    )

                active_languages = st.multiselect(
                    "Idiomas ativos para busca",
                    options=["pt", "en", "es"],
                    default=seg.get("active_languages", ["pt"]),
                    key=f"active_langs_{idx}",
                )

                pt_base = term_pt.strip()
                hints = get_language_hints(pt_base)
                if hints["en"] or hints["es"]:
                    st.caption(
                        "Sugestões rápidas — "
                        f"EN: {', '.join(hints['en']) if hints['en'] else '-'} | "
                        f"ES: {', '.join(hints['es']) if hints['es'] else '-'}"
                    )

                seg["search_terms"] = {
                    "pt": term_pt.strip(),
                    "en": term_en.strip(),
                    "es": term_es.strip(),
                }
                seg["active_languages"] = active_languages

                adv_a, adv_b, adv_c, adv_d = st.columns(4)

                with adv_a:
                    if st.button("⬆️ Subir", key=f"up_{idx}", use_container_width=True):
                        st.session_state["segments"] = move_segment(segments, idx, -1)
                        st.rerun()

                with adv_b:
                    if st.button("⬇️ Descer", key=f"down_{idx}", use_container_width=True):
                        st.session_state["segments"] = move_segment(segments, idx, 1)
                        st.rerun()

                with adv_c:
                    if st.button("📄 Duplicar", key=f"dup_{idx}", use_container_width=True):
                        st.session_state["segments"] = duplicate_segment(segments, idx)
                        st.rerun()

                with adv_d:
                    if st.button("🗑️ Remover", key=f"remove_{idx}", use_container_width=True):
                        st.session_state["segments"] = remove_segment(segments, idx)
                        st.rerun()

                if st.button("🔎 Atualizar busca deste segmento", key=f"refresh_{idx}", use_container_width=True):
                    seg = fetch_options_for_segment(seg)
                    segments[idx] = seg
                    st.session_state["segments"] = segments
                    st.rerun()

                if seg.get("fetch_error"):
                    st.warning(seg["fetch_error"])

            edited_segments.append(seg)

    st.session_state["segments"] = edited_segments
    st.session_state["material_title"] = material_title
    st.session_state["original_text"] = input_text

    st.divider()
    st.markdown("""
    <div class="section-card">
        <div class="section-title">3. Prévia final</div>
        <div class="section-subtitle">
            Visualize como o material será apresentado antes de salvar ou exportar.
        </div>
    </div>
    """)

    preview_text = render_phrase_preview(edited_segments)
    st.markdown("**Estrutura textual final**")
    st.write(preview_text if preview_text else "_Nenhum segmento visível na saída final._")

    st.markdown("<div class='preview-panel'><strong>Prévia visual</strong></div>", unsafe_allow_html=True)
    visible_segments = [seg for seg in edited_segments if segment_mode_to_flags(seg.get("segment_mode", "Texto apenas"))[1]]

    for start in range(0, len(visible_segments), 2):
        row = st.columns(2)
        for col_idx, seg in enumerate(visible_segments[start:start + 2]):
            keep_text, _ = segment_mode_to_flags(seg.get("segment_mode", "Texto apenas"))
            with row[col_idx]:
                with st.container(border=True):
                    st.markdown(f"**{seg['display_text']}**")
                    if seg.get("selected_pictograms"):
                        for pic in seg["selected_pictograms"][:2]:
                            st.image(pic["image_url"], width=95)
                            st.caption(f"{pic['label']} ({pic.get('source_lang', '-')})")
                    else:
                        st.caption("Sem pictograma")
                    st.caption(seg.get("segment_mode", "Texto apenas"))
                    st.caption("Texto mantido" if keep_text else "Sem texto")

    html_hybrid = build_hybrid_html(material_title, input_text, edited_segments)
    json_output = build_output_json(material_title, input_text, edited_segments)

    selected_only = []
    for seg in edited_segments:
        for pic in seg.get("selected_pictograms", []):
            selected_only.append(pic)

    html_board = generate_board_html(material_title, selected_only) if selected_only else ""
    pdf_simple_bytes = generate_simple_pdf(material_title, input_text, preview_text)
    pdf_visual_bytes = generate_visual_pdf(material_title, input_text, edited_segments)
    pdf_board_bytes = generate_board_pdf(material_title, selected_only) if selected_only else b""

    st.divider()
    st.markdown(
    '<div class="section-card">'
    '<div class="section-title">1. Entrada</div>'
    '<div class="section-subtitle">Escreva o conteúdo base que será transformado em material acessível com apoio pictográfico.</div>'
    '</div>',
    unsafe_allow_html=True
)

    st.markdown("<div class='preview-panel'><strong>Prévia visual</strong></div>", unsafe_allow_html=True)

    save_col, export_col1, export_col2 = st.columns(3)

    with save_col:
        if st.button("💾 Salvar como modelo", use_container_width=True):
            save_template({
                "title": material_title,
                "original_text": input_text,
                "segments": edited_segments,
            })
            st.success("Modelo salvo.")

    with export_col1:
        st.download_button(
            label="Baixar HTML híbrido",
            data=html_hybrid,
            file_name="saida_hibrida_pictogramas.html",
            mime="text/html",
            use_container_width=True,
        )

        st.download_button(
            label="Baixar JSON",
            data=json_output,
            file_name="estrutura_hibrida_pictogramas.json",
            mime="application/json",
            use_container_width=True,
        )

    with export_col2:
        st.download_button(
            label="Baixar PDF simples",
            data=pdf_simple_bytes,
            file_name="material_pictogramas_textual.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.download_button(
            label="Baixar PDF visual híbrido",
            data=pdf_visual_bytes,
            file_name="material_pictogramas_visual.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    if pdf_board_bytes:
        st.download_button(
            label="Baixar PDF prancha A4",
            data=pdf_board_bytes,
            file_name="prancha_pictogramas_a4.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    if html_board:
        st.download_button(
            label="Baixar prancha simples em HTML",
            data=html_board,
            file_name="prancha_simples_pictogramas.html",
            mime="text/html",
            use_container_width=True,
        )

st.divider()
st.markdown("</div>", unsafe_allow_html=True)