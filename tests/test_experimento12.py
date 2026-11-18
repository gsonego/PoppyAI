"""Variedade após túneis, controle de repetições e histórico do experimento 11."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ambiente import Ambiente
from campeao import salvar_campeao, VERSAO_EXPERIMENTO
from config import INTERVALO_MINIMO_PX
from geracoes import TreinoGeracoes
from tests.test_rede import politica_conhecida


def familia(tipo):
    return "caixa" if tipo in ("simples", "lado_a_lado", "empilhadas") else tipo


def percurso(ambiente, quadros=2400):
    ambiente.personagem.x = -10000
    vistos = {}
    sequencia = []
    for _ in range(quadros):
        ambiente.avancar(False)
        for grupo in ambiente.grupos:
            if id(grupo) not in vistos:
                vistos[id(grupo)] = grupo
                sequencia.append((familia(grupo.tipo), tuple(grupo.retangulo.size), grupo.intervalo_anterior))
    return sequencia


class TestExperimento12(unittest.TestCase):
    def test_tunel_tem_tres_sucessores_possiveis_sem_dois_seguidos(self):
        sucessores = set()
        for semente in range(12):
            ambiente = Ambiente(semente, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
            sequencia = percurso(ambiente)
            for anterior, proximo in zip(sequencia, sequencia[1:]):
                if anterior[0] == "tunel":
                    sucessores.add(proximo[0])
                    self.assertNotEqual(proximo[0], "tunel")
                    self.assertGreaterEqual(proximo[2], INTERVALO_MINIMO_PX)
        self.assertEqual(sucessores, {"caixa", "pedra", "passarinho"})

    def test_limita_familias_repetidas_e_preserva_pedra_com_passaro_proximo(self):
        for semente in range(6):
            ambiente = Ambiente(semente, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
            sequencia = percurso(ambiente)
            desafios = []
            for indice, item in enumerate(sequencia):
                tipo, _, intervalo = item
                if tipo == "passarinho" and intervalo < INTERVALO_MINIMO_PX:
                    self.assertEqual(sequencia[indice - 1][0], "pedra")
                    continue  # O pássaro acompanhante integra o desafio da pedra.
                desafios.append(tipo)
            for a, b, c in zip(desafios, desafios[1:], desafios[2:]):
                self.assertFalse(a == b == c, (semente, a, b, c))
            for anterior, proximo in zip(sequencia, sequencia[1:]):
                if anterior[0] == "pedra":
                    self.assertEqual(proximo[0], "passarinho")
                    self.assertLess(proximo[2], INTERVALO_MINIMO_PX)

    def test_semente_repete_apos_reset_incluindo_historico_de_sorteio(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
        primeira = percurso(ambiente)
        ambiente.reiniciar(123)
        self.assertEqual(percurso(ambiente), primeira)
        outra = Ambiente(456, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
        self.assertNotEqual(percurso(outra), primeira)

    def test_nao_exige_variedade_quando_so_caixas_estao_habilitadas(self):
        ambiente = Ambiente(123)
        self.assertTrue(all(familia(ambiente._sortear_obstaculo(900).tipo) == "caixa" for _ in range(100)))

    def test_resultado_do_experimento_onze_e_preservado(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            caminho = Path(pasta) / "campeao.json"
            with patch("campeao.VERSAO_EXPERIMENTO", 11):
                salvar_campeao(caminho, politica_conhecida(), 100, None, 123, 50)
            treino = TreinoGeracoes(caminho)
            self.assertEqual(treino.geracao, 1)
            self.assertIsNone(treino.melhores_parametros)
            treino.salvar_melhor(forcar=True)
            self.assertEqual(VERSAO_EXPERIMENTO, 12)
            historico = json.loads(caminho.with_name("historico_experimentos.json").read_text())
            self.assertEqual((historico[0]["experimento"]["versao"], historico[0]["tempo_segundos"],
                              historico[0]["geracao_final"]), (11, 100, 50))
