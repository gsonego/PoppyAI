"""Valores compartilhados do experimento atual."""

from pathlib import Path
from math import ceil

LARGURA = 900
ALTURA = 400
CHAO_Y = 330
POPPY_X = 101
POPPY_LARGURA = 48
POPPY_ALTURA = 56
POPPY_DESLOCAMENTO_VISUAL_X = -5  # Cauda à esquerda e focinho à direita do centro da arte.
GRAVIDADE = 1800
VELOCIDADE_SALTO = -650
VELOCIDADE_OBSTACULO = 350
ACELERACAO_OBSTACULO = 2.5  # +25 px/s a cada 10 segundos, de forma contínua.
VELOCIDADE_MAXIMA = 650
TEMPO_INTERVALO_INICIAL = (1.8, 2.3)
TEMPO_INTERVALO_FINAL = (0.85, 1.15)
TEMPO_REDUCAO_INTERVALOS = 90.0
# Um salto completo mais 0,15 s de margem, mesmo na velocidade máxima.
INTERVALO_MINIMO_PX = ceil(VELOCIDADE_MAXIMA * (2 * abs(VELOCIDADE_SALTO) / GRAVIDADE + 0.15))
FPS = 60
PASSO = 1.0 / FPS
SEMENTE_PARAMETROS = 42
SEMENTE_TREINO = 123
LIMITE_TENTATIVA = None  # Sem limite de tempo: a tentativa termina na colisão.
PASTA_CAMPEOES = Path(__file__).resolve().parent / "dados" / "campeoes"
ARQUIVO_CAMPEAO = PASTA_CAMPEOES / "campeao_intervalos.json"
VERSAO_JOGO = 6  # Só muda quando as regras da partida mudam, não a arquitetura da IA.
ARQUIVO_RECORDE_HUMANO = Path(__file__).resolve().with_name("recorde_humano_intervalos.json")
