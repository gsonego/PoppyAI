"""Rede 5 → 4 → 2, evoluída por mutações, sem bibliotecas de machine learning."""

from math import tanh

from config import ALTURA, LARGURA, VELOCIDADE_MAXIMA

ENTRADAS = 5
OCULTOS = 4
SAIDAS = 2
QUANTIDADE_PARAMETROS = OCULTOS * (ENTRADAS + 1) + SAIDAS * (OCULTOS + 1)
MODELO = {"entradas": ENTRADAS, "ocultos": OCULTOS, "saidas": SAIDAS,
          "ativacao_oculta": "tanh", "ativacao_saida": "degrau"}
DESVIOS_MUTACAO = ((0.20,) * ENTRADAS + (0.10,)) * OCULTOS + ((0.20,) * OCULTOS + (0.10,)) * SAIDAS


def observar(ambiente):
    return (ambiente.distancia / LARGURA, ambiente.obstaculo.height / ALTURA,
            ambiente.obstaculo.width / LARGURA, ambiente.velocidade / VELOCIDADE_MAXIMA,
            ambiente.elevacao_obstaculo / ALTURA)


def calcular_saidas(entradas, parametros):
    if len(entradas) != ENTRADAS or len(parametros) != QUANTIDADE_PARAMETROS:
        raise ValueError("A política exige cinco entradas e 34 parâmetros.")
    ocultos = []
    for indice in range(OCULTOS):
        inicio = indice * (ENTRADAS + 1)
        pesos = parametros[inicio:inicio + ENTRADAS]
        ocultos.append(tanh(sum(peso * entrada for peso, entrada in zip(pesos, entradas))
                            + parametros[inicio + ENTRADAS]))
    saidas = []
    for indice in range(SAIDAS):
        inicio = OCULTOS * (ENTRADAS + 1) + indice * (OCULTOS + 1)
        pesos = parametros[inicio:inicio + OCULTOS]
        saidas.append(sum(peso * entrada for peso, entrada in zip(pesos, ocultos))
                      + parametros[inicio + OCULTOS])
    return tuple(saidas)


def decidir_acoes(ambiente, parametros):
    salto, abaixar = calcular_saidas(observar(ambiente), parametros)
    # Abaixar tem prioridade se as duas saídas dispararem.
    abaixar = abaixar > 0
    return salto > 0 and not abaixar, abaixar


def aplicar_politica(ambiente, parametros):
    salto, abaixar = decidir_acoes(ambiente, parametros)
    ambiente.definir_abaixada(abaixar)
    ambiente.avancar(salto)
    return salto, abaixar
