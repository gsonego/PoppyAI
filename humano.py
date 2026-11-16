"""Partida controlada pelo jogador e recorde pessoal separado da IA."""

import json
import math
from pathlib import Path

from campeao import VERSAO_EXPERIMENTO
from config import ARQUIVO_RECORDE_HUMANO, SEMENTE_TREINO


class JogoHumano:
    def __init__(self, caminho=ARQUIVO_RECORDE_HUMANO):
        self.caminho = Path(caminho)
        self.concluida = False
        self.melhor_tempo = 0.0
        if self.caminho.exists():
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            if not isinstance(dados, dict) or dados.get("experimento") != self._experimento():
                raise ValueError("O recorde pessoal pertence a outro experimento.")
            tempo = dados.get("tempo_segundos")
            if type(tempo) not in (int, float) or not math.isfinite(tempo) or tempo < 0:
                raise ValueError("O recorde pessoal contém um tempo inválido.")
            self.melhor_tempo = tempo

    @staticmethod
    def _experimento():
        return {"versao": VERSAO_EXPERIMENTO, "semente": SEMENTE_TREINO}

    def terminou(self, ambiente):
        return ambiente.fim_de_jogo

    def salvar_recorde(self, ambiente):
        if ambiente.tempo_vivo <= self.melhor_tempo:
            return
        dados = {"experimento": self._experimento(), "tempo_segundos": ambiente.tempo_vivo}
        temporario = self.caminho.with_suffix(self.caminho.suffix + ".tmp")
        temporario.write_text(json.dumps(dados, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporario.replace(self.caminho)
        self.melhor_tempo = ambiente.tempo_vivo

    def concluir_tentativa(self, ambiente):
        self.salvar_recorde(ambiente)
        self.concluida = True
