**[Leia em Português 🇧🇷](README.pt-BR.md)**

> **[⬇ Download the executable (v1.0.0)](https://github.com/HalisonBruno/sentenciador/releases/latest)** — Windows, 100+ MB, no Python install required

# Sentenciador

> A single desktop program that integrates SAJ court-case PDF pre-processing,
> AI-assisted drafting via Claude, and generation of court-ready `.docx`
> rulings — in one click.

## What it does

Drop the court-case PDF into the window and, in a few minutes, you get a
ready ruling in Word format, styled according to Brazilian legal standards,
with sections for Report, Reasoning, and Decision. No copy-paste, no
external editor, no manual conversion.

The program chains three tools into a single flow:

1. **PDF pre-processing** — crops the SAJ side watermark, applies OCR to
   scanned pages (IDs, contracts, property records) and compresses images,
   reducing file size by up to 70%.

2. **AI drafting via Claude API** — sends the cleaned PDF as a native
   document, with a system prompt that encapsulates the judge's writing
   style and Brazilian legal-drafting conventions.

3. **.docx generation** — converts the structured ruling into a Word
   document with Times New Roman 12, 2.5cm indent, 1.5 line spacing,
   italic citations, centered bold headings, and a signature line.

## Highlights

### Full integration — one click, one ruling

Input: court-case PDF. Output: `ruling.docx` ready to sign.
Pre-processing, AI call, Word generation: all automated.

### Supports the latest Claude models

The program lets you pick, via a dropdown in the GUI, any modern Claude
model available on the Anthropic API:

| Model | Strength | Input/Output cost (USD per million tokens) |
|-------|----------|--------------------------------------------|
| **Claude Opus 4.7** | Top-tier legal reasoning | 5.00 / 25.00 |
| **Claude Opus 4.6** | Previous Opus, still excellent | 5.00 / 25.00 |
| **Claude Sonnet 4.6** | Best quality/cost balance | 3.00 / 15.00 |
| **Claude Sonnet 4.5** | Previous Sonnet | 3.00 / 15.00 |

Switch models on the fly — no restart needed. Use Sonnet for simple
cases, Opus for complex ones — case by case.

### Legal-source verification via web search

When the model cites a statute or binding precedent, it can consult
official sources (planalto.gov.br, supreme-court websites) to confirm
exact wording before drafting. Usage is frugal: at most 2-3 queries per
ruling, only in cases of real doubt.

### Smart PDF pre-processing

SAJ court-case PDFs come bundled with side watermarks for electronic
signature, headers, footers, and scanned pages without a text layer
(which blocks keyword search). The program:

- **Crops** SAJ margins with calibrated measurements, removing noise
  without losing content
- **Detects** scanned pages automatically (analyzing the useful page
  area, ignoring header and watermark)
- **Applies OCR** in Portuguese (Tesseract) as an invisible text layer,
  preserving the document's visual appearance
- **Compresses** embedded images (JPEG quality 65, max 1400px), bringing
  files down from tens to a few MB

### Customizable style

The `system prompt` — the file that defines how the judge writes — is an
editable string in `app/cliente_api.py`. Tune it once, and it's applied
to every ruling:

- Report-opening conventions
- Decision formatting
- Legal-fee criteria
- When to rule on summary judgment
- Methodical skepticism toward evidence

### Per-case instructions

Before each generation, an editable field in the GUI lets you add
case-specific notes: "watch for intercurrent prescription," "pending
injunction request," "defendant in default," etc. A default checklist
comes pre-filled — adapt or clear it.

### Token efficiency

Three architectural choices save tokens over naive alternatives:

- The PDF is sent **already cleaned** by the pre-processor (fewer pages,
  no noise, fewer tokens)
- The model returns the ruling in a **compact Python DSL** (`bp`, `cp`,
  `sh`, `ch`, `cc`, `el`), not verbose OpenXML
- **Legal formatting** is applied locally by the generator, not repeated
  by the model in every paragraph

### Cost transparency

After each generation, the log displays:

- Input tokens consumed
- Output tokens generated
- Web search queries made (with the queries themselves)
- **Estimated cost in USD** (calculated with Anthropic's official pricing)

You know exactly how much each ruling cost before even opening the API
console.

### Security

- The API key is stored locally (`~/.sentenciador.json`) and never sent
  to any server other than Anthropic
- The generated `sentenca.py` file runs in a **sandbox** with restricted
  `__builtins__` — no `import`, no `open()`, no filesystem access
- Real case PDFs are excluded from the repository via `.gitignore`

## Installation

### 1. Python 3.10+

If you don't have it:

```powershell
winget install Python.Python.3.12
```

### 2. Tesseract OCR with Portuguese

- Windows: https://github.com/UB-Mannheim/tesseract/wiki (check the
  Portuguese option during install)
- Linux: `sudo apt install tesseract-ocr tesseract-ocr-por`
- macOS: `brew install tesseract tesseract-lang`

### 3. Clone and install

```powershell
git clone https://github.com/HalisonBruno/sentenciador.git
cd sentenciador
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. API key

Get one at https://console.anthropic.com (add credit in *Settings →
Billing*; minimum USD 5 to start). This API key is separate from any
Claude Pro/Max subscription.

## Usage

```powershell
python app\gui.py
```

On first run, paste the API key — it's saved for future sessions. Then
pick the court-case PDF, adjust the case-specific prompt if needed, and
click **▶ Gerar sentença** (Generate ruling).

Three files are created next to the original PDF:

- `{name}_limpo.pdf` — pre-processed PDF
- `{name}_sentenca.py` — DSL code (useful to regenerate the `.docx` with
  tweaks, without spending API tokens again)
- `{name}_sentenca.docx` — final ruling

## Building a Windows .exe

To distribute as a standalone Windows executable:

```powershell
pip install pyinstaller
pyinstaller --onefile --noconsole --name Sentenciador --collect-all anthropic --collect-all fitz app\gui.py
```

The executable is generated at `dist\Sentenciador.exe`. Create a desktop
shortcut pointing to it. Tesseract still needs to be installed on the
machine.

## Project structure

```
sentenciador/
├── app/
│   ├── gui.py            # Tkinter; orchestrates the pipeline
│   └── cliente_api.py    # Anthropic SDK + system prompt
├── processador_pdf/
│   └── processador.py    # OCR + cropping + compression
├── gerador_docx/
│   ├── dsl.py            # bp, cp, sh, ch, cc, el
│   └── gerador.py        # sandbox + python-docx
├── exemplos/
│   └── sentenca_exemplo.py
├── requirements.txt
└── README.md
```

## Technical foundation

This project gathers, extends, and integrates via Anthropic API two
earlier tools by the author:

- [processador-pdf-juridico](https://github.com/HalisonBruno/processador-pdf-juridico)
  — PDF cropping, OCR, and compression
- [sentenca-docx](https://github.com/HalisonBruno/sentenca-docx) — DSL
  for generating court-ready `.docx` from compact structured input

While the earlier tools required three manual steps with copy-paste
through Claude in between, this program eliminates all that friction,
trading human interaction for controlled, transparent API cost.

## License

MIT
