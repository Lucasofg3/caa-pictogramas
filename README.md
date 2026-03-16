# Gerador de Materiais com Pictogramas (Protótipo MVP)

Protótipo em **Streamlit** para apoiar professores na produção de materiais com pictogramas voltados à CAA (Comunicação Aumentativa e Alternativa).

## O que este projeto faz

- recebe um texto do professor;
- extrai palavras-chave úteis para apoio visual;
- busca pictogramas no ARASAAC;
- permite revisar a sugestão visual termo a termo;
- gera uma prancha simples em HTML;
- exporta um arquivo `.json` com o material montado.

## Estrutura do projeto

```text
caa-pictogramas/
  app.py
  requirements.txt
  .env.example
  README.md
  services/
    arasaac_api.py
  utils/
    nlp.py
    export.py
```

## Pré-requisitos

1. Python 3.11 ou 3.12 instalado.
2. VS Code ou outro editor.
3. Terminal / Prompt de Comando.

## Passo a passo para rodar

### 1) Criar ambiente virtual

No terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
```

### 2) Ativar o ambiente virtual

No Windows:

```bash
.venv\Scripts\activate
```

No macOS/Linux:

```bash
source .venv/bin/activate
```

### 3) Instalar dependências

```bash
pip install -r requirements.txt
```

### 4) Criar o arquivo .env

Copie o arquivo `.env.example` e renomeie para `.env`.

No Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

No macOS/Linux:

```bash
cp .env.example .env
```

### 5) Rodar o app

```bash
streamlit run app.py
```

Se o navegador não abrir sozinho, acesse o endereço mostrado no terminal, normalmente:

```text
http://localhost:8501
```

## Como usar

1. Digite ou cole um texto.
2. Clique em **Gerar sugestões**.
3. Revise os pictogramas sugeridos para cada termo.
4. Baixe a prancha em HTML.
5. Baixe também o JSON do material, se quiser guardar a estrutura.

## Observação importante sobre a API

Os endpoints do ARASAAC foram deixados configuráveis no `.env`, porque a documentação pública pode mudar e alguns exemplos públicos usam rotas diferentes. Se a busca não funcionar, ajuste os templates no `.env` conforme a documentação oficial.

## Próximas melhorias sugeridas

- expressões compostas (`lavar as mãos`, `guardar material`);
- sinônimos e dicionário pedagógico próprio;
- categorias escolares;
- exportação em PDF;
- histórico de materiais;
- perfis por estudante.

## Licença e créditos

Verifique os termos e a licença de uso do ARASAAC antes de uso institucional ampliado. O protótipo já inclui uma referência textual no HTML exportado, mas você pode ajustar a atribuição conforme a política oficial do serviço.
