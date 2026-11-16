"""População visível de Poppys: mesma partida, políticas independentes e seleção por geração."""

from colorsys import hsv_to_rgb
from dataclasses import dataclass

from ambiente import Ambiente
from config import SEMENTE_TREINO
from politica import decidir_salto
from treino import Treino


@dataclass
class Individuo:
    numero: int
    parametros: tuple
    cor: tuple
    ambiente: Ambiente


class TreinoGeracoes(Treino):
    def __init__(self, *args, tamanho=50, **kwargs):
        if tamanho < 2:
            raise ValueError("A população precisa de pelo menos duas Poppys.")
        super().__init__(*args, **kwargs)
        self.tamanho = tamanho
        self.geracao = 1
        parametros = [self.parametros] + [self._proxima_candidata() for _ in range(tamanho - 1)]
        self._criar_individuos(parametros)

    def _criar_individuos(self, parametros):
        self.individuos = []
        for indice, pesos in enumerate(parametros):
            cor = tuple(round(c * 255) for c in hsv_to_rgb(indice / self.tamanho, 0.85, 0.72))
            self.individuos.append(Individuo(indice + 1, tuple(pesos), cor, Ambiente(SEMENTE_TREINO)))

    @property
    def vivos(self):
        return [poppy for poppy in self.individuos if not poppy.ambiente.fim_de_jogo]

    @property
    def lider(self):
        return max(self.individuos, key=lambda p: (p.ambiente.tempo_vivo, not p.ambiente.fim_de_jogo))

    def salvar_melhor(self, forcar=False):
        lider = self.lider
        self.parametros = lider.parametros
        return self.registrar_progresso(lider.ambiente, forcar=forcar)

    def avancar(self):
        if not self.vivos:
            self.proxima_geracao()
        for poppy in self.vivos:
            ambiente = poppy.ambiente
            pedido = decidir_salto(ambiente.distancia, ambiente.obstaculo.height,
                                   ambiente.obstaculo.width, ambiente.velocidade, poppy.parametros)
            ambiente.avancar(pedido)
        self.salvar_melhor(forcar=not self.vivos)

    def proxima_geracao(self):
        self.salvar_melhor(forcar=True)
        classificadas = sorted(self.individuos,
                               key=lambda p: (p.ambiente.tempo_vivo, not p.ambiente.fim_de_jogo), reverse=True)
        quantidade_elites = max(1, self.tamanho // 10)
        pais = [p.parametros for p in classificadas[:quantidade_elites]]
        # Preserva a campeã histórica, mesmo ao encerrar uma geração cedo com N.
        parametros = [self.melhores_parametros or pais[0]] + pais[1:]
        while len(parametros) < self.tamanho:
            if self.sorteio.random() < 0.20:
                parametros.append(self._sortear_parametros())
            else:
                mae = self.sorteio.choice(pais)
                parametros.append(tuple(peso + self.sorteio.gauss(0, desvio)
                                        for peso, desvio in zip(mae, (0.20, 0.20, 0.20, 0.20, 0.10))))
        self.geracao += 1
        self._criar_individuos(parametros)
        print(f"Geração {self.geracao}: {self.tamanho} Poppys | recorde={self.melhor_tempo:.2f}s")
