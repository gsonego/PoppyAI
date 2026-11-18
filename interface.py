"""Interface em pixel art: menu, partida e detalhes opcionais da IA."""

from pathlib import Path

import pygame

from apresentacao import VistaAmbiente

from art.cenario import CREME, ROSA, TINTA, PaisagemParalaxe, criar_faixa_chao, desenhar_chao
from art.animacao_poppy import carregar_corrida, quadro_corrida
from art.tunel import carregar_tuneis
from art.pedra import criar_sprite as criar_pedra
from art.passarinho import criar_quadros as criar_passarinhos, quadro_passarinho
from art.fonte_pixel import FontePixel
from config import ALTURA, CHAO_Y, LARGURA, POPPY_DESLOCAMENTO_VISUAL_X
from janela import apresentar, estado_apresentacao
from politica import calcular_saidas, decidir_acoes, observar
from sons import Sons

OPCOES_MENU = (("humano", "JOGAR"), ("treino", "TREINAR IA"), ("avaliacao", "VER A IA JOGAR"))


def botoes_menu():
    return [pygame.Rect(450, 122 + indice * 52, 364, 42) for indice in range(3)]


class RecursosInterface:
    def __init__(self):
        self.fonte = FontePixel()
        self.sons = Sons()
        self.paisagem = PaisagemParalaxe()
        self.faixa_chao = criar_faixa_chao()
        self.passarinhos = criar_passarinhos()
        self.pedra = criar_pedra()
        caminho = Path(__file__).resolve().parent / "art" / "source" / "poppy-aprovada.png"
        self.tuneis = carregar_tuneis(caminho.with_name("tunel.png"))
        imagem = pygame.image.load(caminho).convert_alpha()
        self.poppy = imagem.subsurface(imagem.get_bounding_rect(min_alpha=128))
        imagem_atingida = pygame.image.load(caminho.with_name("poppy-atingida.png")).convert_alpha()
        self.poppy_atingida = imagem_atingida.subsurface(imagem_atingida.get_bounding_rect(min_alpha=128))
        imagem_abaixada = pygame.image.load(caminho.with_name("poppy-abaixada.png")).convert_alpha()
        self.poppy_abaixada = imagem_abaixada.subsurface(imagem_abaixada.get_bounding_rect(min_alpha=128))
        self.corrida = carregar_corrida(caminho.with_name("poppy-corrida-proposta.png"))
        self.corrida_abaixada = carregar_corrida(caminho.with_name("poppy-corrida-abaixada.png"))
        self._sprites = {}
        self.interpolacao = 1.0
        self.mostrar_diagnostico = False
        self.relogio = None

    def visual(self, ambiente):
        if self.interpolacao >= 1.0 or ambiente.fim_de_jogo:
            return ambiente
        return VistaAmbiente(ambiente, self.interpolacao)

    def desenhar_diagnostico(self, tela):
        if self.mostrar_diagnostico and self.relogio is not None:
            fps, media, p95 = self.relogio.resumo()
            pygame.draw.rect(tela, CREME, (232, 72, 660, 22))
            self.texto(tela, f"FPS {fps:.1f} / QUADRO {media:.2f} MS / P95 {p95:.2f} MS / {estado_apresentacao()}",
                       240, 80, escala=1)

    def desenhar_fundo(self, tela, distancia=0):
        self.paisagem.desenhar(tela, distancia)
        desenhar_chao(tela, self.faixa_chao, distancia)

    def desenhar_obstaculos(self, tela, ambiente):
        for pedra in ambiente.pedras_visiveis:
            tela.blit(self.pedra, pedra.topleft)
        for caixa in ambiente.caixas_visiveis:
            desenhar_caixa(tela, caixa)
        for tunel in ambiente.tuneis_visiveis:
            tela.blit(self.tuneis[tunel.width], tunel.topleft)
        quadro = self.passarinhos[quadro_passarinho(ambiente.distancia_percorrida)]
        for passarinho in ambiente.passarinhos_visiveis:
            tela.blit(quadro, quadro.get_rect(center=passarinho.center))

    def sprite_corrida(self, altura, indice):
        chave = ("corrida", altura, indice)
        if chave not in self._sprites:
            quadro = self.corrida[indice]
            tamanho = (round(quadro.get_width() * altura / quadro.get_height()), altura)
            self._sprites[chave] = pygame.transform.scale(quadro, tamanho)
        return self._sprites[chave]

    def sprite(self, altura, atingida=False):
        chave = (altura, atingida)
        if chave not in self._sprites:
            tamanho = (round(self.poppy.get_width() * altura / self.poppy.get_height()), altura)
            imagem = self.poppy_atingida if atingida else self.poppy
            self._sprites[chave] = pygame.transform.scale(imagem, tamanho)
        return self._sprites[chave]

    def sprite_abaixada(self, atingida=False, indice=0):
        chave = ("abaixada", atingida, indice)
        if chave not in self._sprites:
            altura = 38
            quadro = self.corrida_abaixada[indice]
            # Mantém a largura aprovada da pose baixa, com o mesmo tamanho em todo o ciclo.
            tamanho = (round(self.poppy_abaixada.get_width() * altura / self.poppy_abaixada.get_height()), altura)
            sprite = pygame.transform.scale(quadro, tamanho)
            if atingida:
                sprite.fill((255, 90, 90), special_flags=pygame.BLEND_RGB_MULT)
            self._sprites[chave] = sprite
        return self._sprites[chave]

    def texto(self, tela, conteudo, x, y, cor=TINTA, escala=2):
        tela.blit(self.fonte.render(conteudo, tuple(pygame.Color(cor)), escala), (x, y))

    def desenhar_som(self, tela, x=640):
        estado = "OFF" if self.sons.silenciado else "ON"
        self.texto(tela, f"M SOM {estado}" if self.sons.disponivel else "SEM AUDIO", x, 380, escala=1)

    def transparente(self, sprite):
        chave = ("transparente", id(sprite))
        if chave not in self._sprites:
            copia = sprite.copy()
            copia.set_alpha(110)
            self._sprites[chave] = copia
        return self._sprites[chave]


def formatar_tempo(segundos):
    total = max(0, int(segundos))
    minutos, segundos = divmod(total, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02}:{segundos:02}" if horas else f"{minutos:02}:{segundos:02}"


def desenhar_menu(tela, recursos, selecionado=0, aviso=""):
    recursos.desenhar_fundo(tela)
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
    recursos.texto(tela, "F3 FPS", 548, 380, escala=1)
    recursos.desenhar_som(tela, 430)
    recursos.desenhar_diagnostico(tela)
    apresentar(tela)


def desenhar_caixa(tela, retangulo):
    x, y, largura, altura = retangulo
    pygame.draw.rect(tela, "#744D3B", retangulo)
    pygame.draw.rect(tela, "#D8A160", (x + 3, y + 3, largura - 6, altura - 6))
    pygame.draw.rect(tela, "#EDBE7C", (x + 3, y + 3, largura - 6, 5))
    for linha in range(y + 15, y + altura - 3, 14):
        pygame.draw.rect(tela, "#B77C4B", (x + 3, linha, largura - 6, 2))
    pygame.draw.line(tela, "#744D3B", (x + 7, y + altura - 8), (x + largura - 8, y + 12), 4)


def desenhar_decisao(tela, recursos, ambiente, sessao, modo, mostrar_sensor=True):
    salto, abaixar = decidir_acoes(ambiente, sessao.parametros)
    z_salto, z_baixo = calcular_saidas(observar(ambiente), sessao.parametros)
    acao = "ABAIXAR" if abaixar else "SALTAR" if salto else "CORRER"
    linhas = [
        f"DIST {ambiente.distancia} / ALT {ambiente.obstaculo.height} / LARG {ambiente.obstaculo.width} / VEL {ambiente.velocidade:.0f} / ELEV {ambiente.elevacao_obstaculo}",
        f"Z SALTO {z_salto:+.3f} / Z ABAIXAR {z_baixo:+.3f} / ACAO {acao} / PRIORIDADE ABAIXAR",
    ]
    for indice in range(4):
        pesos = sessao.parametros[indice * 6:(indice + 1) * 6]
        linhas.append(f"H{indice + 1} (D A L V E B): " + " / ".join(f"{p:+.3f}" for p in pesos))
    for indice, nome in enumerate(("SALTO", "ABAIXAR")):
        pesos = sessao.parametros[24 + indice * 5:29 + indice * 5]
        linhas.append(f"{nome} (H1 H2 H3 H4 B): " + " / ".join(f"{p:+.3f}" for p in pesos))
    if modo == "avaliacao":
        linhas.append(f"SEMENTE {sessao.semente} / PARAMETROS FIXOS")
    pygame.draw.rect(tela, "#80BBC4", (28, 104, 848, 142))
    pygame.draw.rect(tela, CREME, (24, 100, 848, 142))
    recursos.texto(tela, "REDE 5 ENTRADAS / 4 OCULTOS / 2 SAIDAS - TANH E DEGRAU", 40, 110, ROSA, 1)
    for indice, linha in enumerate(linhas):
        recursos.texto(tela, linha, 40, 128 + indice * 12, escala=1)
    if mostrar_sensor:
        pygame.draw.rect(tela, ROSA, ambiente.personagem, 1)
    if mostrar_sensor and ambiente.obstaculo.right >= ambiente.personagem.left:
        pygame.draw.line(tela, ROSA, ambiente.personagem.topright, ambiente.obstaculo.topleft)


def desenhar_poppy(tela, recursos, ambiente, transparente=False):
    ambiente = recursos.visual(ambiente)
    # Corpo e cabeça colidem; pontas das orelhas e cauda são decorativas.
    if ambiente.abaixada:
        indice = quadro_corrida(ambiente.distancia_percorrida)
        sprite = recursos.sprite_abaixada(atingida=ambiente.fim_de_jogo, indice=indice)
    elif ambiente.fim_de_jogo:
        sprite = recursos.sprite(76, atingida=True)
    else:
        # No ar, mantém uma pose com as patas recolhidas até o pouso.
        indice = quadro_corrida(ambiente.distancia_percorrida) if ambiente.no_chao else 1
        sprite = recursos.sprite_corrida(76, indice)
    apoio = (ambiente.personagem.centerx + POPPY_DESLOCAMENTO_VISUAL_X, ambiente.personagem.bottom)
    if transparente:
        sprite = recursos.transparente(sprite)
    tela.blit(sprite, sprite.get_rect(midbottom=apoio))


def desenhar_populacao(tela, recursos, treino, detalhes=False):
    lider = treino.lider
    ambiente = lider.ambiente
    vivos = treino.vivos
    visual = recursos.visual(ambiente)
    recursos.desenhar_fundo(tela, visual.distancia_percorrida)
    recursos.desenhar_obstaculos(tela, visual)
    # Destinos distribuídos na frente da caixa tornam as linhas sobrepostas mais visíveis.
    if ambiente.obstaculo.right >= ambiente.personagem.left:
        for poppy in vivos:
            origem = recursos.visual(poppy.ambiente).personagem.midright
            destino = (visual.obstaculo.left,
                       visual.obstaculo.top + round((poppy.numero - 0.5) * visual.obstaculo.height / treino.tamanho))
            pygame.draw.line(tela, poppy.cor, origem, destino)
    for poppy in vivos:
        if poppy is not lider:
            desenhar_poppy(tela, recursos, poppy.ambiente, transparente=True)
    if vivos:
        desenhar_poppy(tela, recursos, lider.ambiente)
        recursos.texto(tela, f'#{lider.numero:02}', visual.personagem.x,
                       visual.personagem.top - 29, lider.cor, 1)
    recursos.texto(tela, "POPPY", 24, 22, escala=3)
    recursos.texto(tela, ".AI", 116, 24, ROSA)
    recursos.texto(tela, "TREINO", 24, 55)
    recursos.texto(tela, f"GERACAO {treino.geracao}", 24, 78, escala=1)
    recursos.texto(tela, "SOBREVIVENTES", 242, 18, escala=1)
    recursos.texto(tela, f"{len(vivos):02}/{treino.tamanho}", 242, 42, escala=3)
    recursos.texto(tela, "TEMPO", 474, 18)
    recursos.texto(tela, f"VEL {ambiente.velocidade:.0f} PX/S", 474, 78, escala=1)
    recursos.texto(tela, formatar_tempo(ambiente.tempo_vivo), 474, 42, escala=3)
    recursos.texto(tela, "RECORDE IA", 694, 18)
    recursos.texto(tela, formatar_tempo(treino.melhor_tempo), 694, 42, escala=3)
    if detalhes:
        desenhar_decisao(tela, recursos, ambiente, lider, "treino", mostrar_sensor=False)
    pygame.draw.rect(tela, CREME, (0, 368, LARGURA, 32))
    recursos.texto(tela, "N PROXIMA GERACAO", 24, 380, escala=1)
    recursos.texto(tela, "G GRAFICOS", 242, 380, escala=1)
    recursos.texto(tela, "ESC MENU", 380, 380, escala=1)
    recursos.texto(tela, "F11 TELA", 500, 380, escala=1)
    recursos.texto(tela, "F3 FPS", 580, 380, escala=1)
    recursos.texto(tela, "TAB FECHAR IA" if detalhes else "TAB DETALHES IA", 710, 380, escala=1)
    recursos.desenhar_som(tela)
    recursos.desenhar_diagnostico(tela)
    apresentar(tela)


def desenhar(tela, recursos, ambiente, sessao, modo="treino", detalhes=False):
    visual = recursos.visual(ambiente)
    recursos.desenhar_fundo(tela, visual.distancia_percorrida)
    recursos.desenhar_obstaculos(tela, visual)
    desenhar_poppy(tela, recursos, ambiente)
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
    recursos.texto(tela, f"VEL {ambiente.velocidade:.0f} PX/S", 474, 78, escala=1)
    valor = formatar_tempo(ambiente.tempo_vivo)
    recursos.texto(tela, valor, 474, 42, escala=3 if len(valor) <= 8 else 2)
    recursos.texto(tela, "PESSOAL" if modo == "humano" else "RECORDE IA", 694, 18)
    valor = formatar_tempo(recorde)
    recursos.texto(tela, valor, 694, 42, escala=3 if len(valor) <= 8 else 2)
    pygame.draw.rect(tela, "#80BBC4", (660, 24, 2, 40))
    pygame.draw.rect(tela, CREME, (0, 368, LARGURA, 32))
    recursos.texto(tela, "R REINICIAR", 24, 380, escala=1)
    if modo in ("humano", "treino"):
        recursos.texto(tela, "CIMA SALTAR", 174, 380, escala=1)
        if modo == "humano":
            recursos.texto(tela, "BAIXO ABAIXAR", 278, 380, escala=1)
    elif modo == "avaliacao":
        recursos.texto(tela, "N NOVA SEQUENCIA", 174, 380, escala=1)
    recursos.texto(tela, "ESC MENU", 380, 380, escala=1)
    recursos.texto(tela, "F11 TELA", 500, 380, escala=1)
    recursos.texto(tela, "F3 FPS", 580, 380, escala=1)
    if modo != "humano":
        recursos.texto(tela, "TAB FECHAR IA" if detalhes else "TAB DETALHES IA", 710, 380, escala=1)
    recursos.desenhar_som(tela)
    if detalhes and modo != "humano":
        desenhar_decisao(tela, recursos, ambiente, sessao, modo)
    if ambiente.fim_de_jogo and modo != "treino":
        pygame.draw.rect(tela, TINTA, (300, 222, 372, 66))
        recursos.texto(tela, "FIM DE JOGO", 326, 234, CREME)
        recursos.texto(tela, "R PARA REPETIR / ESC MENU", 326, 264, CREME, 1)
    recursos.desenhar_diagnostico(tela)
    apresentar(tela)
