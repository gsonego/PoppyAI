"""Monta os três comprimentos do túnel a partir da arte aprovada."""

import pygame

from config import TUNEL_ALTURA_TOTAL, TUNEL_COMPRIMENTOS, TUNEL_PASSAGEM_ALTURA


def carregar_tuneis(caminho):
    imagem = pygame.image.load(caminho).convert_alpha()
    imagem = imagem.subsurface(imagem.get_bounding_rect(min_alpha=128))
    largura, altura = imagem.get_size()
    # Separa o bloco, o fundo da passagem e a base para que as três medidas
    # mantenham a mesma abertura de 42 px, sem comprimir a Poppy ou levantar o chão.
    teto = round(altura * 0.75)
    base = round(altura * 0.92)
    partes = (imagem.subsurface((0, 0, largura, teto)),
              imagem.subsurface((0, teto, largura, base - teto)),
              imagem.subsurface((0, base, largura, altura - base)))
    alturas = (TUNEL_ALTURA_TOTAL - TUNEL_PASSAGEM_ALTURA, TUNEL_PASSAGEM_ALTURA, 2)
    sprites = {}
    for comprimento in TUNEL_COMPRIMENTOS:
        sprite = pygame.Surface((comprimento, TUNEL_ALTURA_TOTAL + 2), pygame.SRCALPHA)
        y = 0
        for parte, tamanho_y in zip(partes, alturas):
            # Grade de dois pixels e escala sem suavização, como o restante da arte.
            reduzida = pygame.transform.scale(parte, (comprimento // 2, tamanho_y // 2))
            sprite.blit(pygame.transform.scale(reduzida, (comprimento, tamanho_y)), (0, y))
            y += tamanho_y
        sprites[comprimento] = sprite
    return sprites
