"""Avaliação da campeã com parâmetros fixos, sem modificar o arquivo salvo."""

from secrets import randbelow

from campeao import carregar_campeao
from config import ARQUIVO_CAMPEAO, LIMITE_TENTATIVA, SEMENTE_TREINO


class Avaliacao:
    def __init__(self, caminho=ARQUIVO_CAMPEAO, semente=None):
        try:
            campeao = carregar_campeao(caminho, LIMITE_TENTATIVA, SEMENTE_TREINO)
        except (OSError, ValueError) as erro:
            raise SystemExit(f"Não foi possível carregar {caminho}: {erro}")
        if campeao is None:
            raise SystemExit("Nenhuma campeã salva. Execute o modo treino primeiro.")
        self.parametros, self.recorde_treino = campeao
        self.semente = semente
        if semente is None:
            self.sortear_semente()
        self.concluida = False
        print(
            f"Avaliação: semente={self.semente} | parâmetros fixos | "
            f"recorde de treino={self.recorde_treino:.2f}s"
        )

    def sortear_semente(self):
        anterior = self.semente
        while True:
            semente = randbelow(2**31)
            if semente not in (SEMENTE_TREINO, anterior):
                self.semente = semente
                self.concluida = False
                print(f"Nova sequência de avaliação: semente={semente}")
                return semente

    def terminou(self, ambiente):
        return ambiente.fim_de_jogo

    def concluir_tentativa(self, ambiente):
        self.concluida = True
        tempo = ambiente.tempo_vivo
        print(
            f"Avaliação: semente={self.semente} | {tempo:.2f}s "
            f"(colisão). R para repetir."
        )
