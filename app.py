from __future__ import annotations

from typing import Dict, List

import streamlit as st

from core.ai_utils import ai_rewrite_for_caa, maybe_enrich_tokens
from core.nlp import analyze_text
from core.pdf_utils import generate_pdf
from services.arasaac_api import fetch_pictogram, search_arasaac_options


st.set_page_config(
    page_title="CAA Studio",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main {
            background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
        }

        .hero {
            padding: 1.25rem 1.4rem;
            border-radius: 22px;
            background: linear-gradient(135deg, #4f46e5 0%, #9333ea 50%, #ec4899 100%);
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 10px 28px rgba(79,70,229,0.18);
        }

        .hero h1 {
            margin: 0 0 0.3rem 0;
            font-size: 2rem;
            line-height: 1.1;
        }

        .hero p {
            margin: 0;
            opacity: 0.95;
            font-size: 1rem;
        }

        .mini-badge {
            display: inline-block;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.22);
            padding: 0.3rem 0.6rem;
            border-radius: 999px;
            font-size: 0.85rem;
            margin-bottom: 0.7rem;
        }

        .section-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #111827;
            margin: 1rem 0 0.7rem 0;
        }

        .legend-box {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 8px 24px rgba(15,23,42,0.05);
        }

        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin: 0.25rem 0.65rem 0.25rem 0;
            font-size: 0.9rem;
        }

        .legend-swatch {
            width: 18px;
            height: 18px;
            border-radius: 6px;
            border: 1px solid rgba(0,0,0,0.08);
            display: inline-block;
        }

        .stButton button,
        .stDownloadButton button {
            border-radius: 14px !important;
            font-weight: 700 !important;
        }

        .card-badge {
            display:inline-block;
            padding:6px 12px;
            border-radius:999px;
            font-size:12px;
            font-weight:700;
            color:#111827;
            margin-bottom:8px;
        }

        .card-title {
            font-size: 18px;
            font-weight: 800;
            color: #111827;
            margin-top: 8px;
            margin-bottom: 2px;
        }

        .card-meta {
            font-size: 13px;
            color: #6b7280;
            line-height: 1.4;
            margin-top: 4px;
        }

        .fallback-box {
            height:220px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:56px;
            background:#f8fafc;
            border-radius:16px;
            border: 1px solid #e5e7eb;
        }

        .thumb-frame {
            border-radius: 12px;
            padding: 3px;
            background: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "cards": [],
        "processed_text": "",
        "card_selections": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="mini-badge">CAA Studio • ARASAAC • seleção visual de pictogramas</div>
            <h1>CAA Studio</h1>
            <p>Geração de pranchas com análise sintática, pictogramas ARASAAC e escolha visual do melhor card.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_card_id(token_text: str, lemma: str, index: int) -> str:
    safe_text = (token_text or "").strip().lower()
    safe_lemma = (lemma or "").strip().lower()
    return f"{index}_{safe_text}_{safe_lemma}"


def build_cards(text: str, use_ai: bool) -> List[Dict]:
    base_text = text.strip()
    if not base_text:
        st.session_state["processed_text"] = ""
        st.session_state["cards"] = []
        st.session_state["card_selections"] = {}
        return []

    processed = ai_rewrite_for_caa(base_text) if use_ai else base_text
    analyzed = analyze_text(processed)
    analyzed = maybe_enrich_tokens(analyzed)

    allowed_pos = {"NOUN", "VERB", "ADJ", "PRON"}
    ignored_words = {
        "o", "a", "os", "as", "um", "uma", "uns", "umas",
        "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
        "para", "por", "com", "sem", "e", "ou", "mas", "que", "se"
    }

    cards = []
    seen = set()

    for idx, item in enumerate(analyzed):
        token_text = str(item.get("text", "")).strip()
        lemma = str(item.get("lemma", "")).strip().lower()
        pos = item.get("pos", "X")

        if not token_text or pos == "PUNCT":
            continue

        if token_text.lower() in ignored_words:
            continue

        if pos not in allowed_pos:
            continue

        dedupe_key = lemma or token_text.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        picto = fetch_pictogram(token_text, lemma=lemma)
        options = search_arasaac_options(lemma or token_text, lang="pt", limit=8)

        image_url = picto.get("image_url")
        if not image_url and options:
            image_url = options[0]["image_url"]

        card_id = build_card_id(token_text, lemma, idx)

        cards.append(
            {
                "id": card_id,
                "text": token_text,
                "lemma": lemma or token_text.lower(),
                "pos": pos,
                "sintax_color": item.get("sintax_color", "#E5E7EB"),
                "emoji_fallback": item.get("emoji_fallback", "🧩"),
                "image_url": image_url,
                "options": options,
            }
        )

    st.session_state["processed_text"] = processed
    st.session_state["cards"] = cards

    new_selections = {}
    for card in cards:
        options = card.get("options", [])
        current = st.session_state["card_selections"].get(card["id"], 0)

        if not options:
            new_selections[card["id"]] = 0
            continue

        if current >= len(options):
            current = 0

        new_selections[card["id"]] = current
        card["image_url"] = options[current]["image_url"]

    st.session_state["card_selections"] = new_selections
    return cards


def render_legend() -> None:
    legend = [
        ("PRON", "#FFE8A3", "Pronome"),
        ("VERB", "#FFC2D1", "Verbo"),
        ("NOUN", "#BDE0FE", "Substantivo"),
        ("ADJ", "#CDEAC0", "Adjetivo"),
        ("ADP", "#E9D5FF", "Preposição"),
        ("CCONJ", "#FDE68A", "Conjunção"),
        ("DET", "#FBCFE8", "Determinante/Artigo"),
        ("X", "#D1FAE5", "Outros"),
    ]

    st.markdown('<div class="section-title">Legenda sintática</div>', unsafe_allow_html=True)
    st.markdown('<div class="legend-box">', unsafe_allow_html=True)

    for pos, color, label in legend:
        st.markdown(
            f"""
            <span class="legend-item">
                <span class="legend-swatch" style="background:{color};"></span>
                <strong>{pos}</strong> — {label}
            </span>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def apply_card_selection(card: Dict, selected_idx: int) -> None:
    options = card.get("options", [])
    if options and 0 <= selected_idx < len(options):
        card["image_url"] = options[selected_idx]["image_url"]
        st.session_state["card_selections"][card["id"]] = selected_idx


def render_option_thumbnails(card: Dict) -> None:
    options = card.get("options", [])
    if not options:
        return

    current_idx = st.session_state["card_selections"].get(card["id"], 0)

    st.caption("Escolha visualmente o pictograma:")
    thumb_cols = st.columns(min(len(options), 4))

    for idx, option in enumerate(options[:8]):
        col = thumb_cols[idx % 4]

        with col:
            is_selected = idx == current_idx
            border_color = card["sintax_color"] if is_selected else "#E5E7EB"
            border_size = 3 if is_selected else 1

            st.markdown(
                f"""
                <div class="thumb-frame" style="border:{border_size}px solid {border_color};">
                """,
                unsafe_allow_html=True,
            )
            st.image(option["image_url"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            button_label = "Selecionado" if is_selected else "Usar"
            if st.button(
                button_label,
                key=f"use_option_{card['id']}_{idx}",
                use_container_width=True,
                disabled=is_selected,
            ):
                apply_card_selection(card, idx)
                st.rerun()


def render_cards(cards: List[Dict]) -> None:
    st.markdown("## Cards gerados")

    if not cards:
        st.info("Digite uma frase e clique em gerar.")
        return

    cols_per_row = 3

    for row_start in range(0, len(cards), cols_per_row):
        cols = st.columns(cols_per_row)
        row_cards = cards[row_start:row_start + cols_per_row]

        for col, card in zip(cols, row_cards):
            with col:
                st.markdown(
                    f'<div class="card-badge" style="background:{card["sintax_color"]};">{card["pos"]}</div>',
                    unsafe_allow_html=True,
                )

                with st.container(border=True):
                    image_border_color = card["sintax_color"]

                    st.markdown(
                        f"""
                        <div style="
                            border: 4px solid {image_border_color};
                            border-radius: 18px;
                            padding: 8px;
                            background: white;
                            margin-bottom: 10px;
                        ">
                        """,
                        unsafe_allow_html=True,
                    )

                    if card.get("image_url"):
                        st.image(card["image_url"], use_container_width=True)
                    else:
                        st.markdown(
                            f'<div class="fallback-box">{card["emoji_fallback"]}</div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown("</div>", unsafe_allow_html=True)

                    render_option_thumbnails(card)

                    st.markdown(
                        f'<div class="card-title">{card["text"]}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="card-meta">Lema: {card["lemma"]} | Classe: {card["pos"]}</div>',
                        unsafe_allow_html=True,
                    )


def sidebar_controls():
    st.sidebar.title("Configurações")
    use_ai = st.sidebar.toggle("Ativar camada de IA", value=False)
    pdf_title = st.sidebar.text_input("Título do PDF", value="Prancha CAA")
    st.sidebar.caption(
        "A imagem escolhida visualmente em cada card será mantida na exportação em PDF."
    )
    return use_ai, pdf_title


def get_cards_for_export() -> List[Dict]:
    exported_cards = []

    for card in st.session_state["cards"]:
        card_copy = dict(card)
        options = card_copy.get("options", [])
        selected_idx = st.session_state["card_selections"].get(card_copy["id"], 0)

        if options and 0 <= selected_idx < len(options):
            card_copy["image_url"] = options[selected_idx]["image_url"]

        exported_cards.append(card_copy)

    return exported_cards


def main():
    init_state()
    inject_css()
    render_header()

    use_ai, pdf_title = sidebar_controls()

    input_col, action_col = st.columns([3, 1])

    with input_col:
        user_text = st.text_area(
            "Digite o texto para gerar os cards",
            height=130,
            placeholder="Ex.: Guarde os brinquedos na caixa.",
        )

    with action_col:
        st.write("")
        st.write("")
        generate = st.button("Gerar cards", use_container_width=True)
        clear = st.button("Limpar", use_container_width=True)

    if clear:
        st.session_state["cards"] = []
        st.session_state["processed_text"] = ""
        st.session_state["card_selections"] = {}
        st.rerun()

    if generate:
        try:
            build_cards(user_text, use_ai=use_ai)
        except Exception as exc:
            st.error(f"Falha ao processar o texto: {exc}")

    if st.session_state["processed_text"]:
        st.markdown('<div class="section-title">Texto processado</div>', unsafe_allow_html=True)
        st.code(st.session_state["processed_text"], language="text")

    render_legend()
    render_cards(st.session_state["cards"])

    if st.session_state["cards"]:
        try:
            export_cards = get_cards_for_export()
            pdf_path = generate_pdf(export_cards, title=pdf_title)

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Baixar PDF",
                    data=f.read(),
                    file_name="prancha_caa.pdf",
                    mime="application/pdf",
                    use_container_width=False,
                )
        except Exception as exc:
            st.warning(f"Não foi possível gerar o PDF: {exc}")


if __name__ == "__main__":
    main()