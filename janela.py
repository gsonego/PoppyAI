"""Amplia a apresentação sem mudar as coordenadas da física ou da interface."""

import pygame

from config import ALTURA, LARGURA

_tamanho_janela = (1350, 600)


def criar_janela():
    global _tamanho_janela
    largura_monitor, altura_monitor = pygame.display.get_desktop_sizes()[0]
    escala = min(2.0, max(1, largura_monitor - 80) / LARGURA,
                 max(1, altura_monitor - 120) / ALTURA)
    tamanho = (max(1, round(LARGURA * escala)), max(1, round(ALTURA * escala)))
    _tamanho_janela = tamanho
    pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    # A simulação e o desenho continuam na resolução original, de 900 × 400.
    return pygame.Surface((LARGURA, ALTURA))


def area_conteudo():
    janela = pygame.display.get_surface()
    largura, altura = janela.get_size()
    if largura * ALTURA <= altura * LARGURA:
        tamanho = (largura, max(1, round(largura * ALTURA / LARGURA)))
    else:
        tamanho = (max(1, round(altura * LARGURA / ALTURA)), altura)
    return pygame.Rect((largura - tamanho[0]) // 2, (altura - tamanho[1]) // 2, *tamanho)


def posicao_logica(posicao):
    """Converte o clique ampliado para a posição dos botões no desenho original."""
    area = area_conteudo()
    if not area.collidepoint(posicao):
        return None
    return ((posicao[0] - area.x) * LARGURA / area.width,
            (posicao[1] - area.y) * ALTURA / area.height)


def tratar_redimensionamento(evento):
    global _tamanho_janela
    janela = pygame.display.get_surface()
    tela_cheia = bool(janela.get_flags() & pygame.FULLSCREEN)
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
        if tela_cheia:
            pygame.display.set_mode(_tamanho_janela, pygame.RESIZABLE)
        else:
            _tamanho_janela = janela.get_size()
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    elif evento.type == pygame.VIDEORESIZE and not tela_cheia:
        pygame.display.set_mode((max(1, evento.w), max(1, evento.h)), pygame.RESIZABLE)


def apresentar(tela):
    janela = pygame.display.get_surface()
    if tela is not janela:
        area = area_conteudo()
        janela.fill("#493B45")
        # Escala sem suavização e sem criar uma superfície grande a cada quadro.
        pygame.transform.scale(tela, area.size, janela.subsurface(area))
    pygame.display.flip()
