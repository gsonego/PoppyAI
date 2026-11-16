"""Ponto de entrada: menu e coordenação das partidas de humano, treino e avaliação."""

import argparse

import pygame

from ambiente import Ambiente
from avaliacao import Avaliacao
from campeao import GravadorCampeao
from config import ALTURA, FPS, LARGURA, SEMENTE_TREINO
from humano import JogoHumano
from interface import OPCOES_MENU, RecursosInterface, botoes_menu, desenhar, desenhar_menu
from politica import decidir_salto
from treino import Treino


def escolher_modo(tela, recursos, relogio, aviso=""):
    selecionado = 0
    while True:
        relogio.tick(FPS)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
                if evento.key in (pygame.K_DOWN, pygame.K_UP):
                    selecionado = (selecionado + (1 if evento.key == pygame.K_DOWN else -1)) % len(OPCOES_MENU)
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return OPCOES_MENU[selecionado][0]
            if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                for indice, retangulo in enumerate(botoes_menu()):
                    if retangulo.collidepoint(evento.pos):
                        selecionado = indice
                        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                            return OPCOES_MENU[indice][0]
        desenhar_menu(tela, recursos, selecionado, aviso)


def jogar(tela, recursos, relogio, modo, semente):
    """Retorna True para fechar a janela, False para voltar ao menu."""
    gravador = GravadorCampeao() if modo == "treino" else None
    sessao = None
    ambiente = None
    try:
        if modo == "treino":
            sessao = Treino(salvar=gravador.agendar)
        elif modo == "humano":
            sessao = JogoHumano()
        else:
            sessao = Avaliacao(semente=semente)
        ambiente = Ambiente(semente)
        pygame.display.set_caption(f"PoppyAI — {modo}")
        detalhes = False
        while True:
            relogio.tick(FPS)
            if gravador is not None:
                gravador.verificar_erro()
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return True
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        return False
                    if evento.key == pygame.K_TAB and modo != "humano":
                        detalhes = not detalhes
                    if evento.key == pygame.K_r:
                        if modo == "treino":
                            sessao.registrar_progresso(ambiente, forcar=True)
                            ambiente.reiniciar_manualmente()
                        else:
                            if modo == "humano":
                                sessao.salvar_recorde(ambiente)
                            ambiente.reiniciar(semente)
                            sessao.concluida = False
                    if evento.key == pygame.K_SPACE and modo in ("treino", "humano"):
                        ambiente.pular_manualmente()

            if modo == "treino" or not sessao.concluida:
                pedir_salto = False
                if modo != "humano":
                    pedir_salto = decidir_salto(
                        ambiente.distancia, ambiente.obstaculo.height, sessao.parametros,
                    )
                ambiente.avancar(pedir_salto)
                if sessao.terminou(ambiente):
                    sessao.concluir_tentativa(ambiente)
                    if modo == "treino":
                        ambiente.reiniciar(SEMENTE_TREINO)
                elif modo == "treino":
                    sessao.registrar_progresso(ambiente)
            desenhar(tela, recursos, ambiente, sessao, modo, detalhes)
    finally:
        try:
            if sessao is not None and ambiente is not None:
                if modo == "treino":
                    sessao.registrar_progresso(ambiente, forcar=True)
                elif modo == "humano":
                    sessao.salvar_recorde(ambiente)
        finally:
            if gravador is not None:
                gravador.fechar()


def main(modo=None, semente=None):
    if modo not in (None, "treino", "avaliacao", "humano"):
        raise ValueError("Modo inválido.")
    if semente is not None and modo != "avaliacao":
        raise ValueError("--semente só pode ser usada no modo avaliacao.")
    semente_partida = SEMENTE_TREINO if semente is None else semente
    pygame.init()
    try:
        tela = pygame.display.set_mode((LARGURA, ALTURA))
        recursos = RecursosInterface()
        relogio = pygame.time.Clock()
        aviso = ""
        while True:
            pelo_menu = modo is None
            if pelo_menu:
                pygame.display.set_caption("PoppyAI")
                modo = escolher_modo(tela, recursos, relogio, aviso)
                if modo is None:
                    break
                semente_partida = SEMENTE_TREINO
            try:
                if jogar(tela, recursos, relogio, modo, semente_partida):
                    break
                aviso = ""
            except (SystemExit, OSError, ValueError) as erro:
                if not pelo_menu:
                    raise
                print(f"Não foi possível abrir ou continuar {modo}: {erro}")
                aviso = (
                    "CAMPEA INDISPONIVEL. VEJA O TERMINAL OU TREINE."
                    if modo == "avaliacao" else "FALHA AO SALVAR OU CARREGAR. VEJA O TERMINAL."
                )
            modo = None
    finally:
        pygame.quit()


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description="Jogar com a Poppy, treinar ou avaliar a IA.")
    argumentos.add_argument("--modo", choices=("humano", "treino", "avaliacao"),
                            help="Abre uma partida diretamente; sem esta opção, mostra o menu.")
    argumentos.add_argument("--semente", type=int,
                            help=f"Sequência de obstáculos na avaliação (padrão: {SEMENTE_TREINO}).")
    opcoes = argumentos.parse_args()
    if opcoes.semente is not None and opcoes.modo != "avaliacao":
        argumentos.error("--semente só pode ser usada no modo avaliacao.")
    main(opcoes.modo, opcoes.semente)
