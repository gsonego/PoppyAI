"""A política transforma uma observação em um pedido de salto."""

from config import LARGURA


def decidir_salto(distancia, parametros):
    peso, vies = parametros
    entrada = distancia / LARGURA
    z = peso * entrada + vies
    return z > 0
