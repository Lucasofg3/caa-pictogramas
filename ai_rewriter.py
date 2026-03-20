import json
import os
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _build_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def rewrite_for_caa_with_ai(text: str) -> Optional[Dict]:
    """
    Reescreve a frase em padrão CAA.
    Retorna:
    {
        "success": bool,
        "rewritten_text": str,
        "message": str
    }
    """
    client = _build_client()
    if client is None:
        return {
            "success": False,
            "rewritten_text": "",
            "message": "OPENAI_API_KEY não configurada. O sistema continuou apenas com regras locais."
        }

    model = os.getenv("OPENAI_MODEL", "").strip()
    if not model:
        return {
            "success": False,
            "rewritten_text": "",
            "message": "OPENAI_MODEL não configurado. O sistema continuou apenas com regras locais."
        }

    developer_prompt = """
Você é um assistente especializado em Comunicação Aumentativa e Alternativa (CAA) em português do Brasil.

Tarefa:
Reescreva a frase do usuário em um padrão CAA simples e direto.

Regras obrigatórias:
1. Use português do Brasil.
2. Preserve a intenção original.
3. Prefira frases curtas.
4. Evite vírgulas e pontuação desnecessária.
5. Use verbos no infinitivo.
6. Evite formalidades excessivas.
7. Não invente conteúdo que não esteja implícito.
8. Retorne JSON válido.

Formato de saída:
{
  "rewritten_text": "frase simplificada aqui",
  "notes": "explicação curta"
}
""".strip()

    user_prompt = f"Frase do usuário: {text}"

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "developer", "content": developer_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "caa_rewrite",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "rewritten_text": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["rewritten_text", "notes"],
                        "additionalProperties": False
                    }
                }
            }
        )

        raw_output = getattr(response, "output_text", "") or ""
        if not raw_output:
            return {
                "success": False,
                "rewritten_text": "",
                "message": "A IA não retornou conteúdo utilizável."
            }

        data = json.loads(raw_output)
        rewritten = (data.get("rewritten_text") or "").strip()

        if not rewritten:
            return {
                "success": False,
                "rewritten_text": "",
                "message": "A IA não retornou uma frase reescrita."
            }

        return {
            "success": True,
            "rewritten_text": rewritten,
            "message": data.get("notes", "")
        }

    except Exception as e:
        return {
            "success": False,
            "rewritten_text": "",
            "message": f"Falha na camada de IA: {str(e)}"
        }