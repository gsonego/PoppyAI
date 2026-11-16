"""A política transforma uma observação em um pedido de salto."""

import math

from config import LARGURA


def limiar_salto(parametros):
    """Distância em que z = 0; peso zero não tem um limiar de distância."""
    peso, vies = parametros
    if peso == 0:
        return None
    limiar = -(vies / peso) * LARGURA
    return limiar if math.isfinite(limiar) else None


def decidir_salto(distancia, parametros):
    peso, vies = parametros
    entrada = distancia / LARGURA
    z = peso * entrada + vies
    return z > 0
