"""Amplia a apresentação sem mudar as coordenadas da física ou da interface."""

import ctypes
import os
from pathlib import Path

import pygame

from config import ALTURA, LARGURA

_tamanho_janela = (1350, 600)
_modo_escalado = False


def _consulta_renderer():
    """Retorna nome e flags do renderer SDL da janela atual, quando disponíveis."""
    if not pygame.display.get_init() or pygame.display.get_surface() is None:
        return None
    try:
        from pygame._sdl2 import Window

        class Info(ctypes.Structure):
            _fields_ = [("nome", ctypes.c_char_p), ("flags", ctypes.c_uint32),
                        ("quantidade", ctypes.c_uint32), ("formatos", ctypes.c_uint32 * 16),
                        ("largura_maxima", ctypes.c_int), ("altura_maxima", ctypes.c_int)]

        sdl = ctypes.CDLL(str(Path(pygame.__file__).parent / "SDL2.dll"))
        sdl.SDL_GetWindowFromID.argtypes = [ctypes.c_uint32]
        sdl.SDL_GetWindowFromID.restype = ctypes.c_void_p
        sdl.SDL_GetRenderer.argtypes = [ctypes.c_void_p]
        sdl.SDL_GetRenderer.restype = ctypes.c_void_p
        sdl.SDL_GetRendererInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Info)]
        sdl.SDL_GetRendererInfo.restype = ctypes.c_int
        janela = sdl.SDL_GetWindowFromID(Window.from_display_module().id)
        renderer = sdl.SDL_GetRenderer(janela)
        if not renderer:
            return None
        info = Info()
        if sdl.SDL_GetRendererInfo(renderer, ctypes.byref(info)) == 0:
            return (info.nome or b"SDL").decode("utf-8", errors="replace"), info.flags
    except (OSError, AttributeError, pygame.error, ImportError):
        pass
    return None


def _usando_escalado():
    if not _modo_escalado:
        return False
    # O segundo teste também reconhece janelas recriadas diretamente nos testes.
    info = _consulta_renderer()
    return info is not None if os.name == "nt" else True


def vsync_ativo():
    if not _modo_escalado or not pygame.display.get_init() or pygame.display.get_driver() == "dummy":
        return False
    info = _consulta_renderer()
    # SDL_RENDERER_ACCELERATED (2) e SDL_RENDERER_PRESENTVSYNC (4).
    return info is not None and info[1] & 6 == 6


def estado_apresentacao():
    if vsync_ativo():
        return "VSYNC ATIVO"
    return "VSYNC SOLICITADO" if _usando_escalado() else "SEM VSYNC"


def _abrir_modo(tela_cheia, tamanho_janela=None):
    global _modo_escalado
    _modo_escalado = False
    flags = pygame.FULLSCREEN if tela_cheia else pygame.RESIZABLE
    if pygame.display.get_driver() != "dummy":
        try:
            os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "0")
            pygame.display.set_mode((LARGURA, ALTURA), flags | pygame.SCALED, vsync=1)
            if not tela_cheia and tamanho_janela is not None:
                from pygame._sdl2 import Window
                Window.from_display_module().size = tamanho_janela
            _modo_escalado = True
            return
        except (pygame.error, ImportError):
            pass
    pygame.display.set_mode((0, 0) if tela_cheia else tamanho_janela or _tamanho_janela, flags)


def taxa_atualizacao():
    """Consulta o monitor pelo SDL já usado pelo Pygame; fallback de 60 Hz."""
    class Modo(ctypes.Structure):
        _fields_ = [("formato", ctypes.c_uint32), ("largura", ctypes.c_int),
                    ("altura", ctypes.c_int), ("hz", ctypes.c_int), ("dados", ctypes.c_void_p)]

    try:
        caminho = Path(pygame.__file__).parent / "SDL2.dll"
        sdl = ctypes.CDLL(str(caminho))
        sdl.SDL_GetCurrentDisplayMode.argtypes = [ctypes.c_int, ctypes.POINTER(Modo)]
        sdl.SDL_GetCurrentDisplayMode.restype = ctypes.c_int
        modo = Modo()
        if sdl.SDL_GetCurrentDisplayMode(0, ctypes.byref(modo)) == 0 and modo.hz > 0:
            # Modos 59/59,94 Hz são tratados como a família nominal de 60 Hz.
            return 60 if 59 <= modo.hz <= 60 else modo.hz
    except (OSError, AttributeError):
        pass
    return 60


def criar_janela():
    global _tamanho_janela
    largura_monitor, altura_monitor = pygame.display.get_desktop_sizes()[0]
    escala = min(2.0, max(1, largura_monitor - 80) / LARGURA,
                 max(1, altura_monitor - 120) / ALTURA)
    tamanho = (max(1, round(LARGURA * escala)), max(1, round(ALTURA * escala)))
    _tamanho_janela = tamanho
    _abrir_modo(True)
    # A simulação e o desenho continuam na resolução original, de 900 × 400.
    return pygame.Surface((LARGURA, ALTURA))


def area_conteudo():
    janela = pygame.display.get_surface()
    largura, altura = pygame.display.get_window_size() if _usando_escalado() else janela.get_size()
    if largura * ALTURA <= altura * LARGURA:
        tamanho = (largura, max(1, round(largura * ALTURA / LARGURA)))
    else:
        tamanho = (max(1, round(altura * LARGURA / ALTURA)), altura)
    return pygame.Rect((largura - tamanho[0]) // 2, (altura - tamanho[1]) // 2, *tamanho)


def posicao_logica(posicao):
    """Converte o clique ampliado para a posição dos botões no desenho original."""
    if _usando_escalado():
        # O SDL já converte os eventos do mouse para a resolução lógica.
        return posicao if 0 <= posicao[0] < LARGURA and 0 <= posicao[1] < ALTURA else None
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
            _abrir_modo(False, _tamanho_janela)
        else:
            _tamanho_janela = pygame.display.get_window_size()
            _abrir_modo(True)
    elif evento.type == pygame.VIDEORESIZE and not tela_cheia:
        if not _usando_escalado():
            pygame.display.set_mode((max(1, evento.w), max(1, evento.h)), pygame.RESIZABLE)


def apresentar(tela):
    janela = pygame.display.get_surface()
    if tela is not janela:
        if _usando_escalado():
            # O renderer amplia e apresenta a textura com VSync, sem uma escala
            # grande por CPU seguida de uma atualização de janela sem sincronismo.
            janela.blit(tela, (0, 0))
        else:
            area = area_conteudo()
            janela.fill("#493B45")
            pygame.transform.scale(tela, area.size, janela.subsurface(area))
    pygame.display.flip()
