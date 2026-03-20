from __future__ import annotations

import os
import tempfile
import unicodedata
from typing import Dict, List, Optional

import requests
from fpdf import FPDF


def safe_pdf_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    return text.encode("latin-1", "ignore").decode("latin-1")


class CAAPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, safe_pdf_text("Prancha CAA"), border=0, ln=1, align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, safe_pdf_text(f"Pagina {self.page_no()}"), border=0, ln=0, align="C")


def hex_to_rgb(hex_color: str):
    hex_color = (hex_color or "#EEEEEE").lstrip("#")
    if len(hex_color) != 6:
        return (238, 238, 238)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def download_image_temp(url: str) -> Optional[str]:
    if not url:
        return None

    try:
        response = requests.get(url, timeout=15, verify=False)
        if response.status_code != 200 or not response.content:
            return None

        suffix = ".png"
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        with open(path, "wb") as f:
            f.write(response.content)

        return path
    except Exception:
        return None


def generate_pdf(cards: List[Dict], title: str = "Prancha CAA") -> str:
    pdf = CAAPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_title(safe_pdf_text(title))

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, safe_pdf_text(title), ln=1)
    pdf.ln(2)

    cell_w = 60
    cell_h = 78
    margin_x = 10
    gap_x = 5
    gap_y = 8

    x = margin_x
    y = pdf.get_y()

    temp_files = []

    try:
        for card in cards:
            word = safe_pdf_text(card.get("text", ""))
            pos = safe_pdf_text(card.get("pos", ""))
            lemma = safe_pdf_text(card.get("lemma", ""))
            color = card.get("sintax_color", "#EEEEEE")
            image_url = card.get("image_url")

            if x + cell_w > 200:
                x = margin_x
                y += cell_h + gap_y

            if y + cell_h > 270:
                pdf.add_page()
                x = margin_x
                y = pdf.get_y()

            rgb = hex_to_rgb(color)
            pdf.set_fill_color(*rgb)
            pdf.set_draw_color(180, 180, 180)
            pdf.rect(x, y, cell_w, cell_h, style="FD")

            # Faixa superior da classe gramatical
            pdf.set_xy(x + 3, y + 3)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(cell_w - 6, 6, pos, border=0, ln=0)

            # Área da imagem
            image_x = x + 6
            image_y = y + 12
            image_w = cell_w - 12
            image_h = 34

            pdf.set_fill_color(248, 250, 252)
            pdf.rect(image_x, image_y, image_w, image_h, style="F")

            img_path = download_image_temp(image_url) if image_url else None
            if img_path:
                temp_files.append(img_path)
                try:
                    pdf.image(img_path, x=image_x, y=image_y, w=image_w, h=image_h)
                except Exception:
                    pdf.set_xy(image_x, image_y + 12)
                    pdf.set_font("Helvetica", "", 18)
                    pdf.cell(image_w, 10, "[]", border=0, ln=0, align="C")
            else:
                pdf.set_xy(image_x, image_y + 12)
                pdf.set_font("Helvetica", "", 18)
                pdf.cell(image_w, 10, "[]", border=0, ln=0, align="C")

            # Palavra
            pdf.set_xy(x + 4, y + 50)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(cell_w - 8, 5, word, border=0)

            # Metadados
            pdf.set_xy(x + 4, y + 61)
            pdf.set_font("Helvetica", "", 9)
            meta = f"Classe: {pos}"
            if lemma and lemma != word.lower():
                meta += f" | lema: {lemma}"
            pdf.multi_cell(cell_w - 8, 4.5, safe_pdf_text(meta), border=0)

            x += cell_w + gap_x

        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        pdf.output(path)
        return path

    finally:
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass