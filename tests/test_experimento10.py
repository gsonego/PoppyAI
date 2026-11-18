"""Treino, avaliação, mistura idêntica e transição segura do experimento 9."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ambiente import Ambiente
from avaliacao import Avaliacao
from campeao import salvar_campeao, VERSAO_EXPERIMENTO
from config import SEMENTE_TREINO
from geracoes import TreinoGeracoes
from politica import aplicar_politica, QUANTIDADE_PARAMETROS
from tests.test_rede import politica_conhecida


class TestExperimento10(unittest.TestCase):
    def test_cinquenta_poppys_enfrentam_mesma_pista_do_humano(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            treino = TreinoGeracoes(Path(pasta) / "campeao.json")
            humano = Ambiente(SEMENTE_TREINO, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
            humano.personagem.x = -10000
            for poppy in treino.individuos:
                poppy.ambiente.personagem.x = -10000
                self.assertTrue(poppy.ambiente.incluir_pedras)
            viu_sequencia = False
            for quadro in range(600):
                treino.avancar()
                humano.avancar(False)
                if quadro % 60 == 0:
                    referencia = [(g.tipo, tuple(g.retangulo), g.intervalo_anterior) for g in humano.grupos]
                    for poppy in treino.individuos:
                        self.assertEqual([(g.tipo, tuple(g.retangulo), g.intervalo_anterior)
                                          for g in poppy.ambiente.grupos], referencia)
                    viu_sequencia |= any(a.tipo == "pedra" and b.tipo == "passarinho"
                                         for a, b in zip(humano.grupos, humano.grupos[1:]))
            self.assertEqual(len(treino.vivos), 50)
            self.assertTrue(viu_sequencia)

    def test_agachar_sempre_falha_e_correr_passa_na_sequencia(self):
        for agachar in (False, True):
            ambiente = Ambiente(123, incluir_pedras=True, incluir_passarinhos=True, incluir_tuneis=True)
            pedra = ambiente._sortear_obstaculo(225)
            ambiente.grupos = [pedra]
            ambiente._alvo = pedra
            pesos = [0] * QUANTIDADE_PARAMETROS
            pesos[-1] = int(agachar)
            for _ in range(60):
                aplicar_politica(ambiente, pesos)
            self.assertEqual(ambiente.fim_de_jogo, agachar)

    def test_experimento_nove_arquivado_e_avaliacao_preserva_pesos(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            caminho = Path(pasta) / "campeao.json"
            with patch("campeao.VERSAO_EXPERIMENTO", 9):
                salvar_campeao(caminho, politica_conhecida(), 90, None, 123, 42)
            original = caminho.read_bytes()
            with self.assertRaises(SystemExit):
                Avaliacao(caminho, semente=456)
            self.assertEqual(caminho.read_bytes(), original)
            treino = TreinoGeracoes(caminho)
            self.assertEqual(treino.geracao, 1)
            self.assertIsNone(treino.melhores_parametros)
            self.assertNotEqual(treino.parametros, politica_conhecida())
            treino.salvar_melhor(forcar=True)
            dados = json.loads(caminho.read_text())
            self.assertEqual(dados["experimento"]["versao"], 12)
            self.assertEqual(VERSAO_EXPERIMENTO, 12)
            historico = json.loads(caminho.with_name("historico_experimentos.json").read_text())
            self.assertEqual((historico[0]["experimento"]["versao"], historico[0]["tempo_segundos"],
                              historico[0]["geracao_final"]), (9, 90, 42))
            avaliacao = Avaliacao(caminho, semente=456)
            pesos = avaliacao.parametros
            original = caminho.read_bytes()
            ambiente = Ambiente(avaliacao.semente, incluir_pedras=True, incluir_passarinhos=True, incluir_tuneis=True)
            for _ in range(300):
                aplicar_politica(ambiente, avaliacao.parametros)
                if ambiente.fim_de_jogo:
                    break
            self.assertEqual(avaliacao.parametros, pesos)
            self.assertEqual(caminho.read_bytes(), original)
