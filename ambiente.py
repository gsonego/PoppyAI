"""Estado e regras de uma partida, sem conhecer o treino ou a janela."""

import random

import pygame

from config import (
    CHAO_Y, GRAVIDADE, LARGURA, PASSO, VELOCIDADE_OBSTACULO,
    VELOCIDADE_SALTO,
)


class Ambiente:
    def __init__(self, semente):
        self.gerador_obstaculos = random.Random()
        self.personagem = pygame.Rect(100, CHAO_Y - 40, 40, 40)
        self.obstaculo = pygame.Rect(LARGURA, CHAO_Y - 50, 30, 50)
        self.reiniciar(semente)

    @property
    def distancia(self):
        return self.obstaculo.left - self.personagem.right

    @property
    def caixas(self):
        """Caixas que preenchem exatamente o retângulo de colisão do conjunto."""
        x, y, largura, altura = self.obstaculo
        if self.tipo_obstaculo == "lado_a_lado":
            metade = largura // 2
            return (pygame.Rect(x, y, metade, altura),
                    pygame.Rect(x + metade, y, largura - metade, altura))
        if self.tipo_obstaculo == "empilhadas":
            metade = altura // 2
            return (pygame.Rect(x, y, largura, metade),
                    pygame.Rect(x, y + metade, largura, altura - metade))
        return (self.obstaculo.copy(),)

    def _sortear_obstaculo(self):
        # Metade dos sorteios mantém uma caixa simples; os demais introduzem pares.
        self.tipo_obstaculo = self.gerador_obstaculos.choice(
            ("simples", "simples", "lado_a_lado", "empilhadas"),
        )
        if self.tipo_obstaculo == "lado_a_lado":
            largura = 2 * self.gerador_obstaculos.randint(20, 40)
            altura = self.gerador_obstaculos.randint(30, 70)
        elif self.tipo_obstaculo == "empilhadas":
            largura = self.gerador_obstaculos.randint(20, 40)
            # Dobrar os antigos 70 px ultrapassaria a altura máxima do salto.
            altura = 2 * self.gerador_obstaculos.randint(30, 42)
        else:
            largura = self.gerador_obstaculos.randint(20, 50)
            altura = self.gerador_obstaculos.randint(30, 70)
        self.obstaculo.size = (largura, altura)
        self.obstaculo.bottom = CHAO_Y
        intervalo_extra = self.gerador_obstaculos.randint(0, 250)
        self.obstaculo_x = float(LARGURA + intervalo_extra)
        self.obstaculo.x = round(self.obstaculo_x)

    def _reposicionar(self):
        self.posicao_y = float(CHAO_Y - self.personagem.height)
        self.personagem.y = round(self.posicao_y)
        self.velocidade_y = 0.0
        self.no_chao = True
        self.obstaculo_x = float(LARGURA)
        self.obstaculo.x = round(self.obstaculo_x)
        self.tempo_vivo = 0.0
        self.distancia_percorrida = 0.0
        self.fim_de_jogo = False

    def reiniciar(self, semente):
        self._reposicionar()
        self.gerador_obstaculos.seed(semente)
        self.tipo_obstaculo = "simples"
        self.obstaculo.size = (30, 50)
        self.obstaculo.bottom = CHAO_Y
        self.tentativa_manual = False

    def reiniciar_manualmente(self):
        # Preserva o comportamento de R: mantém tamanho e sequência atuais.
        self._reposicionar()
        self.tentativa_manual = True

    def _pular(self):
        self.velocidade_y = VELOCIDADE_SALTO
        self.no_chao = False

    def pular_manualmente(self):
        if self.no_chao and not self.fim_de_jogo:
            self.tentativa_manual = True
            self._pular()

    def avancar(self, pedir_salto):
        if self.fim_de_jogo:
            return
        if self.distancia >= 0 and self.no_chao and pedir_salto:
            self._pular()

        self.velocidade_y += GRAVIDADE * PASSO
        self.posicao_y += self.velocidade_y * PASSO
        if self.posicao_y >= CHAO_Y - self.personagem.height:
            self.posicao_y = float(CHAO_Y - self.personagem.height)
            self.velocidade_y = 0.0
            self.no_chao = True
        self.personagem.y = round(self.posicao_y)

        deslocamento = VELOCIDADE_OBSTACULO * PASSO
        self.distancia_percorrida += deslocamento
        self.obstaculo_x -= deslocamento
        self.obstaculo.x = round(self.obstaculo_x)
        if self.obstaculo.right < 0:
            self._sortear_obstaculo()

        # Os pares não têm vãos: a união é um retângulo, usado também no sensor.
        if self.personagem.colliderect(self.obstaculo):
            self.fim_de_jogo = True
        else:
            self.tempo_vivo += PASSO
