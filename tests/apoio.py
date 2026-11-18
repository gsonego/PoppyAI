from config import PASSO


def rede_simples(pesos):
    """Fixture: uma combinação conhecida na camada oculta, abaixar desligado."""
    distancia, altura, largura, velocidade, vies = pesos
    return (distancia, altura, largura, velocidade, 0, vies) + (0,) * 18 + (1, 0, 0, 0, 0) + (0, 0, 0, 0, -1)


class RelogioTeste:
    """Um passo fixo por quadro nos testes de fluxo, sem espera real."""

    def __init__(self, *args):
        pass

    def reiniciar(self):
        pass

    def tick(self):
        return PASSO

    def resumo(self):
        return 60.0, 1000 / 60, 1000 / 60
