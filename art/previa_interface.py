r"""Proposta visual isolada: gera imagens, sem alterar a interface atual do jogo.

Execute da raiz: .\.venv\Scripts\python.exe art/previa_interface.py
"""

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from fonte_pixel import FontePixel


RAIZ = Path(__file__).resolve().parent
CEU = "#B7E5F0"
TINTA = "#493B45"
CREME = "#FFF3D9"
ROSA = "#DC7189"
VERDE = "#64A54C"
TERRA = "#C38B59"


def texto(tela, fonte, conteudo, x, y, cor=TINTA, escala=2):
    tela.blit(fonte.render(conteudo, tuple(pygame.Color(cor)), escala), (x, y))


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


def caixa(tela, x, altura=50, largura=34):
    y = 330 - altura
    pygame.draw.rect(tela, "#744D3B", (x, y, largura, altura))
    pygame.draw.rect(tela, "#D8A160", (x + 3, y + 3, largura - 6, altura - 6))
    pygame.draw.rect(tela, "#EDBE7C", (x + 3, y + 3, largura - 6, 5))
    for linha in range(y + 15, 327, 14):
        pygame.draw.rect(tela, "#B77C4B", (x + 3, linha, largura - 6, 2))
    pygame.draw.line(tela, "#744D3B", (x + 7, y + altura - 8), (x + largura - 8, y + 12), 4)


def previa(com_tentativa=True, detalhes=False):
    tela = pygame.Surface((900, 400))
    fonte = FontePixel()
    terreno(tela)

    # O protótipo mostra a arte aprovada em tamanho legível. Física e colisões
    # permanecem no jogo atual até a composição visual ser aprovada.
    poppy = pygame.image.load(RAIZ / "source" / "poppy-aprovada.png").convert_alpha()
    poppy = poppy.subsurface(poppy.get_bounding_rect(min_alpha=128))
    tamanho = (round(poppy.get_width() * 76 / poppy.get_height()), 76)
    poppy = pygame.transform.scale(poppy, tamanho)
    tela.blit(poppy, (108, 330 - poppy.get_height()))
    caixa(tela, 565)

    # Cabeçalho arejado: nome à esquerda, indicadores alinhados à direita.
    texto(tela, fonte, "POPPY", 24, 22, escala=3)
    texto(tela, fonte, ".AI", 116, 24, ROSA)
    texto(tela, fonte, "TREINO", 24, 55, escala=2)
    if com_tentativa:
        texto(tela, fonte, "TENTATIVA 65", 24, 78, escala=1)
    texto(tela, fonte, "TEMPO", 474, 18, escala=2)
    texto(tela, fonte, "02:14", 474, 42, escala=3)
    texto(tela, fonte, "RECORDE", 694, 18, escala=2)
    texto(tela, fonte, "03:28", 694, 42, escala=3)
    pygame.draw.rect(tela, "#80BBC4", (660, 24, 2, 40))

    pygame.draw.rect(tela, CREME, (0, 368, 900, 32))
    texto(tela, fonte, "R", 24, 378, ROSA)
    texto(tela, fonte, "REINICIAR", 48, 378)
    texto(tela, fonte, "ESPACO", 224, 378, ROSA)
    texto(tela, fonte, "SALTAR", 310, 378)
    texto(tela, fonte, "TAB", 664, 378, ROSA)
    texto(tela, fonte, "FECHAR IA" if detalhes else "DETALHES IA", 710, 378)

    if detalhes:
        pygame.draw.rect(tela, "#80BBC4", (24, 104, 852, 92))
        pygame.draw.rect(tela, CREME, (24, 100, 848, 92))
        texto(tela, fonte, "DECISAO DA POPPY", 40, 112, ROSA, 1)
        texto(tela, fonte, "PESO DIST -1.5000  /  PESO ALT +0.7000  /  VIES +0.4500", 40, 132, escala=1)
        texto(tela, fonte, "DISTANCIA 397 PX  /  ALTURA 50 PX  /  ESPERAR", 40, 152, escala=1)
        texto(tela, fonte, "SALTA ABAIXO DE 322.5 PX", 40, 172, escala=1)
        for y in range(210, 330, 12):
            pygame.draw.rect(tela, ROSA, (490, y, 2, 6))
    return tela


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1))
    destino = RAIZ / "previews"
    destino.mkdir(exist_ok=True)
    for nome, com_tentativa, detalhes in (
        ("interface-com-tentativa.png", True, False),
        ("interface-minima.png", False, False),
        ("interface-detalhes.png", True, True),
    ):
        pygame.image.save(previa(com_tentativa, detalhes), destino / nome)
    pygame.quit()
    print(f"Prévias salvas em {destino}")
