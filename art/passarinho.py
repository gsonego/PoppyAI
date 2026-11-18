"""Passarinho azul em quatro poses de asas, desenhado por código em pixel art."""

import pygame

DISTANCIA_POR_QUADRO = 24.0


def quadro_passarinho(distancia):
    return int(max(0.0, distancia) / DISTANCIA_POR_QUADRO) % 4


def criar_quadros():
    contorno = "#35455D"
    asas = (
        ((9, 8), (9, 2), (12, 1), (14, 3), (13, 9)),
        ((9, 8), (15, 5), (18, 6), (16, 9), (11, 10)),
        ((9, 8), (14, 9), (15, 13), (12, 15), (10, 12)),
        ((9, 8), (14, 7), (18, 9), (15, 11), (10, 10)),
    )
    quadros = []
    for asa in asas:
        imagem = pygame.Surface((20, 16), pygame.SRCALPHA)
        # Perfil para a esquerda, na direção em que atravessa a tela.
        pygame.draw.polygon(imagem, contorno, ((12, 8), (18, 6), (18, 11), (12, 12)))
        pygame.draw.polygon(imagem, "#4A84AD", ((13, 9), (17, 8), (17, 10), (13, 11)))
        pygame.draw.polygon(imagem, contorno, ((5, 6), (11, 6), (14, 8), (14, 11), (11, 13), (6, 12), (4, 9)))
        pygame.draw.polygon(imagem, "#5599C1", ((5, 7), (11, 7), (13, 9), (12, 11), (7, 11), (5, 9)))
        pygame.draw.rect(imagem, "#FFF3D9", (6, 10, 5, 2))
        pygame.draw.polygon(imagem, contorno, asa)
        pygame.draw.line(imagem, "#8CCCE0", (10, 8), asa[1], 1)
        pygame.draw.rect(imagem, contorno, (3, 5, 5, 5))
        pygame.draw.rect(imagem, "#5599C1", (4, 6, 4, 3))
        pygame.draw.rect(imagem, "#FFF3D9", (4, 7, 2, 2))
        pygame.draw.rect(imagem, "#241E26", (4, 7, 1, 1))
        pygame.draw.polygon(imagem, "#E69035", ((0, 8), (3, 7), (3, 9)))
        quadros.append(pygame.transform.scale(imagem, (40, 32)))
    return tuple(quadros)


def salvar_folha(caminho):
    folha = pygame.Surface((160, 32), pygame.SRCALPHA)
    for indice, quadro in enumerate(criar_quadros()):
        folha.blit(quadro, (indice * 40, 0))
    pygame.image.save(folha, str(caminho))
