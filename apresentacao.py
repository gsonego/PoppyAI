"""Vista interpolada para desenho. Não altera o estado usado pela IA ou colisões."""

from config import LARGURA


class VistaAmbiente:
    def __init__(self, ambiente, fracao):
        self._ambiente = ambiente
        fracao = max(0.0, min(1.0, fracao))
        self.distancia_percorrida = (ambiente.distancia_anterior
                                    + (ambiente.distancia_percorrida - ambiente.distancia_anterior) * fracao)
        self._deslocamento = ambiente.distancia_percorrida - self.distancia_percorrida
        self.personagem = ambiente.personagem.copy()
        self.personagem.y = round(ambiente.posicao_y_anterior
                                  + (ambiente.posicao_y - ambiente.posicao_y_anterior) * fracao)
        self.obstaculo = ambiente.obstaculo.copy()
        self.obstaculo.x = round(ambiente.obstaculo_x + self._deslocamento)

    def __getattr__(self, nome):
        return getattr(self._ambiente, nome)

    @property
    def caixas_visiveis(self):
        caixas = []
        for grupo in self._ambiente.grupos:
            x = round(grupo.x + self._deslocamento)
            if x < LARGURA and x + grupo.retangulo.width > 0:
                deslocamento = x - grupo.retangulo.x
                caixas.extend(c.move(deslocamento, 0) for c in self._ambiente._caixas_do_grupo(grupo))
        return tuple(caixas)

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
        retangulos = []
        for grupo in self._ambiente.grupos:
            if grupo.tipo != tipo:
                continue
            retangulo = grupo.retangulo.copy()
            retangulo.x = round(grupo.x + self._deslocamento)
            if retangulo.left < LARGURA and retangulo.right > 0:
                retangulos.append(retangulo)
        return tuple(retangulos)
