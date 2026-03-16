import html
import json
from typing import List, Dict, Any


def generate_board_html(title: str, selected_items: List[Dict[str, Any]]) -> str:
    cards = []
    for item in selected_items:
        cards.append(f"""
        <div class=\"card\"> 
            <img src=\"{html.escape(item['image_url'])}\" alt=\"{html.escape(item['label'])}\"> 
            <div class=\"label\">{html.escape(item['label'])}</div>
        </div>
        """)

    return f"""
    <!DOCTYPE html>
    <html lang=\"pt-BR\">
    <head>
      <meta charset=\"UTF-8\">
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
      <title>{html.escape(title)}</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          padding: 24px;
          background: #f8fafc;
        }}
        h1 {{
          text-align: center;
          margin-bottom: 8px;
        }}
        .subtitle {{
          text-align: center;
          color: #475569;
          margin-bottom: 20px;
        }}
        .grid {{
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 16px;
          margin-top: 24px;
        }}
        .card {{
          border: 1px solid #cbd5e1;
          border-radius: 16px;
          padding: 12px;
          text-align: center;
          background: white;
          box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        img {{
          max-width: 100%;
          height: 140px;
          object-fit: contain;
        }}
        .label {{
          margin-top: 10px;
          font-size: 20px;
          font-weight: bold;
        }}
        .credits {{
          margin-top: 32px;
          font-size: 12px;
          color: #555;
          line-height: 1.5;
        }}
      </style>
    </head>
    <body>
      <h1>{html.escape(title)}</h1>
      <div class=\"subtitle\">Prancha visual gerada automaticamente</div>
      <div class=\"grid\">
        {''.join(cards)}
      </div>
      <div class=\"credits\">
        Pictogramas obtidos a partir do ARASAAC. Verifique os termos de uso, créditos e exigências de atribuição da licença aplicável antes do uso institucional ampliado.
      </div>
    </body>
    </html>
    """



def generate_material_json(title: str, original_text: str, selected_items: List[Dict[str, Any]]) -> str:
    payload = {
        "title": title,
        "original_text": original_text,
        "items": selected_items,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
