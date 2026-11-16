"""A política transforma uma observação em um pedido de salto."""

import math

from config import ALTURA, LARGURA


def limiar_salto(altura, parametros):
    """Distância em que z = 0, considerando a altura do obstáculo atual."""
    peso_distancia, peso_altura, vies = parametros
    if peso_distancia == 0:
        return None
    termo_altura = peso_altura * (altura / ALTURA)
    limiar = -((termo_altura + vies) / peso_distancia) * LARGURA
    return limiar if math.isfinite(limiar) else None


def decidir_salto(distancia, altura, parametros):
    peso_distancia, peso_altura, vies = parametros
    entrada_distancia = distancia / LARGURA
    entrada_altura = altura / ALTURA
    z = peso_distancia * entrada_distancia + peso_altura * entrada_altura + vies
    return z > 0
