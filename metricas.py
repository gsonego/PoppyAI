"""Diário de treino em segundo plano: preserva todos os eventos, sem bloquear quadros."""

from copy import deepcopy
import json
import os
from pathlib import Path
from queue import Queue
import subprocess
import sys
from threading import Thread

from diagnostico import registro


class GravadorMetricas:
    def __init__(self, caminho, campeao):
        self.caminho = Path(caminho)
        self.campeao = Path(campeao)
        self.fila = Queue()
        self.erro = None
        self._fechado = False
        self._processo = None
        self._thread = Thread(target=self._gravar, name="metricas-treino", daemon=True)
        self._thread.start()

    def agendar(self, evento):
        if self._fechado:
            raise RuntimeError("O registro do treino já foi fechado.")
        if self.erro is None:
            self.fila.put(("evento", deepcopy(evento)))

    def solicitar_graficos(self):
        if not self._fechado and self.erro is None:
            self.fila.put(("graficos", None))

    def _abrir_graficos(self):
        if self._processo is not None and self._processo.poll() is None:
            return
        pasta = self.caminho.with_suffix("")
        pasta.mkdir(parents=True, exist_ok=True)
        comando = [sys.executable, str(Path(__file__).with_name("relatorio_treino.py")),
                   "--arquivo", str(self.caminho), "--campeao", str(self.campeao),
                   "--saida", str(pasta), "--abrir"]
        with (pasta / "plotagem.log").open("a", encoding="utf-8") as log:
            self._processo = subprocess.Popen(comando, stdout=log, stderr=log,
                                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def _gravar(self):
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            with self.caminho.open("a", encoding="utf-8") as arquivo:
                while True:
                    tipo, dado = self.fila.get()
                    if tipo == "fechar":
                        return
                    if tipo == "evento":
                        arquivo.write(json.dumps(dado, ensure_ascii=False, allow_nan=False) + "\n")
                        arquivo.flush()
                    elif tipo == "graficos":
                        arquivo.flush()
                        try:
                            self._abrir_graficos()
                        except (OSError, ValueError):
                            registro.exception("Falha ao iniciar os graficos do treino")
        except Exception as erro:
            self.erro = erro
            registro.exception("Registro de metricas indisponivel; jogo continua sem coletar")

    def fechar(self):
        if not self._fechado:
            self._fechado = True
            self.fila.put(("fechar", None))
            self._thread.join()
