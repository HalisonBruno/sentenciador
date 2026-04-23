"""DSL para estruturar sentenças.

Portado 1-para-1 do `sentenca.js` original do HalisonBruno. As funções
apenas *marcam* o tipo do parágrafo; a formatação fica em `gerador.py`.
"""

from __future__ import annotations

from typing import NamedTuple


class Bloco(NamedTuple):
    tipo: str   # "bp" | "cp" | "sh" | "ch" | "cc" | "el"
    texto: str


def bp(texto: str) -> Bloco:
    """Parágrafo de corpo: justificado, recuo 1ª linha 2,5cm, Times 12, 1,5."""
    return Bloco("bp", texto)


def cp(texto: str) -> Bloco:
    """Citação: justificada, recuo esq. 2,5cm, itálico, espaço antes/depois."""
    return Bloco("cp", texto)


def sh(texto: str) -> Bloco:
    """Subcabeçalho de seção: negrito, justificado, espaço antes."""
    return Bloco("sh", texto)


def ch(texto: str) -> Bloco:
    """Cabeçalho centralizado em negrito (RELATÓRIO, FUNDAMENTAÇÃO, etc)."""
    return Bloco("ch", texto)


def cc(texto: str) -> Bloco:
    """Texto centralizado simples (cabeçalho do processo, assinatura, data)."""
    return Bloco("cc", texto)


def el() -> Bloco:
    """Linha em branco."""
    return Bloco("el", "")
