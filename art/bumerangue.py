"""Bumerangue em pixel art, desenhado por código e guardado em 16 poses."""

import pygame

from config import BUMERANGUE_TAMANHO

DISTANCIA_POR_QUADRO = 12.0
QUANTIDADE_QUADROS = 16


def quadro_bumerangue(distancia):
    return int(max(0.0, distancia) / DISTANCIA_POR_QUADRO) % QUANTIDADE_QUADROS


def criar_quadros():
    base = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.polygon(base, "#493B45", ((3, 3), (6, 3), (13, 8), (6, 13), (3, 13), (8, 8)))
    pygame.draw.polygon(base, "#E69035", ((4, 4), (6, 4), (11, 8), (6, 12), (4, 12), (9, 8)))
    pygame.draw.lines(base, "#FFE19A", False, ((5, 4), (10, 8), (5, 12)), 1)
    pygame.draw.rect(base, "#DC7189", (4, 4, 2, 1))
    pygame.draw.rect(base, "#DC7189", (4, 12, 2, 1))
    quadros = []
    for indice in range(QUANTIDADE_QUADROS):
        rotacao = pygame.transform.rotate(base, -indice * 360 / QUANTIDADE_QUADROS)
        quadro = pygame.Surface((16, 16), pygame.SRCALPHA)
        quadro.blit(rotacao, rotacao.get_rect(center=(8, 8)))
        quadros.append(pygame.transform.scale(quadro, (BUMERANGUE_TAMANHO, BUMERANGUE_TAMANHO)))
    return tuple(quadros)


def salvar_folha(caminho):
    """Exporta a mesma arte do jogo para uma folha revisável no repositório."""
    folha = pygame.Surface((BUMERANGUE_TAMANHO * 4, BUMERANGUE_TAMANHO * 4), pygame.SRCALPHA)
    for indice, quadro in enumerate(criar_quadros()):
        folha.blit(quadro, ((indice % 4) * BUMERANGUE_TAMANHO, (indice // 4) * BUMERANGUE_TAMANHO))
    pygame.image.save(folha, str(caminho))
