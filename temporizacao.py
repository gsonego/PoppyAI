"""Ritmo de apresentação medido e física acumulada em passos fixos de 1/60 s."""

from collections import deque
from time import perf_counter, sleep

from config import PASSO


class RelogioQuadros:
    def __init__(self, fps=60):
        self.periodo = 1.0 / max(1, fps)
        self.amostras = deque(maxlen=240)
        self.reiniciar()

    def reiniciar(self):
        self.anterior = perf_counter()
        self.proximo = self.anterior + self.periodo
        self.amostras.clear()

    def tick(self):
        restante = self.proximo - perf_counter()
        if restante > 0:
            sleep(restante)
        agora = perf_counter()
        decorrido = agora - self.anterior
        self.anterior = agora
        self.proximo += self.periodo
        if self.proximo < agora:
            self.proximo = agora + self.periodo
        self.amostras.append(decorrido)
        return decorrido

    def resumo(self):
        valores = sorted(self.amostras)
        if not valores:
            return 0.0, 0.0, 0.0
        media = sum(valores) / len(valores)
        return 1 / media if media > 0 else 0.0, media * 1000, valores[min(len(valores) - 1, int(len(valores) * 0.95))] * 1000


class AvancoFixo:
    def __init__(self):
        self.acumulado = 0.0

    @property
    def fracao(self):
        return min(1.0, max(0.0, self.acumulado / PASSO))

    def acumular(self, segundos):
        # Evita dezenas de segundos de atualizações ao voltar de uma pausa do SO.
        self.acumulado += max(0.0, min(0.25, segundos))
        passos = int((self.acumulado + 1e-12) / PASSO)
        self.acumulado = max(0.0, self.acumulado - passos * PASSO)
        return passos
