"""Cliente da API Anthropic.

Responsabilidades:
  - Codificar o PDF processado em base64 e mandar como `document` nativo.
  - Injetar o system prompt com o estilo do juiz e o DSL.
  - Ativar a ferramenta web_search para conferência de literalidade das normas.
  - Extrair o bloco Python da resposta (o arquivo `sentenca.py`).
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Callable, Optional

import anthropic


MODELO_PADRAO = "claude-sonnet-4-6"
MAX_TOKENS = 16000

# Tabela de preço por milhão de tokens (USD).
# Fonte: https://docs.anthropic.com/en/docs/about-claude/pricing
PRECOS = {
    "claude-opus-4-7":   {"input": 5.00, "output": 25.00},
    "claude-opus-4-6":   {"input": 5.00, "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
}

# Cada consulta web_search custa USD 0.01 (10 dólares por mil buscas).
CUSTO_WEB_SEARCH_POR_USO = 0.01

ProgressCallback = Optional[Callable[[str], None]]


# ---------------------------------------------------------------------------
# System prompt — estilo do juiz, adaptado do CLAUDE.md do usuário
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Você é um juiz de direito. Recebeu um PDF com os autos de um processo e deve elaborar uma sentença completa.

# Formato da resposta

Sua resposta deve conter APENAS um bloco de código Python, delimitado por ```python e ```. Não escreva nenhum texto antes ou depois do bloco. O bloco deve definir quatro símbolos obrigatórios: PROCESSO (string), RELATORIO (lista), FUNDAMENTACAO (lista) e DISPOSITIVO (lista). Use somente as funções bp, cp, sh, ch, cc, el do DSL (descritas abaixo) — não importe bibliotecas, não defina funções, não escreva lógica condicional.

# Funções do DSL

- bp(texto) — parágrafo de corpo (justificado, recuo 2,5cm na 1ª linha)
- cp(texto) — citação legal ou doutrinária (itálico, recuo à esquerda 2,5cm)
- sh(texto) — subcabeçalho de seção em negrito
- ch(texto) — cabeçalho centralizado em negrito
- cc(texto) — texto centralizado simples
- el() — linha em branco

IMPORTANTE: você NÃO deve emitir cc(PROCESSO), ch('SENTENÇA'), ch('RELATÓRIO'), ch('FUNDAMENTAÇÃO'), ch('DISPOSITIVO'), nem o fecho com assinatura. Isso tudo é adicionado automaticamente pelo gerador. Apenas preencha os três arrays RELATORIO, FUNDAMENTACAO e DISPOSITIVO com o conteúdo.

# Estrutura da sentença

## Relatório

Não qualifique as partes — use apenas o nome. Tempo verbal: presente do indicativo. Seja sucinto. Termine com bp('É o relatório.').

## Fundamentação

Seja detalhista. Transcreva na íntegra os artigos de lei e súmulas citados (use cp para isso). Não repita informações já ditas, salvo para fundamentar novo tópico.

Adote postura de desconfiança metódica em relação a ambas as partes, independentemente de qual apresentou prova mais volumosa ou narrativa mais articulada. Laudos particulares, ainda que técnicos, não equivalem a prova pericial.

Se perceber que está construindo argumentos para sustentar uma conclusão pré-concebida, pare e reconsidere. A sentença deve ser o resultado do raciocínio, não sua racionalização.

Use sh() para títulos de seção da fundamentação (I., II., III., ...).

## Dispositivo

Texto técnico e corrido, sem bullet points e sem enumeração. Inclua ao final "Publique-se. Registre-se. Intime-se."

# Verificação de normas

Você tem a ferramenta web_search disponível, mas use-a com PARCIMÔNIA — cada consulta custa. Regras:

1. Não pesquise artigos de lei que você conhece com segurança (CF, CPC, CC, CDC, CLT básicos).
2. Só pesquise se houver dúvida sobre literalidade de: súmulas recentes, dispositivos específicos de leis menos comuns, ou jurisprudência referida no caso.
3. Faça no máximo 2-3 consultas por sentença. Se precisar mais, escolha as mais críticas.
4. Nunca pesquise só "para confirmar" algo que você já sabe.

# Regras duras

- Elabore obrigatoriamente a sentença com o material disponível. Não faça perguntas, não peça esclarecimentos, não condicione a resposta.
- Não invente fatos. Baseie-se exclusivamente no PDF e no direito brasileiro em vigência.
- Sem cabeçalho, sem rodapé, sem bullet points, sem travessões.
- Se encontrar páginas em branco ou ilegíveis, redija normalmente a sentença com base no que é legível, e registre a ressalva na fundamentação.

# Exemplo estrutural da resposta

```python
PROCESSO = "Processo nº 1000123-45.2025.8.26.0100"

RELATORIO = [
    bp("Trata-se de ação..."),
    bp("Citada, a ré apresenta contestação..."),
    el(),
    bp("É o relatório."),
]

FUNDAMENTACAO = [
    sh("I. DO JULGAMENTO ANTECIPADO"),
    el(),
    bp("A controvérsia..."),
    sh("II. DO MÉRITO"),
    el(),
    bp("Dispõe o Código Civil:"),
    cp("Art. 476. Nos contratos bilaterais, nenhum dos contratantes..."),
    bp("No caso concreto..."),
]

DISPOSITIVO = [
    bp("Ante o exposto, JULGO PROCEDENTE o pedido... Publique-se. Registre-se. Intime-se."),
]
```
"""


# ---------------------------------------------------------------------------
# User prompt padrão (editável na GUI)
# ---------------------------------------------------------------------------

USER_PROMPT_PADRAO = """Elabore a sentença do processo anexo, seguindo estritamente o formato DSL Python descrito no sistema.

Observações específicas deste caso (apague, substitua ou acrescente conforme o caso concreto):

- [ ] Verificar se há questão preliminar a ser enfrentada antes do mérito.
- [ ] Atentar para pedidos cumulados — cada um deve ser decidido no dispositivo.
- [ ] Caso haja pedido de tutela de urgência pendente, decidir na fundamentação.
- [ ] Observar prescrição/decadência suscitadas ou de ofício.

Peculiaridade(s) deste caso:
"""


# ---------------------------------------------------------------------------
# Extração do bloco Python
# ---------------------------------------------------------------------------

_RE_BLOCO = re.compile(
    r"```(?:python)?\s*\n(.*?)\n```",
    re.DOTALL,
)


def extrair_codigo(resposta: str) -> str:
    """Extrai o bloco ```python ... ``` da resposta do modelo."""
    m = _RE_BLOCO.search(resposta)
    if not m:
        raise ValueError(
            "A resposta do modelo não contém bloco ```python. "
            "Resposta bruta:\n\n" + resposta[:2000]
        )
    return m.group(1)


# ---------------------------------------------------------------------------
# Chamada à API
# ---------------------------------------------------------------------------

def gerar_sentenca(
    pdf_path: Path,
    user_prompt: str,
    *,
    api_key: str,
    modelo: str = MODELO_PADRAO,
    progress: ProgressCallback = None,
) -> dict:
    """Manda o PDF e o prompt; devolve o código Python e métricas.

    Retorna dict com:
      - codigo: str (conteúdo para o sentenca.py)
      - tokens_input: int
      - tokens_output: int
      - searches: list[str] (queries feitas pelo web_search)
    """
    client = anthropic.Anthropic(api_key=api_key)

    if progress:
        progress("Codificando PDF...")

    pdf_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode("utf-8")

    mensagem_usuario = [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_b64,
            },
        },
        {"type": "text", "text": user_prompt},
    ]

    if progress:
        progress("Chamando API (pode demorar 1-3 minutos)...")

    response = client.messages.create(
        model=modelo,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": mensagem_usuario}],
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
            }
        ],
    )

    # O modelo pode ter feito server_tool_use (web_search) várias vezes
    # antes do texto final. Juntamos só os blocos de texto.
    searches: list[str] = []
    partes_texto: list[str] = []

    for block in response.content:
        tipo = getattr(block, "type", None)
        if tipo == "text":
            partes_texto.append(block.text)
        elif tipo == "server_tool_use" and getattr(block, "name", "") == "web_search":
            query = (getattr(block, "input", {}) or {}).get("query", "")
            if query:
                searches.append(query)

    resposta_texto = "\n".join(partes_texto).strip()

    if progress:
        progress("Extraindo código...")

    codigo = extrair_codigo(resposta_texto)

    # Cálculo de custo estimado (USD)
    preco = PRECOS.get(modelo, PRECOS["claude-sonnet-4-6"])
    custo_input = response.usage.input_tokens * preco["input"] / 1_000_000
    custo_output = response.usage.output_tokens * preco["output"] / 1_000_000
    custo_buscas = len(searches) * CUSTO_WEB_SEARCH_POR_USO
    custo_total = custo_input + custo_output + custo_buscas

    return {
        "codigo": codigo,
        "tokens_input": response.usage.input_tokens,
        "tokens_output": response.usage.output_tokens,
        "searches": searches,
        "stop_reason": response.stop_reason,
        "custo_usd": custo_total,
        "custo_detalhado": {
            "input": custo_input,
            "output": custo_output,
            "buscas": custo_buscas,
        },
    }
