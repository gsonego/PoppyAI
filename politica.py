"""A política transforma uma observação em um pedido de salto."""

import math

from config import ALTURA, LARGURA


def limiar_salto(altura, largura, parametros):
    """Distância em que z = 0, para a altura e a largura totais do conjunto."""
    peso_distancia, peso_altura, peso_largura, vies = parametros
    if peso_distancia == 0:
        return None
    termo_altura = peso_altura * (altura / ALTURA)
    termo_largura = peso_largura * (largura / LARGURA)
    limiar = -((termo_altura + termo_largura + vies) / peso_distancia) * LARGURA
    return limiar if math.isfinite(limiar) else None


def decidir_salto(distancia, altura, largura, parametros):
    peso_distancia, peso_altura, peso_largura, vies = parametros
    entrada_distancia = distancia / LARGURA
    entrada_altura = altura / ALTURA
    entrada_largura = largura / LARGURA
    z = (peso_distancia * entrada_distancia + peso_altura * entrada_altura
         + peso_largura * entrada_largura + vies)
    return z > 0
