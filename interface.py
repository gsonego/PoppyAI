"""Desenho do jogo; não altera a simulação nem os parâmetros."""

import pygame

from config import CHAO_Y, LARGURA
from politica import decidir_salto, limiar_salto


def desenhar_decisao(tela, fonte, ambiente, sessao, modo):
    peso_distancia, peso_altura, vies = sessao.parametros
    altura = ambiente.obstaculo.height
    limiar = limiar_salto(altura, sessao.parametros)
    cor = (185, 95, 15)

    if peso_distancia == 0:
        pedido_constante = decidir_salto(0, altura, sessao.parametros)
        regra = (
            "Nesta altura: pede salto em qualquer distância"
            if pedido_constante else "Nesta altura: não pede salto"
        )
    elif limiar is None:
        regra = "Limite de salto fora da escala de exibição"
    else:
        sentido = "abaixo" if peso_distancia < 0 else "acima"
        regra = f"Nesta altura: pede salto {sentido} de {limiar:.1f} px"
        if limiar < 0:
            regra += " (atrás do personagem)"

    pedido = decidir_salto(ambiente.distancia, altura, sessao.parametros)
    if ambiente.fim_de_jogo or (modo == "avaliacao" and sessao.concluida):
        estado = "partida encerrada"
    elif not ambiente.no_chao:
        estado = "em voo; aguarda pouso"
    elif ambiente.distancia < 0:
        estado = "obstáculo passou da frente do personagem"
    else:
        estado = "no chão"

    linhas = (
        f"Peso distância: {peso_distancia:.4f} | Peso altura: {peso_altura:.4f} | Viés: {vies:.4f}",
        f"Distância: {ambiente.distancia} px | Altura do obstáculo: {altura} px",
        regra,
        f"Pedido nesta distância: {'SALTAR' if pedido else 'ESPERAR'} | {estado}",
    )
    for indice, linha in enumerate(linhas):
        texto = fonte.render(linha, True, cor if indice == 2 else (40, 40, 40))
        tela.blit(texto, (20, 120 + indice * 24))

    # A distância é medida entre a frente do personagem e a frente do obstáculo.
    # A marca indica z = 0; o salto exige z > 0 e personagem no chão.
    if limiar is not None and limiar >= 0:
        marca_x = ambiente.personagem.right + limiar
        if 0 <= marca_x < LARGURA:
            marca_x = round(marca_x)
            for y in range(220, CHAO_Y, 12):
                pygame.draw.line(tela, cor, (marca_x, y), (marca_x, min(y + 6, CHAO_Y)), 2)
            pygame.draw.line(tela, cor, (marca_x, CHAO_Y - 6), (marca_x, CHAO_Y + 8), 3)
            rotulo = fonte.render(f"Limite: {limiar:.1f} px", True, cor)
            rotulo_x = max(10, min(marca_x - rotulo.get_width() // 2, LARGURA - rotulo.get_width() - 10))
            tela.blit(rotulo, (rotulo_x, CHAO_Y + 14))


def desenhar(tela, fonte, ambiente, sessao, modo="treino"):
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

    if modo == "treino":
        informacoes = (
            f"Treino | Tentativa: {sessao.tentativa} | "
            f"Tempo: {ambiente.tempo_vivo:.1f}s | "
            f"Recorde: {max(0.0, sessao.melhor_tempo):.1f}s"
        )
    else:
        informacoes = (
            f"Avaliação | Tempo: {ambiente.tempo_vivo:.1f}s | "
            f"Recorde de treino: {sessao.recorde_treino:.1f}s"
        )
    texto = fonte.render(
        informacoes,
        True,
        (40, 40, 40),
    )
    tela.blit(texto, (20, 20))

    if modo == "avaliacao":
        if sessao.concluida:
            resultado = "Colisão" if ambiente.fim_de_jogo else "Limite atingido"
            aviso = f"{resultado}! R: repetir avaliação."
        else:
            aviso = "Campeã fixa | R: reiniciar | Salto manual desativado"
        mensagem = fonte.render(aviso, True, (40, 40, 40))
        tela.blit(mensagem, (20, 60))
        semente = fonte.render(f"Semente da avaliação: {sessao.semente}", True, (40, 40, 40))
        tela.blit(semente, (20, 95))
    elif ambiente.fim_de_jogo:
        mensagem = fonte.render(
            "Colisao! Pressione R para tentar novamente.",
            True,
            (180, 60, 60),
        )
        tela.blit(mensagem, (20, 60))

    desenhar_decisao(tela, fonte, ambiente, sessao, modo)
    pygame.display.flip()
