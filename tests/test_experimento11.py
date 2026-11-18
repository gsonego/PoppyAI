"""Intervalo curto mantido e margem normal depois dos túneis."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ambiente import Ambiente
from campeao import salvar_campeao, VERSAO_EXPERIMENTO
from config import (INTERVALO_MINIMO_PX, PEDRA_PASSARO_ATRASO,
                    PEDRA_PASSARO_INTERVALO_MINIMO, TUNEL_COMPRIMENTOS)
from geracoes import TreinoGeracoes
from tests.test_rede import politica_conhecida


class TestExperimento11(unittest.TestCase):
    def test_intervalo_aprovado_e_menor_que_experimento_dez(self):
        self.assertEqual(PEDRA_PASSARO_ATRASO, 0.10)
        self.assertEqual(PEDRA_PASSARO_INTERVALO_MINIMO, 32)
        for velocidade in (350, 450, 550, 650):
            self.assertLess(max(32, round(velocidade * 0.1)), max(90, round(velocidade * 0.3)))

    def test_cada_comprimento_de_tunel_tem_margem_ate_proximo_desafio(self):
        for comprimento in TUNEL_COMPRIMENTOS:
            for velocidade in (350, 450, 550, 650):
                ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
                ambiente._sortear_obstaculo(0)
                with patch.object(ambiente.gerador_obstaculos, "choice", return_value=comprimento):
                    tunel = ambiente._sortear_obstaculo(0)
                ambiente.grupos = [tunel]
                ambiente._alvo = tunel
                ambiente.tempo_vivo = (velocidade - 350) / 2.5
                with patch.object(ambiente, "_sortear_intervalo", return_value=INTERVALO_MINIMO_PX):
                    ambiente._completar_pista()
                proximo = ambiente.grupos[1]
                self.assertNotEqual(proximo.tipo, "tunel")
                self.assertEqual(proximo.retangulo.left - tunel.retangulo.right, INTERVALO_MINIMO_PX)

    def test_percurso_real_nao_tem_tuneis_consecutivos_e_repete_apos_reiniciar(self):
        def percurso(ambiente):
            ambiente.personagem.x = -10000
            vistos = {}
            sequencia = []
            for _ in range(1800):
                ambiente.avancar(False)
                for grupo in ambiente.grupos:
                    if id(grupo) not in vistos:
                        vistos[id(grupo)] = grupo
                        sequencia.append((grupo.tipo, tuple(grupo.retangulo.size), grupo.intervalo_anterior))
            return sequencia
        for semente in (1, 123, 456):
            ambiente = Ambiente(semente, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
            primeira = percurso(ambiente)
            self.assertIn("tunel", [tipo for tipo, _, _ in primeira])
            for anterior, proximo in zip(primeira, primeira[1:]):
                if anterior[0] == "tunel":
                    self.assertNotEqual(proximo[0], "tunel")
                    self.assertGreaterEqual(proximo[2], INTERVALO_MINIMO_PX)
            ambiente.reiniciar(semente)
            self.assertEqual(percurso(ambiente), primeira)

    def test_resultado_das_91_geracoes_e_guardado_antes_de_reiniciar_busca(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            caminho = Path(pasta) / "campeao.json"
            with patch("campeao.VERSAO_EXPERIMENTO", 10):
                salvar_campeao(caminho, politica_conhecida(), 90.47, None, 123, 91)
            original = caminho.read_bytes()
            treino = TreinoGeracoes(caminho)
            self.assertEqual(treino.geracao, 1)
            self.assertIsNone(treino.melhores_parametros)
            self.assertEqual(caminho.read_bytes(), original)
            treino.salvar_melhor(forcar=True)
            self.assertEqual(VERSAO_EXPERIMENTO, 12)
            historico = json.loads(caminho.with_name("historico_experimentos.json").read_text())
            self.assertEqual((historico[0]["experimento"]["versao"], historico[0]["tempo_segundos"],
                              historico[0]["geracao_final"]), (10, 90.47, 91))
