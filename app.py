import os
import json
import re
from copy import deepcopy
from typing import List, Dict, Any
from io import BytesIO

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

st.set_page_config(page_title=APP_TITLE, page_icon="🧩", layout="wide")

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
                "keep_text": True,
                "visible": True,
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
                "keep_text": True,
                "visible": True,
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
                "keep_text": True,
                "visible": True,
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
                "keep_text": True,
                "visible": True,
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


def render_phrase_preview(segments: List[Dict[str, Any]]) -> str:
    parts = []

    for seg in segments:
        if not seg.get("visible", True):
            continue

        text = seg.get("display_text", "")

        if seg.get("selected_pictograms"):
            if seg.get("keep_text", True):
                parts.append(f"[PIC] {text}")
            else:
                labels = " + ".join(p["label"] for p in seg["selected_pictograms"])
                parts.append(f"[PIC] {labels}")
        else:
            if seg.get("keep_text", True):
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
        if not seg.get("visible", True):
            continue

        text = seg.get("display_text", "")
        selected = seg.get("selected_pictograms", [])
        keep_text = seg.get("keep_text", True)

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
          padding: 24px;
          background: #ffffff;
          color: #222;
        }}
        h1 {{ margin-bottom: 8px; }}
        .subtitle {{ color: #555; margin-bottom: 24px; }}
        .sentence {{
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: flex-end;
        }}
        .segment {{
          border: 1px solid #ddd;
          border-radius: 14px;
          padding: 10px;
          min-height: 80px;
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
          min-width: 90px;
        }}
        .picto-item img {{
          width: 80px;
          height: 80px;
          object-fit: contain;
        }}
        .picto-label {{
          font-size: 12px;
          color: #444;
        }}
        .segment-text {{
          text-align: center;
          font-size: 18px;
          font-weight: 600;
        }}
        .original {{
          margin-bottom: 20px;
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


def generate_simple_pdf(title: str, original_text: str, preview_text: str) -> bytes:
    def sanitize_text(text: str) -> str:
        if not text:
            return ""
        text = str(text).replace("\r", " ").replace("\t", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    usable_width = pdf.w - pdf.l_margin - pdf.r_margin

    title = sanitize_text(title)
    original_text = sanitize_text(original_text)
    preview_text = sanitize_text(preview_text) or "Sem conteúdo visível."

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
    pdf.multi_cell(usable_width, 8, "Prévia da saída final:")

    pdf.set_font("Helvetica", "", 12)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(usable_width, 8, preview_text)

    return bytes(pdf.output())


st.title(APP_TITLE)
st.caption("Protótipo para transformar texto em saída híbrida com pictogramas e linguagem escrita.")

templates = load_templates()
favorites = load_favorites()
history = load_search_history()

with st.expander("Modelos salvos"):
    if templates:
        template_names = [tpl.get("title", "Sem título") for tpl in templates]
        selected_template_name = st.selectbox("Carregar modelo", [""] + template_names)
        if selected_template_name:
            selected_template = next(t for t in templates if t.get("title") == selected_template_name)
            if st.button("Carregar este modelo"):
                st.session_state["material_title"] = selected_template.get("title", "")
                st.session_state["original_text"] = selected_template.get("original_text", "")
                st.session_state["segments"] = selected_template.get("segments", [])
                st.rerun()
    else:
        st.caption("Nenhum modelo salvo ainda.")

with st.expander("Favoritos"):
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

with st.expander("Histórico de busca"):
    if history:
        for item in history[:20]:
            st.write(f"{item.get('segment_text', '')} → {item.get('term', '')} [{item.get('lang', '')}]")
    else:
        st.caption("Nenhum histórico ainda.")

left, right = st.columns([2, 1])

with left:
    material_title = st.text_input(
        "Título do material",
        value=st.session_state.get("material_title", "Material acessível com pictogramas"),
    )
    input_text = st.text_area(
        "Texto do professor",
        height=180,
        value=st.session_state.get("original_text", ""),
        placeholder="Ex.: Depois do recreio, guarde o material e sente-se em roda.",
    )

with right:
    st.info("Versão 1.4: modelos, favoritos, histórico e PDF simples.")

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
    st.subheader("Revisão dos segmentos e pictogramas")

    segments = st.session_state["segments"]
    edited_segments = []

    for idx, seg in enumerate(segments):
        with st.container(border=True):
            top_a, top_b, top_c, top_d = st.columns(4)

            with top_a:
                if st.button("⬆️ Subir", key=f"up_{idx}", use_container_width=True):
                    st.session_state["segments"] = move_segment(segments, idx, -1)
                    st.rerun()

            with top_b:
                if st.button("⬇️ Descer", key=f"down_{idx}", use_container_width=True):
                    st.session_state["segments"] = move_segment(segments, idx, 1)
                    st.rerun()

            with top_c:
                if st.button("📄 Duplicar", key=f"dup_{idx}", use_container_width=True):
                    st.session_state["segments"] = duplicate_segment(segments, idx)
                    st.rerun()

            with top_d:
                if st.button("🗑️ Remover", key=f"remove_{idx}", use_container_width=True):
                    st.session_state["segments"] = remove_segment(segments, idx)
                    st.rerun()

            st.markdown(f"### Segmento {idx + 1}")
            st.markdown(f"**Texto original:** `{seg['original_text']}`")

            if seg["segment_type"] == "text":
                display_text = st.text_input(
                    "Texto exibido na saída final",
                    value=seg.get("display_text", seg["original_text"]),
                    key=f"display_text_text_{idx}",
                )
                keep_text = st.checkbox(
                    "Manter este texto na saída final",
                    value=seg.get("keep_text", True),
                    key=f"keep_text_only_{idx}",
                )
                visible = st.checkbox(
                    "Exibir este segmento",
                    value=seg.get("visible", True),
                    key=f"visible_text_only_{idx}",
                )

                seg["display_text"] = display_text
                seg["keep_text"] = keep_text
                seg["visible"] = visible
                seg["selected_pictograms"] = []
                seg["selected_pictogram_ids"] = []

                edited_segments.append(seg)
                continue

            display_text = st.text_input(
                "Texto exibido na saída final",
                value=seg.get("display_text", seg["original_text"]),
                key=f"display_text_{idx}",
            )

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

            col_a, col_b = st.columns(2)
            with col_a:
                keep_text = st.checkbox(
                    "Manter texto junto com os pictogramas",
                    value=seg.get("keep_text", True),
                    key=f"keep_text_{idx}",
                )
            with col_b:
                visible = st.checkbox(
                    "Exibir este segmento",
                    value=seg.get("visible", True),
                    key=f"visible_{idx}",
                )

            seg["display_text"] = display_text
            seg["search_terms"] = {
                "pt": term_pt.strip(),
                "en": term_en.strip(),
                "es": term_es.strip(),
            }
            seg["active_languages"] = active_languages
            seg["keep_text"] = keep_text
            seg["visible"] = visible

            if st.button(f"🔎 Atualizar busca deste segmento", key=f"refresh_{idx}", use_container_width=True):
                seg = fetch_options_for_segment(seg)
                segments[idx] = seg
                st.session_state["segments"] = segments
                st.rerun()

            options = seg.get("pictogram_options", [])
            fetch_error = seg.get("fetch_error", "")

            if fetch_error:
                st.warning(fetch_error)

            if not options:
                st.info("Nenhum pictograma encontrado para este segmento. Ele pode permanecer apenas como texto.")
                seg["selected_pictograms"] = []
                seg["selected_pictogram_ids"] = []
                edited_segments.append(seg)
                continue

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
                f"Selecione um ou mais pictogramas para '{seg['display_text']}'",
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
                cols = st.columns(min(len(selected_pictograms), 4))
                for pic_idx, pic in enumerate(selected_pictograms[:4]):
                    with cols[pic_idx]:
                        st.image(pic["image_url"], width=120)
                        st.caption(f"{pic['label']} ({pic.get('source_lang', '-')})")
                        if st.button("⭐ Favoritar", key=f"fav_{idx}_{pic['id']}"):
                            save_favorite(pic)
                            st.rerun()

            edited_segments.append(seg)

    st.session_state["segments"] = edited_segments
    st.session_state["material_title"] = material_title
    st.session_state["original_text"] = input_text

    st.divider()
    st.subheader("Prévia da saída final")

    preview_text = render_phrase_preview(edited_segments)
    st.markdown("**Prévia textual da estrutura final:**")
    st.write(preview_text if preview_text else "_Nenhum segmento visível na saída final._")

    st.markdown("**Prévia visual por segmento:**")
    preview_cols = st.columns(4)
    visible_index = 0

    for seg in edited_segments:
        if not seg.get("visible", True):
            continue

        with preview_cols[visible_index % 4]:
            st.markdown(f"**{seg['display_text']}**")
            if seg.get("selected_pictograms"):
                for pic in seg["selected_pictograms"][:2]:
                    st.image(pic["image_url"], width=90)
                    st.caption(f"{pic['label']} ({pic.get('source_lang', '-')})")
            else:
                st.caption("Sem pictograma")

            st.caption("Texto mantido" if seg.get("keep_text", True) else "Só pictograma")

        visible_index += 1

    html_hybrid = build_hybrid_html(material_title, input_text, edited_segments)
    json_output = build_output_json(material_title, input_text, edited_segments)

    selected_only = []
    for seg in edited_segments:
        for pic in seg.get("selected_pictograms", []):
            selected_only.append(pic)

    html_board = generate_board_html(material_title, selected_only) if selected_only else ""
    pdf_bytes = generate_simple_pdf(material_title, input_text, preview_text)

    st.divider()
    st.subheader("Salvar e exportar")

    col_save, col_html, col_json, col_pdf = st.columns(4)

    with col_save:
        if st.button("💾 Salvar como modelo", use_container_width=True):
            save_template({
                "title": material_title,
                "original_text": input_text,
                "segments": edited_segments,
            })
            st.success("Modelo salvo.")

    with col_html:
        st.download_button(
            label="Baixar HTML híbrido",
            data=html_hybrid,
            file_name="saida_hibrida_pictogramas.html",
            mime="text/html",
            use_container_width=True,
        )

    with col_json:
        st.download_button(
            label="Baixar JSON",
            data=json_output,
            file_name="estrutura_hibrida_pictogramas.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_pdf:
        st.download_button(
            label="Baixar PDF simples",
            data=pdf_bytes,
            file_name="material_pictogramas.pdf",
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
st.caption(
    "Protótipo educacional em evolução. Recomenda-se validação pedagógica com professores, estudantes e equipes de acessibilidade antes de uso ampliado."
)