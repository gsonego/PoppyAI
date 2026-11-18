"""Ponto de entrada: menu e coordenação das partidas de humano, treino e avaliação."""

import argparse

import pygame

from ambiente import Ambiente
from avaliacao import Avaliacao
from campeao import GravadorCampeao, VERSAO_EXPERIMENTO
from config import SEMENTE_TREINO, PASTA_TREINOS, ARQUIVO_CAMPEAO
from metricas import GravadorMetricas
from diagnostico import registrar_execucao, registro
from humano import JogoHumano
from interface import OPCOES_MENU, RecursosInterface, botoes_menu, desenhar, desenhar_menu, desenhar_populacao
from janela import criar_janela, posicao_logica, taxa_atualizacao, tratar_redimensionamento
from politica import aplicar_politica
from geracoes import TreinoGeracoes
from temporizacao import AvancoFixo, RelogioQuadros


def tratar_evento_visual(evento, recursos):
    tratar_redimensionamento(evento)
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F3:
        recursos.mostrar_diagnostico = not recursos.mostrar_diagnostico
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_m:
        recursos.sons.alternar()


def escolher_modo(tela, recursos, relogio, aviso=""):
    recursos.mostrar_diagnostico = False
    selecionado = 0
    while True:
        relogio.tick()
        for evento in pygame.event.get():
            tratar_evento_visual(evento, recursos)
            if evento.type == pygame.QUIT:
                registro.info("Pedido de fechar a janela no menu")
                return None
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    registro.info("Saida por Escape no menu")
                    return None
                if evento.key in (pygame.K_DOWN, pygame.K_UP):
                    selecionado = (selecionado + (1 if evento.key == pygame.K_DOWN else -1)) % len(OPCOES_MENU)
                    recursos.sons.tocar("menu_mover")
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    recursos.sons.tocar("menu_confirmar")
                    return OPCOES_MENU[selecionado][0]
            if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                posicao = posicao_logica(evento.pos)
                if posicao is None:
                    continue
                for indice, retangulo in enumerate(botoes_menu()):
                    if retangulo.collidepoint(posicao):
                        if selecionado != indice:
                            recursos.sons.tocar("menu_mover")
                        selecionado = indice
                        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                            recursos.sons.tocar("menu_confirmar")
                            return OPCOES_MENU[indice][0]
        desenhar_menu(tela, recursos, selecionado, aviso)


def jogar_populacao(tela, recursos, relogio):
    gravador = GravadorCampeao()
    metricas = GravadorMetricas(PASTA_TREINOS / f"experimento_{VERSAO_EXPERIMENTO}.jsonl", ARQUIVO_CAMPEAO)
    treino = None
    try:
        treino = TreinoGeracoes(salvar=gravador.agendar, registrar=metricas.agendar)
        pygame.display.set_caption("PoppyAI — treino de 50 Poppys")
        detalhes = False
        avanco = AvancoFixo()
        relogio.reiniciar()
        while True:
            segundos = relogio.tick()
            gravador.verificar_erro()
            for evento in pygame.event.get():
                tratar_evento_visual(evento, recursos)
                if evento.type == pygame.QUIT:
                    registro.info("Pedido de fechar a janela no treino")
                    return True
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        registro.info("Voltando ao menu pelo treino")
                        return False
                    if evento.key == pygame.K_TAB:
                        detalhes = not detalhes
                    if evento.key == pygame.K_n:
                        treino.proxima_geracao()
                    if evento.key == pygame.K_g:
                        treino.registrar_geracao("grafico", definitiva=False)
                        metricas.solicitar_graficos()
            for _ in range(avanco.acumular(segundos)):
                treino.avancar()
            recursos.interpolacao = avanco.fracao
            desenhar_populacao(tela, recursos, treino, detalhes)
    finally:
        try:
            if treino is not None:
                try:
                    treino.salvar_melhor(forcar=True)
                finally:
                    treino.finalizar_registro()
        finally:
            try:
                gravador.fechar()
            finally:
                metricas.fechar()


def jogar(tela, recursos, relogio, modo, semente):
    """Retorna True para fechar a janela, False para voltar ao menu."""
    if modo == "treino":
        return jogar_populacao(tela, recursos, relogio)
    sessao = None
    ambiente = None
    try:
        sessao = JogoHumano() if modo == "humano" else Avaliacao(semente=semente)
        if modo == "avaliacao":
            semente = sessao.semente
        ambiente = Ambiente(semente, incluir_tuneis=True, incluir_passarinhos=True,
                            incluir_pedras=True)
        pygame.display.set_caption(f"PoppyAI — {modo}")
        detalhes = False
        avanco = AvancoFixo()
        relogio.reiniciar()
        while True:
            segundos = relogio.tick()
            for evento in pygame.event.get():
                tratar_evento_visual(evento, recursos)
                if evento.type == pygame.QUIT:
                    registro.info("Pedido de fechar a janela no modo %s", modo)
                    return True
                if modo == "humano":
                    if evento.type in (pygame.KEYDOWN, pygame.KEYUP) and evento.key == pygame.K_DOWN:
                        ambiente.definir_abaixada(evento.type == pygame.KEYDOWN)
                    elif evento.type == pygame.WINDOWFOCUSLOST:
                        ambiente.definir_abaixada(False)
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        registro.info("Voltando ao menu pelo modo %s", modo)
                        return False
                    if evento.key == pygame.K_TAB and modo == "avaliacao":
                        detalhes = not detalhes
                    if evento.key == pygame.K_r:
                        if modo == "humano":
                            sessao.salvar_recorde(ambiente)
                        ambiente.reiniciar(semente)
                        sessao.concluida = False
                    if evento.key == pygame.K_n and modo == "avaliacao":
                        semente = sessao.sortear_semente()
                        ambiente.reiniciar(semente)
                    if evento.key == pygame.K_UP and modo == "humano":
                        estava_no_chao = ambiente.no_chao
                        ambiente.pular_manualmente()
                        if estava_no_chao and not ambiente.no_chao:
                            recursos.sons.tocar("salto")
            for _ in range(avanco.acumular(segundos)):
                if sessao.concluida:
                    break
                estava_no_chao = ambiente.no_chao
                if modo == "avaliacao":
                    aplicar_politica(ambiente, sessao.parametros)
                else:
                    ambiente.avancar(False)
                if modo == "avaliacao" and estava_no_chao and not ambiente.no_chao:
                    recursos.sons.tocar("salto")
                if sessao.terminou(ambiente):
                    novo_recorde = modo == "humano" and ambiente.tempo_vivo > sessao.melhor_tempo
                    sessao.concluir_tentativa(ambiente)
                    recursos.sons.fim_partida(novo_recorde=novo_recorde)
            recursos.interpolacao = avanco.fracao
            desenhar(tela, recursos, ambiente, sessao, modo, detalhes)
    finally:
        if modo == "humano" and sessao is not None and ambiente is not None:
            sessao.salvar_recorde(ambiente)


def main(modo=None, semente=None):
    if modo not in (None, "treino", "avaliacao", "humano"):
        raise ValueError("Modo inválido.")
    if semente is not None and modo != "avaliacao":
        raise ValueError("--semente só pode ser usada no modo avaliacao.")
    semente_partida = semente if modo == "avaliacao" else SEMENTE_TREINO
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try:
        tela = criar_janela()
        recursos = RecursosInterface()
        relogio = RelogioQuadros(taxa_atualizacao())
        recursos.relogio = relogio
        aviso = ""
        while True:
            pelo_menu = modo is None
            if pelo_menu:
                pygame.display.set_caption("PoppyAI")
                modo = escolher_modo(tela, recursos, relogio, aviso)
                if modo is None:
                    break
                semente_partida = None if modo == "avaliacao" else SEMENTE_TREINO
            try:
                registro.info("Abrindo modo %s", modo)
                if jogar(tela, recursos, relogio, modo, semente_partida):
                    break
                aviso = ""
            except (SystemExit, OSError, ValueError) as erro:
                registro.exception("Falha no modo %s", modo)
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
                            help="Sequência de obstáculos na avaliação (padrão: sorteada).")
    opcoes = argumentos.parse_args()
    if opcoes.semente is not None and opcoes.modo != "avaliacao":
        argumentos.error("--semente só pode ser usada no modo avaliacao.")
    with registrar_execucao():
        main(opcoes.modo, opcoes.semente)
