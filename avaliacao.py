"""Avaliação da campeã com parâmetros fixos, sem modificar o arquivo salvo."""

from campeao import carregar_campeao
from config import ARQUIVO_CAMPEAO, LIMITE_TENTATIVA, SEMENTE_TREINO


class Avaliacao:
    def __init__(self, caminho=ARQUIVO_CAMPEAO, semente=SEMENTE_TREINO):
        try:
            campeao = carregar_campeao(caminho, LIMITE_TENTATIVA, SEMENTE_TREINO)
        except (OSError, ValueError) as erro:
            raise SystemExit(f"Não foi possível carregar {caminho}: {erro}")
        if campeao is None:
            raise SystemExit("Nenhuma campeã salva. Execute o modo treino primeiro.")
        self.parametros, self.recorde_treino = campeao
        self.semente = semente
        self.concluida = False
        print(
            f"Avaliação: semente={self.semente} | parâmetros fixos | "
            f"recorde de treino={self.recorde_treino:.2f}s"
        )

    def terminou(self, ambiente):
        return ambiente.fim_de_jogo or ambiente.tempo_vivo >= LIMITE_TENTATIVA

    def concluir_tentativa(self, ambiente):
        self.concluida = True
        tempo = min(ambiente.tempo_vivo, LIMITE_TENTATIVA)
        motivo = "colisão" if ambiente.fim_de_jogo else "limite atingido"
        print(
            f"Avaliação: semente={self.semente} | {tempo:.2f}s "
            f"({motivo}). R para repetir."
        )
