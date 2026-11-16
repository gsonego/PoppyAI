"""Valores compartilhados do experimento atual."""

from pathlib import Path

LARGURA = 900
ALTURA = 400
CHAO_Y = 330
GRAVIDADE = 1800
VELOCIDADE_SALTO = -650
VELOCIDADE_OBSTACULO = 350
FPS = 60
PASSO = 1.0 / FPS
SEMENTE_PARAMETROS = 42
SEMENTE_TREINO = 123
LIMITE_TENTATIVA = 30.0
ARQUIVO_CAMPEAO = Path(__file__).resolve().with_name("campeao_altura.json")
