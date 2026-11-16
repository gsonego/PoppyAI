"""Ponto de entrada: conecta ambiente, política, treino e interface."""

import argparse

import pygame

from ambiente import Ambiente
from avaliacao import Avaliacao
from config import ALTURA, FPS, LARGURA, SEMENTE_TREINO
from interface import desenhar
from politica import decidir_salto
from treino import Treino


def main(modo="treino"):
    pygame.init()
    try:
        sessao = Treino() if modo == "treino" else Avaliacao()
        ambiente = Ambiente(SEMENTE_TREINO)
        tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption(f"PoppyAI — {modo}")
        relogio = pygame.time.Clock()
        fonte = pygame.font.Font(None, 28)
        executando = True

        while executando:
            relogio.tick(FPS)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    executando = False
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_r:
                        if modo == "treino":
                            ambiente.reiniciar_manualmente()
                        else:
                            ambiente.reiniciar(SEMENTE_TREINO)
                            sessao.concluida = False
                    if evento.key == pygame.K_SPACE and modo == "treino":
                        ambiente.pular_manualmente()

            if not executando:
                break
            if modo == "treino" or not sessao.concluida:
                pedir_salto = decidir_salto(ambiente.distancia, sessao.parametros)
                ambiente.avancar(pedir_salto)
                if sessao.terminou(ambiente):
                    sessao.concluir_tentativa(ambiente)
                    if modo == "treino":
                        ambiente.reiniciar(SEMENTE_TREINO)
            desenhar(tela, fonte, ambiente, sessao, modo)
    finally:
        pygame.quit()


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description="Treinar ou avaliar a IA do PoppyAI.")
    argumentos.add_argument("--modo", choices=("treino", "avaliacao"), default="treino")
    main(argumentos.parse_args().modo)
