"""Paisagem em pixel art e chão repetível, sem dependência da simulação."""

import pygame

from config import ALTURA, CHAO_Y, LARGURA

CEU = "#B7E5F0"

TINTA = "#493B45"

CREME = "#FFF3D9"

ROSA = "#DC7189"

VERDE = "#64A54C"

TERRA = "#C38B59"

def nuvem(tela, x, y, tamanho=1):
    for dx, dy, largura, altura in ((8, 0, 22, 8), (0, 8, 46, 12), (6, 20, 34, 4)):
        pygame.draw.rect(tela, CREME, (x + dx * tamanho, y + dy * tamanho, largura * tamanho, altura * tamanho))

def terreno(tela, incluir_chao=True):
    tela.fill(CEU)
    nuvem(tela, 250, 106, 2)
    nuvem(tela, 630, 150, 1)
    nuvem(tela, 810, 100, 2)
    # Colinas em degraus, com poucos tons: o cenário deixa a Poppy em destaque.
    pygame.draw.polygon(tela, "#92C8A0", [(0, 285), (0, 263), (56, 263), (56, 245), (114, 245),
        (114, 228), (188, 228), (188, 245), (248, 245), (248, 266), (310, 266), (310, 285),
        (394, 285), (394, 267), (450, 267), (450, 244), (510, 244), (510, 226), (580, 226),
        (580, 244), (644, 244), (644, 266), (706, 266), (706, 282), (900, 282), (900, 330), (0, 330)])
    pygame.draw.polygon(tela, "#7CB66E", [(0, 309), (60, 309), (60, 295), (136, 295),
        (136, 281), (208, 281), (208, 295), (296, 295), (296, 309), (390, 309),
        (390, 299), (482, 299), (482, 309), (650, 309), (650, 289), (730, 289),
        (730, 272), (810, 272), (810, 289), (900, 289), (900, 330), (0, 330)])
    if incluir_chao:
        desenhar_chao(tela, criar_faixa_chao(), 0)


def criar_faixa_chao():
    # 144 é múltiplo dos padrões de 16 e 36 px: a emenda não dá um salto.
    faixa = pygame.Surface((144, ALTURA - CHAO_Y))
    faixa.fill(TERRA)
    pygame.draw.rect(faixa, VERDE, (0, 0, 144, 8))
    pygame.draw.rect(faixa, "#407849", (0, 8, 144, 4))
    for x in range(0, 144, 16):
        pygame.draw.rect(faixa, VERDE, (x, 8, 8, 4))
    for x in range(10, 144, 36):
        pygame.draw.rect(faixa, "#A96F49", (x, 23, 8, 4))
        pygame.draw.rect(faixa, "#DCA56F", (x + 16, 15, 6, 4))
    return faixa


def desenhar_chao(tela, faixa, distancia):
    deslocamento = round(distancia)
    for x in range(-(deslocamento % faixa.get_width()), LARGURA, faixa.get_width()):
        tela.blit(faixa, (x, CHAO_Y))
    # As flores estão enraizadas no chão e acompanham sua mesma velocidade.
    for origem, y in ((376, 316), (740, 316), (794, 308)):
        x = (origem - deslocamento) % LARGURA
        _flor(tela, x, y)
        if x + 10 > LARGURA:
            _flor(tela, x - LARGURA, y)


def _flor(tela, x, y):
    pygame.draw.rect(tela, "#407849", (x + 4, y + 6, 2, 8))
    pygame.draw.rect(tela, ROSA, (x, y + 2, 10, 6))
    pygame.draw.rect(tela, ROSA, (x + 2, y, 6, 10))
    pygame.draw.rect(tela, CREME, (x + 4, y + 4, 2, 2))
