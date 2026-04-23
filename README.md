# Sentenciador

Programa único que integra, via API Anthropic, os três passos do fluxo de
elaboração de sentença a partir de autos do SAJ:

1. **Pré-processamento do PDF** (baseado em
   [`processador-pdf-juridico`](https://github.com/HalisonBruno/processador-pdf-juridico)):
   recorte da tarja lateral do SAJ, OCR onde necessário, compressão.

2. **Redação da sentença pelo Claude** (via API com modelo Sonnet por padrão):
   PDF enviado como documento nativo, com system prompt que encapsula o estilo
   do juiz e o DSL; com `web_search` ativado para conferir literalidade de
   dispositivos legais citados.

3. **Geração do .docx forense** (portado de
   [`sentenca-docx`](https://github.com/HalisonBruno/sentenca-docx)): as seis
   funções do DSL original (bp/cp/sh/ch/cc/el) com formatação idêntica ao
   `sentenca.js`.

O ganho em tokens dos projetos do HalisonBruno é preservado: o PDF é
enviado já limpo (menos páginas, sem ruído), e o modelo produz apenas o
DSL compacto em Python, não o .docx/OpenXML.

## Instalação

### 1. Tesseract OCR (uma vez só)

- **Windows:** https://github.com/UB-Mannheim/tesseract/wiki (marcar idioma
  Portuguese durante a instalação).
- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-por`
- **macOS:** `brew install tesseract tesseract-lang`

### 2. Dependências Python

```bash
pip install -r requirements.txt
```

### 3. API key

Crie uma chave em https://console.anthropic.com. Ela é armazenada (em
`~/.sentenciador.json`) após a primeira execução bem-sucedida. O crédito
da API é **independente** da assinatura Claude Pro/Max.

## Uso

```bash
python app/gui.py
```

Na janela:

1. Cole a API key (só precisa da primeira vez).
2. Escolha o PDF dos autos.
3. Edite o campo de instruções específicas do caso (há um template com
   checklist que você pode adaptar ou apagar).
4. Clique em **▶ Gerar sentença**.

Três arquivos são criados ao lado do PDF original:

- `nome_limpo.pdf` — PDF pré-processado
- `nome_sentenca.py` — código no DSL (útil para revisar ou regenerar o
  .docx sem custo extra de API)
- `nome_sentenca.docx` — documento final no padrão forense

## Custo estimado por sentença

Variável conforme o tamanho dos autos. Referência para autos de ~50
páginas já processadas:

| Modelo | Input | Output | Custo aprox. (USD) |
|--------|-------|--------|--------------------|
| Sonnet 4.5 | ~30k tokens | ~2k tokens | ~$0,15 |
| Opus 4.x | ~30k tokens | ~2k tokens | ~$0,80 |

A ativação do `web_search` adiciona uma pequena taxa por consulta.

## Estrutura

```
sentenciador/
├── app/
│   ├── gui.py            # Tkinter; orquestra o pipeline
│   └── cliente_api.py    # SDK Anthropic + system prompt
├── processador_pdf/
│   └── processador.py    # OCR + recorte + compressão (módulo)
├── gerador_docx/
│   ├── dsl.py            # bp, cp, sh, ch, cc, el
│   └── gerador.py        # sandbox + python-docx
├── exemplos/
│   └── sentenca_exemplo.py
├── requirements.txt
└── README.md
```

## Ajuste do system prompt

O prompt com o estilo do juiz está em `app/cliente_api.py`, constante
`SYSTEM_PROMPT`. Foi montado a partir do `CLAUDE.md` do autor. Para
adequar ao seu próprio estilo de sentenciar, edite essa string.

## Notas sobre o comportamento esperado

- O modelo **não pergunta**: sempre devolve uma sentença completa. A
  instrução original ("pergunte ao usuário em caso de dúvida entre
  sanear e julgar antecipadamente") foi removida porque o fluxo é
  request/response único.
- O modelo **verifica a literalidade** dos dispositivos citados via
  `web_search` (planalto.gov.br e sites de tribunais superiores).
- O modelo **não inventa fatos**; se o PDF tiver páginas ilegíveis, faz
  a ressalva na fundamentação.
