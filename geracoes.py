"""População visível de Poppys: mesma partida, políticas independentes e seleção por geração."""

from colorsys import hsv_to_rgb
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from statistics import fmean, median
from uuid import uuid4

from ambiente import Ambiente
from config import LIMITE_TENTATIVA, SEMENTE_TREINO
from politica import aplicar_politica, calcular_saidas, observar, DESVIOS_MUTACAO
from treino import Treino
from campeao import VERSAO_EXPERIMENTO


@dataclass
class Individuo:
    numero: int
    parametros: tuple
    cor: tuple
    ambiente: Ambiente
    ultimo_encontro: int = 0
    politica_hash: str = ""

    def __post_init__(self):
        self.politica_hash = sha256(json.dumps(self.parametros).encode()).hexdigest()[:16]


class TreinoGeracoes(Treino):
    def __init__(self, *args, tamanho=50, registrar=None, **kwargs):
        if tamanho < 2:
            raise ValueError("A população precisa de pelo menos duas Poppys.")
        super().__init__(*args, **kwargs)
        self._registrar = registrar
        self._sessao = uuid4().hex
        self.tamanho = tamanho
        parametros = [self.parametros] + [self._proxima_candidata() for _ in range(tamanho - 1)]
        self._criar_individuos(parametros)
        self._evento("inicio_sessao", geracao_inicial=self.geracao,
                     recorde_herdado=self.melhor_tempo if self.melhores_parametros is not None else None)
        self._evento("inicio_geracao", total=self.tamanho)

    def _criar_individuos(self, parametros):
        self._geracao_registrada = False
        self.individuos = []
        for indice, pesos in enumerate(parametros):
            cor = tuple(round(c * 255) for c in hsv_to_rgb(indice / self.tamanho, 0.85, 0.72))
            ambiente = Ambiente(SEMENTE_TREINO, incluir_tuneis=True, incluir_passarinhos=True,
                                incluir_pedras=True)
            self.individuos.append(Individuo(indice + 1, tuple(pesos), cor, ambiente))

    def _evento(self, tipo, **dados):
        if self._registrar is not None:
            self._registrar({"schema": 1, "tipo": tipo, "sessao": self._sessao,
                             "experimento": VERSAO_EXPERIMENTO, "semente": SEMENTE_TREINO,
                             "geracao": self.geracao, "registrado_em": datetime.now(timezone.utc).isoformat(),
                             **dados})

    def _registrar_resultado(self, poppy, acoes, entradas, alvo_anterior):
        if self._registrar is None:
            return
        ambiente = poppy.ambiente
        for grupo in ambiente.grupos:
            if (grupo.numero > poppy.ultimo_encontro
                    and grupo.retangulo.left < ambiente.personagem.right
                    and grupo.retangulo.right > ambiente.personagem.left):
                poppy.ultimo_encontro = grupo.numero
                self._evento("encontro", individuo=poppy.numero, tempo=ambiente.tempo_vivo,
                             politica=poppy.politica_hash, obstaculo=ambiente.descrever_grupo(grupo))
        if ambiente.fim_de_jogo and ambiente.grupo_colisao is not None:
            grupo = ambiente.grupo_colisao
            z_salto, z_abaixar = calcular_saidas(entradas, poppy.parametros)
            self._evento("colisao", individuo=poppy.numero, tempo=ambiente.tempo_vivo,
                         politica=poppy.politica_hash, obstaculo=ambiente.descrever_grupo(grupo),
                         anterior=grupo.anterior, distancia=grupo.retangulo.left - ambiente.personagem.right,
                         velocidade=ambiente.velocidade, velocidade_y=ambiente.velocidade_y,
                         abaixada=ambiente.abaixada, no_chao=ambiente.no_chao,
                         pediu_salto=acoes[0], pediu_abaixar=acoes[1], entradas=entradas,
                         alvo_da_decisao=ambiente.descrever_grupo(alvo_anterior),
                         saida_salto=z_salto, saida_abaixar=z_abaixar,
                         conflito=z_salto > 0 and z_abaixar > 0)

    def registrar_geracao(self, motivo="fim", definitiva=True):
        if self._geracao_registrada:
            return
        tempos = [p.ambiente.tempo_vivo for p in self.individuos]
        self._evento("geracao", motivo=motivo, concluida=not self.vivos, total=self.tamanho,
                     vivos=len(self.vivos), mortos=self.tamanho - len(self.vivos),
                     melhor_tempo=max(tempos), mediana=median(tempos), media=fmean(tempos),
                     recorde=max(0, self.melhor_tempo),
                     politicas_distintas=len({p.politica_hash for p in self.individuos}))
        if definitiva:
            self._geracao_registrada = True

    def finalizar_registro(self):
        self.registrar_geracao("saida")
        self._evento("fim_sessao")

    @property
    def vivos(self):
        return [poppy for poppy in self.individuos if not poppy.ambiente.fim_de_jogo]

    @property
    def lider(self):
        return max(self.individuos, key=lambda p: (p.ambiente.tempo_vivo, not p.ambiente.fim_de_jogo))

    def salvar_melhor(self, forcar=False):
        lider = self.lider
        self.parametros = lider.parametros
        melhorou = self.registrar_progresso(lider.ambiente, forcar=forcar)
        if forcar and not melhorou:
            self.salvar_contagem()
        return melhorou

    def salvar_contagem(self):
        """Atualiza a geração mesmo se nenhuma candidata superar a campeã."""
        if self.melhores_parametros is not None:
            self._salvar(self.caminho, self.melhores_parametros, self.melhor_tempo,
                         LIMITE_TENTATIVA, SEMENTE_TREINO, self.geracao)

    def avancar(self):
        if not self.vivos:
            self.proxima_geracao()
        for poppy in self.vivos:
            entradas = observar(poppy.ambiente) if self._registrar is not None else None
            alvo_anterior = poppy.ambiente._alvo
            acoes = aplicar_politica(poppy.ambiente, poppy.parametros)
            self._registrar_resultado(poppy, acoes, entradas, alvo_anterior)
        self.salvar_melhor(forcar=not self.vivos)
        if not self.vivos:
            self.registrar_geracao()

    def proxima_geracao(self):
        self.salvar_melhor(forcar=True)
        self.registrar_geracao("fim" if not self.vivos else "antecipada")
        classificadas = sorted(self.individuos,
                               key=lambda p: (p.ambiente.tempo_vivo, not p.ambiente.fim_de_jogo), reverse=True)
        quantidade_elites = max(1, self.tamanho // 10)
        pais = [p.parametros for p in classificadas[:quantidade_elites]]
        # Preserva a campeã histórica, mesmo ao encerrar uma geração cedo com N.
        parametros = [self.melhores_parametros or pais[0]] + pais[1:]
        while len(parametros) < self.tamanho:
            if self.sorteio.random() < 0.20:
                parametros.append(self._sortear_parametros())
            else:
                mae = self.sorteio.choice(pais)
                parametros.append(tuple(peso + self.sorteio.gauss(0, desvio)
                                        for peso, desvio in zip(mae, DESVIOS_MUTACAO)))
        self.geracao += 1
        self._criar_individuos(parametros)
        self._evento("inicio_geracao", total=self.tamanho)
        self.salvar_contagem()
        print(f"Geração {self.geracao}: {self.tamanho} Poppys | recorde={self.melhor_tempo:.2f}s")
