"""Quatro poses de corrida, alinhadas pela cabeça e guiadas pelo deslocamento."""

import pygame

DISTANCIA_POR_QUADRO = 32.0


def quadro_corrida(distancia_percorrida):
    return int(max(0.0, distancia_percorrida) / DISTANCIA_POR_QUADRO) % 4


def carregar_corrida(caminho):
    folha = pygame.image.load(caminho).convert_alpha()
    largura, altura = folha.get_size()
    recortes = []
    for indice in range(4):
        coluna, linha = indice % 2, indice // 2
        esquerda, direita = coluna * largura // 2, (coluna + 1) * largura // 2
        topo, fundo = linha * altura // 2, (linha + 1) * altura // 2
        celula = folha.subsurface((esquerda, topo, direita - esquerda, fundo - topo))
        recortes.append(celula.subsurface(celula.get_bounding_rect(min_alpha=128)))

    # A folha tem margens diferentes entre células. Remove-as e fixa o topo
    # das orelhas na mesma origem, sem esticar cada pose para uma altura diferente.
    tamanho = (max(r.get_width() for r in recortes), max(r.get_height() for r in recortes))
    quadros = []
    for recorte in recortes:
        quadro = pygame.Surface(tamanho, pygame.SRCALPHA)
        quadro.blit(recorte, (0, 0))
        quadros.append(quadro)
    return tuple(quadros)
