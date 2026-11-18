"""Resultados preservados antes da troca de experimento, sem duplicação ou perda."""

from tests.apoio import rede_simples

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campeao import GravadorCampeao, VERSAO_EXPERIMENTO, carregar_campeao, salvar_campeao
from config import SEMENTE_TREINO
from geracoes import TreinoGeracoes


class TestHistorico(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "campeao.json"
        self.historico = self.caminho.with_name("historico_experimentos.json")
        self.parametros = rede_simples((-1.5, 0.7, 0.2, 0.0, 0.5))
        salvar_campeao(self.caminho, self.parametros, 120, None, SEMENTE_TREINO, 42)

    def test_mesmo_experimento_nao_gera_historico(self):
        salvar_campeao(self.caminho, self.parametros, 121, None, SEMENTE_TREINO, 43)
        self.assertFalse(self.historico.exists())

    def test_novo_experimento_comeca_na_geracao_um_e_preserva_resumo(self):
        original = self.caminho.read_bytes()
        with patch("campeao.VERSAO_EXPERIMENTO", VERSAO_EXPERIMENTO + 1), \
                contextlib.redirect_stdout(io.StringIO()):
            treino = TreinoGeracoes(self.caminho)
            self.assertEqual(treino.geracao, 1)
            self.assertIsNone(treino.melhores_parametros)
            self.assertEqual(self.caminho.read_bytes(), original)
            self.assertFalse(self.historico.exists())
            treino.salvar_melhor(forcar=True)
            self.assertEqual(carregar_campeao(self.caminho, None, SEMENTE_TREINO)[1], 0)
        dados = json.loads(self.caminho.read_text())
        self.assertEqual(dados["experimento"]["versao"], VERSAO_EXPERIMENTO + 1)
        self.assertEqual(dados["geracao"], 1)
        historico = json.loads(self.historico.read_text())
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["experimento"]["versao"], VERSAO_EXPERIMENTO)
        self.assertEqual(historico[0]["tempo_segundos"], 120)
        self.assertEqual(historico[0]["geracao_final"], 42)
        self.assertIn("encerrado_em", historico[0])
        self.assertFalse(any(chave.startswith("peso") or chave == "vies" for chave in historico[0]))

    def test_resultados_seguem_ordem_dos_experimentos(self):
        for versao, tempo in ((VERSAO_EXPERIMENTO + 1, 20), (VERSAO_EXPERIMENTO + 2, 10)):
            with patch("campeao.VERSAO_EXPERIMENTO", versao):
                salvar_campeao(self.caminho, self.parametros, tempo, None, SEMENTE_TREINO, 3)
        historico = json.loads(self.historico.read_text())
        self.assertEqual([r["experimento"]["versao"] for r in historico],
                         [VERSAO_EXPERIMENTO, VERSAO_EXPERIMENTO + 1])
        self.assertEqual([r["tempo_segundos"] for r in historico], [120, 20])

    def test_falha_do_historico_preserva_campea_anterior(self):
        original = self.caminho.read_bytes()
        with patch("campeao.VERSAO_EXPERIMENTO", VERSAO_EXPERIMENTO + 1), \
                patch("historico.Path.replace", side_effect=PermissionError("disco indisponivel")):
            with self.assertRaises(PermissionError):
                salvar_campeao(self.caminho, self.parametros, 1, None, SEMENTE_TREINO)
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_retry_apos_falha_na_campea_nao_duplica_historico(self):
        substituir = Path.replace

        def falhar_campea(caminho, destino):
            if caminho == self.caminho.with_suffix(".json.tmp"):
                raise PermissionError("campea bloqueada")
            return substituir(caminho, destino)

        with patch("campeao.VERSAO_EXPERIMENTO", VERSAO_EXPERIMENTO + 1):
            with patch.object(Path, "replace", falhar_campea):
                with self.assertRaises(PermissionError):
                    salvar_campeao(self.caminho, self.parametros, 1, None, SEMENTE_TREINO)
            historico = self.historico.read_bytes()
            salvar_campeao(self.caminho, self.parametros, 2, None, SEMENTE_TREINO)
            self.assertEqual(self.historico.read_bytes(), historico)

    def test_geracao_desconhecida_nao_e_inventada(self):
        dados = json.loads(self.caminho.read_text())
        del dados["geracao"]
        self.caminho.write_text(json.dumps(dados))
        with patch("campeao.VERSAO_EXPERIMENTO", VERSAO_EXPERIMENTO + 1):
            salvar_campeao(self.caminho, self.parametros, 1, None, SEMENTE_TREINO)
        self.assertIsNone(json.loads(self.historico.read_text())[0]["geracao_final"])

    def test_gravacao_em_segundo_plano_tambem_preserva_resultado(self):
        with patch("campeao.VERSAO_EXPERIMENTO", VERSAO_EXPERIMENTO + 1):
            gravador = GravadorCampeao()
            gravador.agendar(self.caminho, self.parametros, 2, None, SEMENTE_TREINO, 1)
            gravador.fechar()
        self.assertEqual(json.loads(self.historico.read_text())[0]["geracao_final"], 42)
