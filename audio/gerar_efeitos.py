"""Gera os efeitos originais em WAV PCM, sem bibliotecas ou arquivos externos.

Execute com: python audio/gerar_efeitos.py
"""

from array import array
from math import sin, tau
from pathlib import Path
import random
import sys
import wave

TAXA = 44100


def sintetizar(notas, ruido=False):
    amostras = array("h")
    sorteio = random.Random(42)
    fase = 0.0
    for inicio, fim, duracao in notas:
        quantidade = round(TAXA * duracao)
        for indice in range(quantidade):
            progresso = indice / max(1, quantidade - 1)
            frequencia = inicio + (fim - inicio) * progresso
            fase = (fase + frequencia / TAXA) % 1
            # Onda quadrada com harmônico suave e ataque/saída para evitar estalos.
            onda = (1.0 if fase < 0.5 else -1.0) * 0.8 + sin(tau * fase) * 0.2
            if ruido:
                onda = onda * 0.45 + sorteio.uniform(-1, 1) * 0.55
            envelope = min(1.0, indice / (TAXA * 0.004),
                           (quantidade - 1 - indice) / (TAXA * 0.018))
            amostras.append(round(onda * envelope * 0.24 * 32767))
    if sys.byteorder != "little":
        amostras.byteswap()
    return amostras.tobytes()


def gerar(pasta=Path(__file__).resolve().parent):
    pasta.mkdir(parents=True, exist_ok=True)
    efeitos = {
        "salto": ([(260, 880, 0.13)], False),
        "colisao": ([(180, 45, 0.20)], True),
        "menu_mover": ([(650, 750, 0.045)], False),
        "menu_confirmar": ([(660, 660, 0.055), (990, 990, 0.09)], False),
        "recorde": ([(523, 523, 0.09), (659, 659, 0.09),
                     (784, 784, 0.09), (1047, 1047, 0.20)], False),
    }
    for nome, (notas, ruido) in efeitos.items():
        with wave.open(str(pasta / f"{nome}.wav"), "wb") as arquivo:
            arquivo.setnchannels(1)
            arquivo.setsampwidth(2)
            arquivo.setframerate(TAXA)
            arquivo.writeframes(sintetizar(notas, ruido))


if __name__ == "__main__":
    gerar()
