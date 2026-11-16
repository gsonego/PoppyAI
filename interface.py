"""Interface em pixel art: menu, partida e detalhes opcionais da IA."""

from pathlib import Path

import pygame

from art.cenario import CREME, ROSA, TINTA, terreno
from art.fonte_pixel import FontePixel
from config import ALTURA, CHAO_Y, LARGURA
from janela import apresentar
from politica import decidir_salto, limiar_salto

OPCOES_MENU = (("humano", "JOGAR"), ("treino", "TREINAR IA"), ("avaliacao", "VER A IA JOGAR"))


def botoes_menu():
    return [pygame.Rect(450, 122 + indice * 52, 364, 42) for indice in range(3)]


class RecursosInterface:
    def __init__(self):
        self.fonte = FontePixel()
        self.fundo = pygame.Surface((LARGURA, ALTURA))
        terreno(self.fundo)
        caminho = Path(__file__).resolve().parent / "art" / "source" / "poppy-aprovada.png"
        imagem = pygame.image.load(caminho).convert_alpha()
        self.poppy = imagem.subsurface(imagem.get_bounding_rect(min_alpha=128))
        self._sprites = {}

    def sprite(self, altura):
        if altura not in self._sprites:
            tamanho = (round(self.poppy.get_width() * altura / self.poppy.get_height()), altura)
            self._sprites[altura] = pygame.transform.scale(self.poppy, tamanho)
        return self._sprites[altura]

    def texto(self, tela, conteudo, x, y, cor=TINTA, escala=2):
        tela.blit(self.fonte.render(conteudo, tuple(pygame.Color(cor)), escala), (x, y))


def formatar_tempo(segundos):
    total = max(0, int(segundos))
    minutos, segundos = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02}:{segundos:02}" if horas else f"{minutos:02}:{segundos:02}"


def desenhar_menu(tela, recursos, selecionado=0, aviso=""):
    tela.blit(recursos.fundo, (0, 0))
    sprite = recursos.sprite(162)
    tela.blit(sprite, (156, CHAO_Y - sprite.get_height()))
    recursos.texto(tela, "POPPY.AI", 450, 40, escala=4)
    recursos.texto(tela, "ESCOLHA COMO JOGAR", 452, 86, escala=1)
    for indice, (retangulo, (_, rotulo)) in enumerate(zip(botoes_menu(), OPCOES_MENU)):
        pygame.draw.rect(tela, "#80BBC4", retangulo.move(4, 4))
        pygame.draw.rect(tela, ROSA if indice == selecionado else CREME, retangulo)
        recursos.texto(tela, rotulo, retangulo.x + 22, retangulo.y + 14,
                       CREME if indice == selecionado else TINTA)
    recursos.texto(tela, aviso or "UMA PATINHA DE CADA VEZ", 450, 286, escala=1)
    pygame.draw.rect(tela, CREME, (0, 368, LARGURA, 32))
    recursos.texto(tela, "SETAS + ENTER OU CLIQUE PARA ESCOLHER", 24, 380, escala=1)
    recursos.texto(tela, "ESC SAIR", 780, 380, escala=1)
    recursos.texto(tela, "F11 TELA", 650, 380, escala=1)
    apresentar(tela)


def desenhar_caixa(tela, retangulo):
    x, y, largura, altura = retangulo
    pygame.draw.rect(tela, "#744D3B", retangulo)
    pygame.draw.rect(tela, "#D8A160", (x + 3, y + 3, largura - 6, altura - 6))
    pygame.draw.rect(tela, "#EDBE7C", (x + 3, y + 3, largura - 6, 5))
    for linha in range(y + 15, y + altura - 3, 14):
        pygame.draw.rect(tela, "#B77C4B", (x + 3, linha, largura - 6, 2))
    pygame.draw.line(tela, "#744D3B", (x + 7, y + altura - 8), (x + largura - 8, y + 12), 4)


def desenhar_decisao(tela, recursos, ambiente, sessao, modo):
    peso_distancia, peso_altura, vies = sessao.parametros
    altura = ambiente.obstaculo.height
    limiar = limiar_salto(altura, sessao.parametros)
    pedido = decidir_salto(ambiente.distancia, altura, sessao.parametros)
    if peso_distancia == 0:
        regra = "PEDIDO INDEPENDE DA DISTANCIA NESTA ALTURA"
    elif limiar is None:
        regra = "LIMIAR FORA DA ESCALA DE EXIBICAO"
    else:
        sentido = "ABAIXO" if peso_distancia < 0 else "ACIMA"
        regra = f"SALTA {sentido} DE {limiar:.1f} PX NESTA ALTURA"
    linhas = [
        f"PESO DIST {peso_distancia:+.4f} / PESO ALT {peso_altura:+.4f} / VIES {vies:+.4f}",
        f"DISTANCIA {ambiente.distancia} PX / ALTURA {altura} PX / {'SALTAR' if pedido else 'ESPERAR'}",
        regra,
    ]
    if modo == "avaliacao":
        linhas.append(f"SEMENTE {sessao.semente} / PARAMETROS FIXOS")
    elif ambiente.tentativa_manual:
        linhas.append("INTERVENCAO MANUAL / FORA DO RECORDE")
    pygame.draw.rect(tela, "#80BBC4", (28, 104, 848, 106))
    pygame.draw.rect(tela, CREME, (24, 100, 848, 106))
    recursos.texto(tela, "DECISAO DA POPPY", 40, 110, ROSA, 1)
    for indice, linha in enumerate(linhas):
        recursos.texto(tela, linha, 40, 130 + indice * 18, escala=1)
    pygame.draw.rect(tela, ROSA, ambiente.personagem, 1)
    if ambiente.obstaculo.right >= ambiente.personagem.left:
        pygame.draw.line(tela, ROSA, ambiente.personagem.topright, ambiente.obstaculo.topleft)
    if limiar is not None and 0 <= limiar < LARGURA - ambiente.personagem.right:
        marca_x = round(ambiente.personagem.right + limiar)
        for y in range(214, CHAO_Y, 12):
            pygame.draw.rect(tela, ROSA, (marca_x, y, 2, 6))


def desenhar(tela, recursos, ambiente, sessao, modo="treino", detalhes=False):
    tela.blit(recursos.fundo, (0, 0))
    desenhar_caixa(tela, ambiente.obstaculo)
    # Orelhas e cauda são decorativas; o retângulo da física é preservado.
    sprite = recursos.sprite(76)
    tela.blit(sprite, sprite.get_rect(midbottom=ambiente.personagem.midbottom))
    recursos.texto(tela, "POPPY", 24, 22, escala=3)
    recursos.texto(tela, ".AI", 116, 24, ROSA)
    rotulo = {"humano": "JOGAR", "treino": "TREINO", "avaliacao": "AVALIACAO"}[modo]
    recursos.texto(tela, rotulo, 24, 55)
    if modo == "treino":
        extra = f"TENTATIVA {sessao.tentativa}"
        if ambiente.tentativa_manual:
            extra += " / MANUAL"
        recursos.texto(tela, extra, 24, 78, escala=1)
    recorde = sessao.recorde_treino if modo == "avaliacao" else max(sessao.melhor_tempo, 0)
    if modo == "humano":
        recorde = max(recorde, ambiente.tempo_vivo)
    recursos.texto(tela, "TEMPO", 474, 18)
    valor = formatar_tempo(ambiente.tempo_vivo)
    recursos.texto(tela, valor, 474, 42, escala=3 if len(valor) <= 8 else 2)
    recursos.texto(tela, "PESSOAL" if modo == "humano" else "RECORDE IA", 694, 18)
    valor = formatar_tempo(recorde)
    recursos.texto(tela, valor, 694, 42, escala=3 if len(valor) <= 8 else 2)
    pygame.draw.rect(tela, "#80BBC4", (660, 24, 2, 40))
    pygame.draw.rect(tela, CREME, (0, 368, LARGURA, 32))
    recursos.texto(tela, "R REINICIAR", 24, 380, escala=1)
    if modo in ("humano", "treino"):
        recursos.texto(tela, "ESPACO SALTAR", 174, 380, escala=1)
    recursos.texto(tela, "ESC MENU", 380, 380, escala=1)
    recursos.texto(tela, "F11 TELA", 500, 380, escala=1)
    if modo != "humano":
        recursos.texto(tela, "TAB FECHAR IA" if detalhes else "TAB DETALHES IA", 710, 380, escala=1)
    if detalhes and modo != "humano":
        desenhar_decisao(tela, recursos, ambiente, sessao, modo)
    if ambiente.fim_de_jogo:
        pygame.draw.rect(tela, TINTA, (300, 222, 372, 66))
        recursos.texto(tela, "FIM DE JOGO", 326, 234, CREME)
        recursos.texto(tela, "R PARA REPETIR / ESC MENU", 326, 264, CREME, 1)
    apresentar(tela)
