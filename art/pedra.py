"""Pedra pequena em pixel art, transposta pela corrida normal em pé."""

import pygame

from config import PEDRA_ALTURA, PEDRA_LARGURA


def criar_sprite():
    imagem = pygame.Surface((16, 5), pygame.SRCALPHA)
    pygame.draw.polygon(imagem, "#493B45", ((0, 4), (2, 2), (5, 0), (10, 0), (14, 2), (15, 4)))
    pygame.draw.polygon(imagem, "#81858B", ((2, 3), (5, 1), (10, 1), (13, 3), (13, 4), (2, 4)))
    pygame.draw.line(imagem, "#B5BAC1", (5, 1), (9, 1))
    pygame.draw.line(imagem, "#5B6069", (10, 2), (12, 4))
    return pygame.transform.scale(imagem, (PEDRA_LARGURA, PEDRA_ALTURA))


def salvar_sprite(caminho):
    pygame.image.save(criar_sprite(), str(caminho))
