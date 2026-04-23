"""Processador de PDFs do SAJ.

Portado FIELMENTE de HalisonBruno/processador-pdf-juridico. Única alteração:
vira módulo importável (com callback de progresso) em vez de app Tkinter
próprio. Valores de corte, lógica do cropbox, detecção de OCR por "miolo"
da página e compressão JPEG: idênticos ao original.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Callable, Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image


# ====== CONFIGURAÇÃO DO TESSERACT ======
# No Windows, o instalador do UB-Mannheim coloca o binário aqui por padrão.
# Se seu caminho for outro, edite abaixo ou defina a variável TESSERACT_CMD.
_TESSERACT_WIN_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == "nt" and Path(_TESSERACT_WIN_DEFAULT).exists():
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_WIN_DEFAULT
elif os.environ.get("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
# =========================================


# Conversão cm → pontos PDF (1 cm ≈ 28,35 pontos).
_PT = 28.35

# Valores padrão idênticos ao original HalisonBruno/processador-pdf-juridico.
# A tarja lateral do SAJ fica à DIREITA da página; por isso "direita=1.72".
CORTE_ESQUERDA_CM_PADRAO = 0.00
CORTE_DIREITA_CM_PADRAO = 1.72
CORTE_TOPO_CM_PADRAO = 0.69
CORTE_BAIXO_CM_PADRAO = 0.76

MAX_DIM_PX_PADRAO = 1400
JPEG_QUALITY_PADRAO = 65

# Para detecção de OCR: menos de 40 caracteres no MIOLO da página (já
# descontadas as laterais e cabeçalho/rodapé) → é scan sem camada de texto.
MIN_CHARS_MIOLO = 40

ProgressCallback = Optional[Callable[[str], None]]


# ---------------------------------------------------------------------------
# Detecção de páginas que precisam de OCR
# ---------------------------------------------------------------------------

def _pagina_precisa_ocr(page: fitz.Page, minimo_chars: int = MIN_CHARS_MIOLO) -> bool:
    """Detecta se a página é essencialmente uma imagem escaneada.

    Ignora o texto das laterais do SAJ (tarja de protocolo) e do
    cabeçalho/rodapé. Conta apenas texto no "miolo" da página.
    """
    rect = page.rect
    miolo = fitz.Rect(
        rect.x0 + rect.width * 0.15,
        rect.y0 + rect.height * 0.08,
        rect.x1 - rect.width * 0.15,
        rect.y1 - rect.height * 0.08,
    )
    texto_miolo = page.get_text(clip=miolo).strip()
    return len(texto_miolo) < minimo_chars


# ---------------------------------------------------------------------------
# OCR com camada de texto invisível (preserva o visual da imagem)
# ---------------------------------------------------------------------------

def _fazer_ocr_pagina(page: fitz.Page) -> None:
    """Renderiza a página, faz OCR e insere camada de texto invisível."""
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))

    pdf_ocr_bytes = pytesseract.image_to_pdf_or_hocr(
        img, lang="por", extension="pdf"
    )
    ocr_doc = fitz.open(stream=pdf_ocr_bytes, filetype="pdf")
    try:
        ocr_page = ocr_doc[0]
        # pixmap gerado a 300dpi; PDF user-space é 72dpi: fator 72/300.
        escala = 72 / 300

        for block in ocr_page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    texto = span["text"]
                    if not texto.strip():
                        continue
                    bbox = span["bbox"]
                    x0 = bbox[0] * escala
                    y0 = bbox[1] * escala
                    x1 = bbox[2] * escala
                    y1 = bbox[3] * escala
                    try:
                        page.insert_text(
                            (x0, y1),
                            texto,
                            fontsize=max((y1 - y0) * 0.9, 1),
                            render_mode=3,  # texto invisível
                            color=(0, 0, 0),
                        )
                    except Exception:
                        # alguns glyphs podem falhar; seguimos adiante
                        pass
    finally:
        ocr_doc.close()


# ---------------------------------------------------------------------------
# Compressão de imagens embutidas
# ---------------------------------------------------------------------------

def _comprimir_imagens(
    doc: fitz.Document,
    max_dim_px: int,
    jpeg_quality: int,
) -> None:
    """Redimensiona imagens maiores que max_dim_px e re-salva como JPEG."""
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            try:
                base = doc.extract_image(xref)
                pil = Image.open(io.BytesIO(base["image"]))
                w, h = pil.size
                if max(w, h) <= max_dim_px:
                    continue
                ratio = max_dim_px / max(w, h)
                pil = pil.resize(
                    (int(w * ratio), int(h * ratio)),
                    Image.LANCZOS,
                )
                if pil.mode != "RGB":
                    pil = pil.convert("RGB")
                buf = io.BytesIO()
                pil.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                page.replace_image(xref, stream=buf.getvalue())
            except Exception:
                # se uma imagem específica falhar, ignora e continua
                pass


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def processar_pdf(
    entrada: Path,
    saida: Path,
    *,
    corte_esquerda_cm: float = CORTE_ESQUERDA_CM_PADRAO,
    corte_direita_cm: float = CORTE_DIREITA_CM_PADRAO,
    corte_topo_cm: float = CORTE_TOPO_CM_PADRAO,
    corte_baixo_cm: float = CORTE_BAIXO_CM_PADRAO,
    max_dim_px: int = MAX_DIM_PX_PADRAO,
    jpeg_quality: int = JPEG_QUALITY_PADRAO,
    aplicar_recorte: bool = True,
    aplicar_ocr: bool = True,
    aplicar_compressao: bool = True,
    progress: ProgressCallback = None,
) -> dict:
    """Executa o pipeline completo e devolve métricas.

    Ordem (importante, seguindo o original):
        1. Recorte  (aproveita área útil da página)
        2. OCR      (com pixmap em alta resolução, ANTES da compressão)
        3. Compressão (por último, não afeta o OCR já inserido)
    """
    doc = fitz.open(entrada)
    total = len(doc)
    paginas_ocr = 0

    if progress:
        progress(f"Abrindo: {total} páginas")

    # === 1) RECORTE ===
    # Nota: o Rect original é montado como:
    #     Rect(x0 + esquerda, y0 + BAIXO, x1 - direita, y1 - TOPO)
    # Parece trocado mas é proposital: "topo" e "baixo" referem-se ao quanto
    # cortar do topo e fundo VISUAIS da folha; em coordenadas PyMuPDF
    # (MediaBox), y0 é o topo do papel — então o recorte superior (visual)
    # usa y1 - TOPO, e o cropbox inicia em y0 + BAIXO. NÃO INVERTA.
    if aplicar_recorte:
        if progress:
            progress(
                f"Recortando: esq={corte_esquerda_cm} dir={corte_direita_cm} "
                f"topo={corte_topo_cm} baixo={corte_baixo_cm} (cm)"
            )
        for page in doc:
            mb = page.mediabox
            novo = fitz.Rect(
                mb.x0 + corte_esquerda_cm * _PT,
                mb.y0 + corte_baixo_cm * _PT,
                mb.x1 - corte_direita_cm * _PT,
                mb.y1 - corte_topo_cm * _PT,
            )
            page.set_cropbox(novo)

    # === 2) OCR ===
    if aplicar_ocr:
        for i, page in enumerate(doc, start=1):
            if _pagina_precisa_ocr(page):
                if progress:
                    progress(f"Página {i}/{total}: OCR")
                try:
                    _fazer_ocr_pagina(page)
                    paginas_ocr += 1
                except Exception as e:
                    if progress:
                        progress(f"  ⚠ Erro OCR pág {i}: {e}")
            else:
                if progress and (i % 10 == 0 or i == total):
                    progress(f"Página {i}/{total}: texto nativo")

    # === 3) COMPRESSÃO ===
    if aplicar_compressao:
        if progress:
            progress(
                f"Comprimindo imagens (máx {max_dim_px}px, JPEG q={jpeg_quality})"
            )
        _comprimir_imagens(doc, max_dim_px, jpeg_quality)

    # === Salvar ===
    saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(saida, garbage=4, deflate=True, clean=True)
    doc.close()

    tam_in = entrada.stat().st_size / 1024 / 1024
    tam_out = saida.stat().st_size / 1024 / 1024
    reducao = (1 - tam_out / tam_in) * 100 if tam_in else 0.0

    if progress:
        progress(
            f"✓ {tam_in:.1f} MB → {tam_out:.1f} MB "
            f"({reducao:.0f}% menor) · {paginas_ocr} pág(s) com OCR"
        )

    return {
        "paginas_total": total,
        "paginas_ocr": paginas_ocr,
        "tamanho_in_mb": tam_in,
        "tamanho_out_mb": tam_out,
        "reducao_pct": reducao,
    }
