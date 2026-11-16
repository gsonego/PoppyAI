"""Cenário estático em pixel art, sem dependência da simulação."""

import pygame

CEU = "#B7E5F0"

TINTA = "#493B45"

CREME = "#FFF3D9"

ROSA = "#DC7189"

VERDE = "#64A54C"

TERRA = "#C38B59"

def nuvem(tela, x, y, tamanho=1):
    for dx, dy, largura, altura in ((8, 0, 22, 8), (0, 8, 46, 12), (6, 20, 34, 4)):
        pygame.draw.rect(tela, CREME, (x + dx * tamanho, y + dy * tamanho, largura * tamanho, altura * tamanho))

def terreno(tela):
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
    pygame.draw.rect(tela, TERRA, (0, 330, 900, 70))
    pygame.draw.rect(tela, VERDE, (0, 330, 900, 8))
    pygame.draw.rect(tela, "#407849", (0, 338, 900, 4))
    for x in range(0, 900, 16):
        pygame.draw.rect(tela, VERDE, (x, 338, 8, 4))
    for x in range(10, 900, 36):
        pygame.draw.rect(tela, "#A96F49", (x, 353, 8, 4))
        pygame.draw.rect(tela, "#DCA56F", (x + 16, 345, 6, 4))
    for x, y in ((376, 316), (740, 316), (794, 308)):
        pygame.draw.rect(tela, "#407849", (x + 4, y + 6, 2, 8))
        pygame.draw.rect(tela, ROSA, (x, y + 2, 10, 6))
        pygame.draw.rect(tela, ROSA, (x + 2, y, 6, 10))
        pygame.draw.rect(tela, CREME, (x + 4, y + 4, 2, 2))
