import pygame
import random

pygame.init()

LARGURA = 900
ALTURA = 400
CHAO_Y = 330

GRAVIDADE = 1800
VELOCIDADE_SALTO = -650
VELOCIDADE_OBSTACULO = 350

# Uma sequencia reproduzivel ajuda a investigar os resulados
sorteio = random.Random(42)
gerador_obstaculos = random.Random(123)

PESO_DISTANCIA = sorteio.uniform(-2.0, 2.0)
VIES = sorteio.uniform(-1.0, 1.0)

melhores_parametros = None
melhor_tempo = -1.0
tentativa = 1
LIMITE_TENTATIVA = 30.0

print(
    f"Tentativa {tentativa}: "
    f"peso: {PESO_DISTANCIA:.3f}, viés: {VIES:.3f}"
)

def decidir_salto(distancia):
    entrada = distancia / LARGURA
    z = PESO_DISTANCIA * entrada + VIES
    return z > 0

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Dino AI")
relogio = pygame.time.Clock()
fonte = pygame.font.Font(None, 28)

personagem = pygame.Rect(100, CHAO_Y - 40, 40, 40)
obstaculo = pygame.Rect(LARGURA, CHAO_Y - 50, 30, 50)

posicao_y = float(personagem.y)
obstaculo_x = float(obstaculo.x)
velocidade_y = 0.0
no_chao = True
fim_de_jogo = False
tempo_vivo = 0.0

executando = True

while executando:
    relogio.tick(60)
    dt = 1.0 / 60.0

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_r:
                posicao_y = float(CHAO_Y - personagem.height)
                personagem.y = round(posicao_y)
                velocidade_y = 0.0
                no_chao = True

                obstaculo_x = float(LARGURA)
                obstaculo.x = round(obstaculo_x)

                tempo_vivo = 0.0
                fim_de_jogo = False

            if (
                evento.key == pygame.K_SPACE
                and no_chao
                and not fim_de_jogo
            ):
                velocidade_y = VELOCIDADE_SALTO
                no_chao = False

    if not fim_de_jogo:
        # Observar: distância entre as bordas mais próximas.
        distancia = obstaculo.left - personagem.right

        # Decidir e executar a ação.
        if distancia >= 0 and no_chao and decidir_salto(distancia):
            velocidade_y = VELOCIDADE_SALTO
            no_chao = False
        
        # Movimento do personagem.
        velocidade_y += GRAVIDADE * dt
        posicao_y += velocidade_y * dt

        if posicao_y >= CHAO_Y - personagem.height:
            posicao_y = float(CHAO_Y - personagem.height)
            velocidade_y = 0.0
            no_chao = True

        personagem.y = round(posicao_y)

        # Movimento do obstáculo.
        obstaculo_x -= VELOCIDADE_OBSTACULO * dt
        obstaculo.x = round(obstaculo_x)

        # Se sair da tela, volta pela direita.
        if obstaculo.right < 0:
            obstaculo.width = gerador_obstaculos.randint(20, 50)
            obstaculo.height = gerador_obstaculos.randint(30, 70)
            obstaculo.bottom = CHAO_Y

            intervalo_extra = gerador_obstaculos.randint(0, 250)
            obstaculo_x = float(LARGURA + intervalo_extra)
            obstaculo.x = round(obstaculo_x)

        # Detectar colisão.
        if personagem.colliderect(obstaculo):
            fim_de_jogo = True
        else:
            tempo_vivo += dt

    # Avaliar a tentativa quando houver colisão ou atingir o limite.
    if fim_de_jogo or tempo_vivo >= LIMITE_TENTATIVA:
        pontuacao = min(tempo_vivo, LIMITE_TENTATIVA)
        melhorou = pontuacao > melhor_tempo

        if melhorou:
            melhor_tempo = pontuacao
            melhores_parametros = (PESO_DISTANCIA, VIES)

        motivo = "colisao" if fim_de_jogo else "limite atingido"

        print(
            f"Tentativa {tentativa}: {pontuacao:.2f}s "
            f"({motivo}) | recorde={melhor_tempo:.2f}s"
            + (" | NOVO RECORDE" if melhorou else "")
        )

        # Escolher os parâmetros da próxima tentativa.
        if melhores_parametros is None or sorteio.random() < 0.20:
            # Explorar uma região completamente diferente.
            PESO_DISTANCIA = sorteio.uniform(-2.0, 2.0)
            VIES = sorteio.uniform(-1.0, 1.0)
        else:
            # Criar uma variação da melhor configuração.
            peso_pai, vies_pai = melhores_parametros
            PESO_DISTANCIA = peso_pai + sorteio.gauss(0.0, 0.20)
            VIES = vies_pai + sorteio.gauss(0.0, 0.10)

        tentativa += 1

        # Reiniciar o ambiente nas mesmas condições.
        posicao_y = float(CHAO_Y - personagem.height)
        personagem.y = round(posicao_y)
        velocidade_y = 0.0
        no_chao = True

        gerador_obstaculos.seed(123)

        obstaculo.size = (30, 50)
        obstaculo.bottom = CHAO_Y
        obstaculo_x = float(LARGURA)
        obstaculo.x = round(obstaculo_x)

        tempo_vivo = 0.0
        fim_de_jogo = False

        print(
            f"Tentativa {tentativa}: "
            f"peso={PESO_DISTANCIA:.3f}, vies={VIES:.3f}"
        )

    # Desenhar o estado atual.
    tela.fill((245, 245, 245))

    pygame.draw.line(
        tela, (80, 80, 80),
        (0, CHAO_Y), (LARGURA, CHAO_Y), 2
    )

    cor_personagem = (180, 60, 60) if fim_de_jogo else (40, 130, 220)
    pygame.draw.rect(tela, cor_personagem, personagem)
    pygame.draw.rect(tela, (60, 160, 90), obstaculo)

    # Mostrar o sensor até o personagem ultrapassar o obstáculo.
    if obstaculo.right >= personagem.left:
        pygame.draw.line(
            tela,
            (160, 160, 160),
            personagem.topright,
            obstaculo.topleft,
            2,
        )

    texto = fonte.render(
        f"Tentativa: {tentativa} | "
        f"Tempo: {tempo_vivo:.1f}s | "
        f"Recorde: {max(0.0, melhor_tempo):.1f}s",
        True,
        (40, 40, 40),
    )
    tela.blit(texto, (20, 20))

    if fim_de_jogo:
        mensagem = fonte.render(
            "Colisao! Pressione R para tentar novamente.",
            True,
            (180, 60, 60),
        )
        tela.blit(mensagem, (20, 60))

    pygame.display.flip()

pygame.quit()