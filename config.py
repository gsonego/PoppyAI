"""Valores compartilhados do experimento atual."""

from pathlib import Path

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
FPS = 60
PASSO = 1.0 / FPS
PAUSA_COLISAO_MS = 450  # Tempo visual antes da próxima tentativa no treino.
SEMENTE_PARAMETROS = 42
SEMENTE_TREINO = 123
LIMITE_TENTATIVA = None  # Sem limite de tempo: a tentativa termina na colisão.
ARQUIVO_CAMPEAO = Path(__file__).resolve().with_name("campeao_colisao.json")
VERSAO_JOGO = 4  # Só muda quando as regras da partida mudam, não a arquitetura da IA.
ARQUIVO_RECORDE_HUMANO = Path(__file__).resolve().with_name("recorde_humano_colisao.json")
