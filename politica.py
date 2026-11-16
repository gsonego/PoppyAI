"""A política transforma uma observação em um pedido de salto."""

import math

from config import ALTURA, LARGURA, VELOCIDADE_MAXIMA


def limiar_salto(altura, largura, velocidade, parametros):
    """Distância em que z = 0, considerando dimensões e velocidade atuais."""
    peso_distancia, peso_altura, peso_largura, peso_velocidade, vies = parametros
    if peso_distancia == 0:
        return None
    termo_altura = peso_altura * (altura / ALTURA)
    termo_largura = peso_largura * (largura / LARGURA)
    termo_velocidade = peso_velocidade * (velocidade / VELOCIDADE_MAXIMA)
    limiar = -((termo_altura + termo_largura + termo_velocidade + vies) / peso_distancia) * LARGURA
    return limiar if math.isfinite(limiar) else None


def decidir_salto(distancia, altura, largura, velocidade, parametros):
    peso_distancia, peso_altura, peso_largura, peso_velocidade, vies = parametros
    entrada_distancia = distancia / LARGURA
    entrada_altura = altura / ALTURA
    entrada_largura = largura / LARGURA
    entrada_velocidade = velocidade / VELOCIDADE_MAXIMA
    z = (peso_distancia * entrada_distancia + peso_altura * entrada_altura
         + peso_largura * entrada_largura + peso_velocidade * entrada_velocidade + vies)
    return z > 0
