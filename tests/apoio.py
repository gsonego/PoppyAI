from config import PASSO


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
