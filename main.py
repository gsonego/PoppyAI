"""Ponto de entrada: conecta ambiente, política, treino e interface."""

import pygame

from ambiente import Ambiente
from config import ALTURA, FPS, LARGURA, SEMENTE_TREINO
from interface import desenhar
from politica import decidir_salto
from treino import Treino


def main():
    pygame.init()
    try:
        treino = Treino()
        ambiente = Ambiente(SEMENTE_TREINO)
        tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("PoppyAI")
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
                        ambiente.reiniciar_manualmente()
                    if evento.key == pygame.K_SPACE:
                        ambiente.pular_manualmente()

            pedir_salto = decidir_salto(ambiente.distancia, treino.parametros)
            ambiente.avancar(pedir_salto)
            if treino.terminou(ambiente):
                treino.concluir_tentativa(ambiente)
                ambiente.reiniciar(SEMENTE_TREINO)
            desenhar(tela, fonte, ambiente, treino)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
