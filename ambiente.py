"""Estado e regras de uma partida, sem conhecer o treino ou a janela."""

import random
from dataclasses import dataclass

import pygame

from config import (
    ACELERACAO_OBSTACULO, CHAO_Y, GRAVIDADE, LARGURA, PASSO, POPPY_ALTURA, POPPY_ALTURA_ABAIXADA, POPPY_LARGURA, POPPY_X,
    VELOCIDADE_MAXIMA, VELOCIDADE_OBSTACULO,
    VELOCIDADE_SALTO,
    INTERVALO_MINIMO_PX, TEMPO_INTERVALO_FINAL, TEMPO_INTERVALO_INICIAL, TEMPO_REDUCAO_INTERVALOS,
    TUNEL_COMPRIMENTOS, TUNEL_PASSAGEM_ALTURA, TUNEL_ALTURA_TOTAL,
    PASSARINHO_LARGURA, PASSARINHO_ALTURA, PASSARINHO_CENTRO_Y,
    PEDRA_LARGURA, PEDRA_ALTURA,
    PEDRA_PASSARO_ATRASO, PEDRA_PASSARO_INTERVALO_MINIMO,
)


@dataclass
class GrupoObstaculo:
    retangulo: pygame.Rect
    x: float
    tipo: str
    intervalo_anterior: int = 0


class Ambiente:
    def __init__(self, semente, *, incluir_tuneis=False, incluir_passarinhos=False, incluir_pedras=False):
        self.incluir_tuneis = incluir_tuneis
        self.incluir_passarinhos = incluir_passarinhos
        self.incluir_pedras = incluir_pedras
        self.gerador_obstaculos = random.Random()
        self.personagem = pygame.Rect(POPPY_X, CHAO_Y - POPPY_ALTURA, POPPY_LARGURA, POPPY_ALTURA)
        self._alvo = GrupoObstaculo(pygame.Rect(LARGURA, CHAO_Y - 50, 30, 50), float(LARGURA), "simples")
        self.reiniciar(semente)

    @property
    def obstaculo(self):
        return self._alvo.retangulo

    @property
    def obstaculo_x(self):
        return self._alvo.x

    @obstaculo_x.setter
    def obstaculo_x(self, valor):
        self._alvo.x = float(valor)

    @property
    def tipo_obstaculo(self):
        return self._alvo.tipo

    @tipo_obstaculo.setter
    def tipo_obstaculo(self, valor):
        self._alvo.tipo = valor

    @property
    def distancia(self):
        return self.obstaculo.left - self.personagem.right

    @property
    def elevacao_obstaculo(self):
        """Espaço entre a base do obstáculo e o chão, em pixels lógicos."""
        return CHAO_Y - self.obstaculo.bottom

    @property
    def velocidade(self):
        return min(VELOCIDADE_MAXIMA, VELOCIDADE_OBSTACULO + ACELERACAO_OBSTACULO * self.tempo_vivo)

    @property
    def caixas(self):
        """Caixas que preenchem exatamente o retângulo de colisão do conjunto."""
        return self._caixas_do_grupo(self._alvo)

    @property
    def caixas_visiveis(self):
        return tuple(caixa for grupo in self.grupos
                     if grupo.retangulo.left < LARGURA and grupo.retangulo.right > 0
                     for caixa in self._caixas_do_grupo(grupo))

    @property
    def tuneis_visiveis(self):
        return self._voadores_visiveis("tunel")

    @property
    def passarinhos_visiveis(self):
        return self._voadores_visiveis("passarinho")

    @property
    def pedras_visiveis(self):
        return self._voadores_visiveis("pedra")

    def _voadores_visiveis(self, tipo):
        return tuple(grupo.retangulo.copy() for grupo in self.grupos
                     if grupo.tipo == tipo
                     and grupo.retangulo.left < LARGURA and grupo.retangulo.right > 0)

    @staticmethod
    def _caixas_do_grupo(grupo):
        if grupo.tipo in ("tunel", "passarinho", "pedra"):
            return ()
        x, y, largura, altura = grupo.retangulo
        if grupo.tipo == "lado_a_lado":
            metade = largura // 2
            return (pygame.Rect(x, y, metade, altura),
                    pygame.Rect(x + metade, y, largura - metade, altura))
        if grupo.tipo == "empilhadas":
            metade = altura // 2
            return (pygame.Rect(x, y, largura, metade),
                    pygame.Rect(x, y + metade, largura, altura - metade))
        return (grupo.retangulo.copy(),)

    def _sortear_obstaculo(self, x):
        apresentacao_concluida = not self._primeiro_tunel and not self._primeiro_passarinho
        if self.incluir_pedras and (self._primeira_pedra or (
            apresentacao_concluida and self.gerador_obstaculos.randrange(5) == 0
        )):
            return self._criar_pedra(x)
        if self.incluir_passarinhos and not self._primeiro_tunel:
            # Apresenta os três desafios antes de passar à mistura aleatória.
            if self._primeiro_passarinho or self.gerador_obstaculos.randrange(4) == 0:
                return self._criar_passarinho(x)
        if self.incluir_tuneis:
            # Apresenta o novo desafio após a primeira caixa; depois mistura com caixas.
            tunel = self._primeiro_tunel or self.gerador_obstaculos.randrange(3) == 0
            self._primeiro_tunel = False
            if tunel:
                comprimento = self.gerador_obstaculos.choice(TUNEL_COMPRIMENTOS)
                retangulo = pygame.Rect(round(x), CHAO_Y - TUNEL_ALTURA_TOTAL,
                                        comprimento, TUNEL_ALTURA_TOTAL - TUNEL_PASSAGEM_ALTURA)
                return GrupoObstaculo(retangulo, float(x), "tunel")
        # Metade dos sorteios mantém uma caixa simples; os demais introduzem pares.
        tipo = self.gerador_obstaculos.choice(
            ("simples", "simples", "lado_a_lado", "empilhadas"),
        )
        if tipo == "lado_a_lado":
            largura = 2 * self.gerador_obstaculos.randint(20, 40)
            altura = self.gerador_obstaculos.randint(30, 70)
        elif tipo == "empilhadas":
            largura = self.gerador_obstaculos.randint(20, 40)
            # Dobrar os antigos 70 px ultrapassaria a altura máxima do salto.
            altura = 2 * self.gerador_obstaculos.randint(30, 42)
        else:
            largura = self.gerador_obstaculos.randint(20, 50)
            altura = self.gerador_obstaculos.randint(30, 70)
        retangulo = pygame.Rect(round(x), CHAO_Y - altura, largura, altura)
        return GrupoObstaculo(retangulo, float(x), tipo)

    def _criar_pedra(self, x):
        self._primeira_pedra = False
        retangulo = pygame.Rect(round(x), CHAO_Y - PEDRA_ALTURA, PEDRA_LARGURA, PEDRA_ALTURA)
        return GrupoObstaculo(retangulo, float(x), "pedra")

    def _criar_passarinho(self, x):
        self._primeiro_passarinho = False
        retangulo = pygame.Rect(round(x), PASSARINHO_CENTRO_Y - PASSARINHO_ALTURA // 2,
                                PASSARINHO_LARGURA, PASSARINHO_ALTURA)
        return GrupoObstaculo(retangulo, float(x), "passarinho")

    def _sortear_intervalo(self):
        progresso = min(1.0, self.tempo_vivo / TEMPO_REDUCAO_INTERVALOS)
        minimo, maximo = (inicio + (fim - inicio) * progresso
                          for inicio, fim in zip(TEMPO_INTERVALO_INICIAL, TEMPO_INTERVALO_FINAL))
        tempo = self.gerador_obstaculos.uniform(minimo, maximo)
        return max(INTERVALO_MINIMO_PX, round(self.velocidade * tempo))

    def _completar_pista(self):
        self.grupos = [grupo for grupo in self.grupos if grupo.retangulo.right >= 0]
        if not self.grupos:
            self.grupos.append(self._sortear_obstaculo(LARGURA))
        while self.grupos[-1].retangulo.left < LARGURA:
            anterior = self.grupos[-1]
            if anterior.tipo == "pedra" and self.incluir_pedras and self.incluir_passarinhos:
                # Obstáculos independentes, com o pássaro um pouco atrás da pedra.
                # Só esta sequência usa o intervalo curto: ambos permitem correr em pé.
                intervalo = max(PEDRA_PASSARO_INTERVALO_MINIMO,
                                round(self.velocidade * PEDRA_PASSARO_ATRASO))
                proximo = self._criar_passarinho(anterior.x + anterior.retangulo.width + intervalo)
            else:
                intervalo = self._sortear_intervalo()
                x = anterior.x + anterior.retangulo.width + intervalo
                if anterior.tipo == "tunel" and self.incluir_pedras:
                    # Exige levantar após o túnel; mantém toda a margem de reação.
                    proximo = self._criar_pedra(x)
                else:
                    proximo = self._sortear_obstaculo(x)
            proximo.intervalo_anterior = intervalo
            self.grupos.append(proximo)
        self._alvo = next((g for g in self.grupos if g.retangulo.right > self.personagem.left), self.grupos[-1])

    def _reposicionar(self):
        self.abaixada = False
        self.pedido_abaixar = False
        self.personagem.height = POPPY_ALTURA
        self.posicao_y = float(CHAO_Y - self.personagem.height)
        self.personagem.y = round(self.posicao_y)
        self.velocidade_y = 0.0
        self.no_chao = True
        self._alvo = GrupoObstaculo(self.obstaculo.copy(), float(LARGURA), self.tipo_obstaculo)
        self.grupos = [self._alvo]
        self.obstaculo_x = float(LARGURA)
        self.obstaculo.x = round(self.obstaculo_x)
        self.tempo_vivo = 0.0
        self.distancia_percorrida = 0.0
        self.distancia_anterior = 0.0
        self.posicao_y_anterior = self.posicao_y
        self.fim_de_jogo = False

    def reiniciar(self, semente):
        self._reposicionar()
        self.gerador_obstaculos.seed(semente)
        self.tipo_obstaculo = "simples"
        self.obstaculo.size = (30, 50)
        self.obstaculo.bottom = CHAO_Y
        self.tentativa_manual = False
        self._primeiro_tunel = self.incluir_tuneis
        self._primeiro_passarinho = self.incluir_passarinhos
        self._primeira_pedra = self.incluir_pedras

    def reiniciar_manualmente(self):
        # Preserva o comportamento de R: mantém tamanho e sequência atuais.
        self._reposicionar()
        self.tentativa_manual = True

    def _pular(self):
        if self.abaixada:
            return
        self.velocidade_y = VELOCIDADE_SALTO
        self.no_chao = False

    def definir_abaixada(self, pedido):
        if self.fim_de_jogo:
            return
        self.pedido_abaixar = bool(pedido)
        self._atualizar_postura()

    def _atualizar_postura(self):
        abaixada = self.pedido_abaixar and self.no_chao
        if abaixada == self.abaixada:
            return
        self.abaixada = abaixada
        self.personagem.height = POPPY_ALTURA_ABAIXADA if abaixada else POPPY_ALTURA
        self.personagem.bottom = CHAO_Y
        self.posicao_y = float(self.personagem.y)
        # Mudança de postura é imediata, mantendo os pés apoiados no chão.
        self.posicao_y_anterior = self.posicao_y

    def pular_manualmente(self):
        if self.no_chao and not self.fim_de_jogo:
            self.tentativa_manual = True
            self._pular()

    def _colidiu(self, grupo):
        if grupo.tipo == "pedra":
            # As pernas em pé transpõem a pedra. Abaixada, a frente do corpo
            # encontra a rocha; depois de passar o focinho, pode abaixar novamente.
            focinho = pygame.Rect(self.personagem.right - 12, self.personagem.top,
                                  12, self.personagem.height)
            return self.abaixada and focinho.colliderect(grupo.retangulo)
        return self.personagem.colliderect(grupo.retangulo)

    def avancar(self, pedir_salto):
        if self.fim_de_jogo:
            return
        self.distancia_anterior = self.distancia_percorrida
        self.posicao_y_anterior = self.posicao_y
        if self.distancia >= 0 and self.no_chao and pedir_salto:
            self._pular()

        self.velocidade_y += GRAVIDADE * PASSO
        self.posicao_y += self.velocidade_y * PASSO
        if self.posicao_y >= CHAO_Y - self.personagem.height:
            self.posicao_y = float(CHAO_Y - self.personagem.height)
            self.velocidade_y = 0.0
            self.no_chao = True
        self.personagem.y = round(self.posicao_y)

        self._atualizar_postura()

        deslocamento = self.velocidade * PASSO
        self.distancia_percorrida += deslocamento
        for grupo in self.grupos:
            grupo.x -= deslocamento
            grupo.retangulo.x = round(grupo.x)
        self._completar_pista()

        # Os pares não têm vãos: a união é um retângulo, usado também no sensor.
        if any(self._colidiu(grupo) for grupo in self.grupos):
            self.fim_de_jogo = True
        else:
            self.tempo_vivo += PASSO
