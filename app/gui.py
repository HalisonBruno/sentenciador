"""GUI do Sentenciador.

Um clique: escolhe PDF dos autos, edita instruções específicas do caso,
clica em "Gerar". O app processa o PDF, chama a API, gera o .docx.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import traceback
from pathlib import Path
from tkinter import (
    Tk, filedialog, messagebox, ttk, scrolledtext,
    StringVar, BooleanVar, END, DISABLED, NORMAL,
)

# Garante que conseguimos importar os outros módulos do projeto
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "processador_pdf"))
sys.path.insert(0, str(RAIZ / "gerador_docx"))
sys.path.insert(0, str(RAIZ / "app"))

from cliente_api import (  # noqa: E402
    MODELO_PADRAO, USER_PROMPT_PADRAO, gerar_sentenca,
)
from gerador import carregar_sentenca, gerar  # noqa: E402
from processador import processar_pdf  # noqa: E402


CONFIG_PATH = Path.home() / ".sentenciador.json"


# ---------------------------------------------------------------------------
# Persistência de configurações
# ---------------------------------------------------------------------------

def carregar_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def salvar_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class Sentenciador:

    def __init__(self, root: Tk) -> None:
        self.root = root
        self.cfg = carregar_config()

        root.title("Sentenciador")
        root.geometry("820x720")

        # Variáveis
        self.var_pdf = StringVar(value="")
        self.var_api_key = StringVar(value=self.cfg.get("api_key", ""))
        self.var_modelo = StringVar(value=self.cfg.get("modelo", MODELO_PADRAO))
        self.var_cidade = StringVar(value=self.cfg.get("cidade", "São Paulo"))
        self.var_pular_proc = BooleanVar(value=False)
        self.var_status = StringVar(value="Pronto.")

        self._montar_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _montar_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # Configurações (API key, modelo, cidade)
        grp_cfg = ttk.LabelFrame(main, text="Configuração", padding=8)
        grp_cfg.pack(fill="x", pady=(0, 8))

        ttk.Label(grp_cfg, text="API Key:").grid(row=0, column=0, sticky="w")
        entry_key = ttk.Entry(grp_cfg, textvariable=self.var_api_key,
                              width=55, show="•")
        entry_key.grid(row=0, column=1, sticky="we", padx=4)

        ttk.Label(grp_cfg, text="Modelo:").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            grp_cfg, textvariable=self.var_modelo,
            values=[
                "claude-sonnet-4-6",
                "claude-opus-4-7",
                "claude-opus-4-6",
                "claude-sonnet-4-5",
            ],
            width=25, state="readonly",
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))

        ttk.Label(grp_cfg, text="Cidade (fecho):").grid(row=2, column=0,
                                                       sticky="w")
        ttk.Entry(grp_cfg, textvariable=self.var_cidade, width=30).grid(
            row=2, column=1, sticky="w", padx=4, pady=(4, 0),
        )

        grp_cfg.columnconfigure(1, weight=1)

        # PDF
        grp_pdf = ttk.LabelFrame(main, text="PDF dos autos", padding=8)
        grp_pdf.pack(fill="x", pady=(0, 8))

        ttk.Entry(grp_pdf, textvariable=self.var_pdf).pack(
            side="left", fill="x", expand=True, padx=(0, 4),
        )
        ttk.Button(grp_pdf, text="Escolher...",
                   command=self._escolher_pdf).pack(side="left")

        ttk.Checkbutton(
            main,
            text="Pular pré-processamento (usar o PDF como está)",
            variable=self.var_pular_proc,
        ).pack(anchor="w")

        # Prompt editável
        grp_prompt = ttk.LabelFrame(
            main,
            text="Instruções específicas deste caso (editáveis)",
            padding=8,
        )
        grp_prompt.pack(fill="both", expand=True, pady=(8, 8))

        self.txt_prompt = scrolledtext.ScrolledText(
            grp_prompt, wrap="word", height=10,
            font=("TkDefaultFont", 10),
        )
        self.txt_prompt.pack(fill="both", expand=True)
        self.txt_prompt.insert("1.0", USER_PROMPT_PADRAO)

        # Botão Gerar + status
        barra = ttk.Frame(main)
        barra.pack(fill="x", pady=(4, 0))

        self.btn_gerar = ttk.Button(
            barra, text="▶ Gerar sentença", command=self._iniciar_geracao,
        )
        self.btn_gerar.pack(side="left")

        ttk.Label(barra, textvariable=self.var_status).pack(
            side="left", padx=12,
        )

        self.pb = ttk.Progressbar(barra, mode="indeterminate", length=200)
        self.pb.pack(side="right")

        # Log
        grp_log = ttk.LabelFrame(main, text="Log", padding=4)
        grp_log.pack(fill="both", expand=True, pady=(8, 0))

        self.txt_log = scrolledtext.ScrolledText(
            grp_log, wrap="word", height=8, state=DISABLED,
            font=("TkFixedFont", 9),
        )
        self.txt_log.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Ações da UI
    # ------------------------------------------------------------------

    def _escolher_pdf(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Escolha o PDF dos autos",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")],
        )
        if caminho:
            self.var_pdf.set(caminho)

    def _log(self, msg: str) -> None:
        def _escrever():
            self.txt_log.configure(state=NORMAL)
            self.txt_log.insert(END, msg + "\n")
            self.txt_log.see(END)
            self.txt_log.configure(state=DISABLED)
        self.root.after(0, _escrever)

    def _set_status(self, msg: str) -> None:
        self.root.after(0, lambda: self.var_status.set(msg))

    def _iniciar_geracao(self) -> None:
        pdf = self.var_pdf.get().strip()
        api_key = self.var_api_key.get().strip()

        if not pdf or not Path(pdf).exists():
            messagebox.showerror("Erro", "Escolha um PDF válido.")
            return
        if not api_key:
            messagebox.showerror(
                "Erro", "Informe a API Key da Anthropic.",
            )
            return

        # Persiste configs não-sensíveis + chave
        self.cfg.update({
            "api_key": api_key,
            "modelo": self.var_modelo.get(),
            "cidade": self.var_cidade.get(),
        })
        salvar_config(self.cfg)

        self.btn_gerar.configure(state=DISABLED)
        self.pb.start(12)

        t = threading.Thread(target=self._executar, daemon=True)
        t.start()

    # ------------------------------------------------------------------
    # Pipeline (roda em thread, fora do main loop do Tk)
    # ------------------------------------------------------------------

    def _executar(self) -> None:
        try:
            self._pipeline()
        except Exception as e:
            self._log("ERRO: " + str(e))
            self._log(traceback.format_exc())
            self.root.after(
                0,
                lambda: messagebox.showerror("Erro", str(e)),
            )
        finally:
            self.root.after(0, self._pb_parar)
            self.root.after(
                0, lambda: self.btn_gerar.configure(state=NORMAL),
            )
            self._set_status("Pronto.")

    def _pb_parar(self) -> None:
        self.pb.stop()

    def _pipeline(self) -> None:
        pdf_in = Path(self.var_pdf.get())
        base = pdf_in.with_suffix("")
        pdf_processado = base.parent / (pdf_in.stem + "_limpo.pdf")
        sentenca_py = base.parent / (pdf_in.stem + "_sentenca.py")
        sentenca_docx = base.parent / (pdf_in.stem + "_sentenca.docx")

        # 1. Processar PDF
        if self.var_pular_proc.get():
            pdf_para_api = pdf_in
            self._log(f"Pulando pré-processamento. Usando: {pdf_in.name}")
        else:
            self._set_status("Processando PDF...")
            self._log(f"→ Pré-processando: {pdf_in.name}")
            metricas = processar_pdf(
                pdf_in, pdf_processado, progress=self._log,
            )
            pdf_para_api = pdf_processado
            self._log(
                f"✓ PDF limpo: {metricas['tamanho_in_mb']:.1f} MB → "
                f"{metricas['tamanho_out_mb']:.1f} MB "
                f"(redução {metricas['reducao_pct']:.0f}%, "
                f"{metricas['paginas_ocr']} páginas com OCR)"
            )

        # 2. Chamar API
        self._set_status("Chamando API (pode demorar 1-3 min)...")
        self._log("→ Enviando para a API Anthropic...")

        user_prompt = self.txt_prompt.get("1.0", END).strip()
        resultado = gerar_sentenca(
            pdf_para_api,
            user_prompt,
            api_key=self.var_api_key.get().strip(),
            modelo=self.var_modelo.get(),
            progress=self._log,
        )

        self._log(
            f"✓ Resposta recebida: "
            f"{resultado['tokens_input']} tokens in / "
            f"{resultado['tokens_output']} tokens out"
        )
        det = resultado["custo_detalhado"]
        self._log(
            f"  Custo estimado: US$ {resultado['custo_usd']:.3f} "
            f"(input {det['input']:.3f} + output {det['output']:.3f} + "
            f"buscas {det['buscas']:.3f})"
        )
        if resultado["searches"]:
            self._log(f"  {len(resultado['searches'])} consulta(s) web_search:")
            for q in resultado["searches"]:
                self._log(f"    · {q}")
        else:
            self._log("  (Nenhuma consulta web_search foi feita.)")

        # 3. Salvar sentenca.py
        sentenca_py.write_text(resultado["codigo"], encoding="utf-8")
        self._log(f"✓ Código salvo: {sentenca_py.name}")

        # 4. Gerar .docx
        self._set_status("Gerando .docx...")
        dados = carregar_sentenca(sentenca_py)
        gerar(dados, sentenca_docx, cidade=self.var_cidade.get())
        self._log(f"✓ Sentença gerada: {sentenca_docx}")

        # 5. Avisar
        self.root.after(
            0,
            lambda: messagebox.showinfo(
                "Pronto",
                f"Sentença gerada em:\n\n{sentenca_docx}",
            ),
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    root = Tk()
    Sentenciador(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
