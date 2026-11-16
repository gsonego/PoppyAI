"""Desenho do jogo; não altera a simulação nem os parâmetros."""

import pygame

from config import CHAO_Y, LARGURA


def desenhar(tela, fonte, ambiente, treino):
    tela.fill((245, 245, 245))

    pygame.draw.line(
        tela, (80, 80, 80),
        (0, CHAO_Y), (LARGURA, CHAO_Y), 2
    )

    cor_personagem = (180, 60, 60) if ambiente.fim_de_jogo else (40, 130, 220)
    pygame.draw.rect(tela, cor_personagem, ambiente.personagem)
    pygame.draw.rect(tela, (60, 160, 90), ambiente.obstaculo)

    # Mostrar o sensor até o personagem ultrapassar o obstáculo.
    if ambiente.obstaculo.right >= ambiente.personagem.left:
        pygame.draw.line(
            tela,
            (160, 160, 160),
            ambiente.personagem.topright,
            ambiente.obstaculo.topleft,
            2,
        )

    texto = fonte.render(
        f"Tentativa: {treino.tentativa} | "
        f"Tempo: {ambiente.tempo_vivo:.1f}s | "
        f"Recorde: {max(0.0, treino.melhor_tempo):.1f}s",
        True,
        (40, 40, 40),
    )
    tela.blit(texto, (20, 20))

    if ambiente.fim_de_jogo:
        mensagem = fonte.render(
            "Colisao! Pressione R para tentar novamente.",
            True,
            (180, 60, 60),
        )
        tela.blit(mensagem, (20, 60))

    pygame.display.flip()
