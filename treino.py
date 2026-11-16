"""Busca evolutiva: os parâmetros mudam somente entre partidas."""

import random

from campeao import carregar_campeao, salvar_campeao
from config import (
    ARQUIVO_CAMPEAO, LIMITE_TENTATIVA, SEMENTE_PARAMETROS, SEMENTE_TREINO,
)


class Treino:
    def __init__(self, caminho=ARQUIVO_CAMPEAO):
        self.caminho = caminho
        self.sorteio = random.Random(SEMENTE_PARAMETROS)
        self.parametros = self._sortear_parametros()
        self.melhores_parametros = None
        self.melhor_tempo = -1.0
        self.tentativa = 1
        try:
            campeao = carregar_campeao(caminho, LIMITE_TENTATIVA, SEMENTE_TREINO)
        except (OSError, ValueError) as erro:
            raise SystemExit(f"Não foi possível carregar {caminho}: {erro}")
        if campeao is not None:
            self.melhores_parametros, self.melhor_tempo = campeao
            self.parametros = self.melhores_parametros
            print(f"Campeã carregada: recorde de treino={self.melhor_tempo:.2f}s")
        else:
            print("Nenhuma campeã salva. Iniciando uma nova busca.")
        self._anunciar_tentativa()

    def _anunciar_tentativa(self):
        peso_distancia, peso_altura, vies = self.parametros
        print(
            f"Tentativa {self.tentativa}: peso_distancia={peso_distancia:.3f}, "
            f"peso_altura={peso_altura:.3f}, vies={vies:.3f}"
        )

    def _sortear_parametros(self):
        return (
            self.sorteio.uniform(-2.0, 2.0),
            self.sorteio.uniform(-2.0, 2.0),
            self.sorteio.uniform(-1.0, 1.0),
        )

    def _proxima_candidata(self):
        if self.melhores_parametros is None or self.sorteio.random() < 0.20:
            return self._sortear_parametros()
        peso_distancia, peso_altura, vies = self.melhores_parametros
        return (
            peso_distancia + self.sorteio.gauss(0.0, 0.20),
            peso_altura + self.sorteio.gauss(0.0, 0.20),
            vies + self.sorteio.gauss(0.0, 0.10),
        )

    def terminou(self, ambiente):
        return ambiente.fim_de_jogo

    def registrar_progresso(self, ambiente, forcar=False):
        """Salva novos recordes sem encerrar a tentativa ou mudar os parâmetros."""
        pontuacao = ambiente.tempo_vivo
        if ambiente.tentativa_manual or pontuacao <= self.melhor_tempo:
            return False
        # Durante a partida, evita escrever no disco a cada quadro.
        if not forcar and pontuacao < max(0.0, self.melhor_tempo) + 1.0:
            return False
        try:
            salvar_campeao(
                self.caminho, self.parametros, pontuacao,
                LIMITE_TENTATIVA, SEMENTE_TREINO,
            )
        except (OSError, ValueError) as erro:
            raise SystemExit(f"Não foi possível salvar a campeã: {erro}")
        self.melhor_tempo = pontuacao
        self.melhores_parametros = self.parametros
        return True

    def concluir_tentativa(self, ambiente):
        pontuacao = ambiente.tempo_vivo
        melhorou = self.registrar_progresso(ambiente, forcar=True)

        print(
            f"Tentativa {self.tentativa}: {pontuacao:.2f}s "
            f"(colisão) | recorde={self.melhor_tempo:.2f}s"
            + (" | NOVO RECORDE" if melhorou else "")
            + (" | intervenção manual: fora do recorde" if ambiente.tentativa_manual else "")
        )
        self.parametros = self._proxima_candidata()
        self.tentativa += 1
        self._anunciar_tentativa()
