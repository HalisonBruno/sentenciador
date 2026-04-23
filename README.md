> **[⬇ Baixar o executável (v1.0.0)](https://github.com/HalisonBruno/sentenciador/releases/latest)** — Windows, 100+ MB, não precisa instalar Python

# Sentenciador

> Programa único que integra pré-processamento de PDFs do SAJ, redação
> assistida pelo Claude e geração de `.docx` forense em um só clique.


## O que ele faz

Você solta o PDF dos autos na janela e, em poucos minutos, recebe uma
sentença pronta em Word, formatada no padrão forense, com relatório,
fundamentação e dispositivo. Sem copy-paste, sem editor externo, sem
conversão manual.

O programa internaliza três ferramentas em um único fluxo:

1. **Pré-processamento do PDF** — recorta a tarja lateral do SAJ, aplica
   OCR nas páginas escaneadas (RGs, contratos, matrículas) e comprime
   imagens, reduzindo o arquivo em até 70%.

2. **Redação pela API do Claude** — envia o PDF já limpo como documento
   nativo, com system prompt que encapsula o estilo do juiz e as regras
   forenses.

3. **Geração do `.docx`** — converte a sentença estruturada em documento
   Word com fonte Times New Roman 12, recuo 2,5 cm, espaçamento 1,5,
   citações em itálico, cabeçalhos centralizados em negrito, fecho com
   linha de assinatura.

## Qualidades

### Integração total — um clique, uma sentença

Entrada: PDF dos autos. Saída: `sentenca.docx` pronto para assinar.
Pré-processamento, chamada à IA, geração do Word: tudo automatizado.

### Compatível com as versões mais recentes do Claude

O programa suporta, via menu dropdown na interface, todas as versões
modernas do Claude disponíveis na API Anthropic:

| Modelo | Força | Custo input/output (USD por milhão tokens) |
|--------|-------|--------------------------------------------|
| **Claude Opus 4.7** | Máxima qualidade em raciocínio jurídico | 5,00 / 25,00 |
| **Claude Opus 4.6** | Versão anterior do Opus, ainda excelente | 5,00 / 25,00 |
| **Claude Sonnet 4.6** | Equilíbrio entre qualidade e custo | 3,00 / 15,00 |
| **Claude Sonnet 4.5** | Versão anterior do Sonnet | 3,00 / 15,00 |

Troque o modelo a qualquer momento, sem reiniciar. Use Sonnet para casos
simples, Opus para os complexos — você escolhe caso a caso.

### Sistema de verificação normativa via web search

Quando o modelo cita um dispositivo legal ou súmula, pode consultar a
base oficial (planalto.gov.br, sites de tribunais superiores) para
conferir a literalidade antes de escrever. O uso é parcimonioso: no
máximo 2-3 consultas por sentença, apenas em casos de dúvida real.

### Pré-processamento inteligente de PDFs

Autos do SAJ vêm com tarja lateral de assinatura eletrônica, cabeçalhos
e rodapés, e páginas escaneadas sem camada de texto (o que impede busca
por termos). O programa:

- **Recorta** as margens do SAJ com medidas calibradas, eliminando ruído
  sem perder conteúdo
- **Detecta** automaticamente páginas escaneadas (analisando o miolo
  útil da página, ignorando cabeçalho e tarja)
- **Aplica OCR** em português (Tesseract) com camada de texto invisível,
  preservando a aparência visual do documento
- **Comprime** imagens embutidas (JPEG qualidade 65, máximo 1400 px),
  reduzindo o arquivo de dezenas para poucos MB

### Estilo personalizável

O `system prompt` — o arquivo que define como o juiz redige — é uma
string editável em `app/cliente_api.py`. Você ajusta uma vez e passa a
ser replicado em toda sentença:

- Convenções de abertura do relatório
- Formato do dispositivo
- Critério de fixação de honorários
- Quando julgar antecipadamente
- Postura de desconfiança metódica quanto às provas

### Instruções específicas por caso

Antes de cada geração, um campo editável na GUI permite acrescentar
peculiaridades: "atentar para prescrição intercorrente", "pedido de
tutela pendente", "réu revel", etc. Um checklist padrão já vem
preenchido — adapte ou apague.

### Economia de tokens

Três decisões de arquitetura preservam economia sobre alternativas
ingênuas:

- O PDF é enviado **já limpo** pelo pré-processador (menos páginas, sem
  ruído, menos tokens)
- O modelo retorna a sentença em **DSL Python compacto** (`bp`, `cp`,
  `sh`, `ch`, `cc`, `el`), não em OpenXML verboso
- A **formatação forense** é aplicada localmente pelo gerador, não
  repetida pelo modelo em cada parágrafo

### Transparência de custo

Após cada geração, o log exibe:

- Tokens de input consumidos
- Tokens de output gerados
- Consultas web_search realizadas (com as queries)
- **Custo estimado em USD** (calculado com a tabela oficial da Anthropic)

Você sabe exatamente quanto custou cada sentença antes mesmo de olhar o
console da API.

### Segurança

- A chave da API é armazenada localmente (`~/.sentenciador.json`) e
  nunca enviada a nenhum servidor além da Anthropic
- O arquivo `sentenca.py` gerado é executado em **sandbox** com
  `__builtins__` restrito — sem `import`, sem `open()`, sem acesso a
  sistema de arquivos
- PDFs de casos reais ficam de fora do repositório pelo `.gitignore`

## Instalação

### 1. Python 3.10+

Se ainda não tiver:

```powershell
winget install Python.Python.3.12
```

### 2. Tesseract OCR com português

- Windows: https://github.com/UB-Mannheim/tesseract/wiki (marcar
  idioma Portuguese durante o instalador)
- Linux: `sudo apt install tesseract-ocr tesseract-ocr-por`
- macOS: `brew install tesseract tesseract-lang`

### 3. Clonar e instalar

```powershell
git clone https://github.com/HalisonBruno/sentenciador.git
cd sentenciador
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Chave da API

Obtenha em https://console.anthropic.com (adicione crédito em
*Settings → Billing*; mínimo de US$ 5 para começar). A chave é
independente da sua assinatura Claude Pro/Max.

## Uso

```powershell
python app\gui.py
```

Na primeira execução, cole a chave da API — ela fica salva para os
próximos usos. Depois é só escolher o PDF dos autos, ajustar o prompt do
caso se houver peculiaridade, e clicar em **▶ Gerar sentença**.

Três arquivos são criados ao lado do PDF original:

- `{nome}_limpo.pdf` — PDF pré-processado
- `{nome}_sentenca.py` — código no DSL (útil para regenerar o `.docx`
  ajustando parágrafos sem gastar API de novo)
- `{nome}_sentenca.docx` — sentença final

## Empacotamento como `.exe`

Para distribuir como executável Windows:

```powershell
pip install pyinstaller
pyinstaller --onefile --noconsole --name Sentenciador --collect-all anthropic --collect-all fitz app\gui.py
```

O executável fica em `dist\Sentenciador.exe`. Crie um atalho na área de
trabalho apontando para ele. O Tesseract precisa continuar instalado na
máquina.

## Estrutura

```
sentenciador/
├── app/
│   ├── gui.py            # Tkinter; orquestra o pipeline
│   └── cliente_api.py    # SDK Anthropic + system prompt
├── processador_pdf/
│   └── processador.py    # OCR + recorte + compressão
├── gerador_docx/
│   ├── dsl.py            # bp, cp, sh, ch, cc, el
│   └── gerador.py        # sandbox + python-docx
├── exemplos/
│   └── sentenca_exemplo.py
├── requirements.txt
└── README.md
```

## Base técnica

Este projeto reúne, estende e integra via API Anthropic duas ferramentas
anteriores do autor:

- [processador-pdf-juridico](https://github.com/HalisonBruno/processador-pdf-juridico)
  — recorte, OCR e compressão do PDF
- [sentenca-docx](https://github.com/HalisonBruno/sentenca-docx) — DSL
  para gerar `.docx` forense a partir de estrutura compacta

Enquanto as ferramentas anteriores exigiam três passos manuais e copy-
paste com o Claude no meio, este programa elimina todo o atrito,
trocando interação humana por custo de API controlado e transparente.

## Licença

MIT