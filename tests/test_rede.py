"""Cinco medidas, camada oculta e comandos independentes no experimento 8."""

import contextlib
import io
import json
from math import tanh
from pathlib import Path
import tempfile
import unittest

from ambiente import Ambiente
from campeao import carregar_campeao, salvar_campeao, VERSAO_EXPERIMENTO
from config import SEMENTE_TREINO
from geracoes import TreinoGeracoes
from politica import aplicar_politica, calcular_saidas, decidir_acoes, observar, QUANTIDADE_PARAMETROS


def politica_conhecida():
    # Fixture construída para testar capacidade e integração. Não entra no treino.
    ocultos = (-10, 0, 0, 13/9, -20, 0)  # Saltar perto das caixas, compensando velocidade.
    ocultos += (0, 0, 0, 0, 30, -1.5)   # Faixa inferior para abaixar.
    ocultos += (0, 0, 0, 0, 30, -4.5)   # Faixa superior: evita abaixar para pássaros.
    ocultos += (0, 40, 0, 0, 0, -2)   # Distingue pedras baixas de caixas.
    return ocultos + (1, 0, 0, 1, -1) + (0, 1, -1, 0, -1)


class TestRede(unittest.TestCase):
    def test_conta_tanh_e_duas_saidas(self):
        parametros = [0.0] * QUANTIDADE_PARAMETROS
        parametros[0] = 2
        parametros[5] = -0.5
        parametros[24] = 3
        parametros[28] = 0.25
        parametros[29] = -4
        parametros[33] = -0.1
        salto, baixo = calcular_saidas((0.5, 0, 0, 0, 0), parametros)
        self.assertAlmostEqual(salto, 3 * tanh(0.5) + 0.25)
        self.assertAlmostEqual(baixo, -4 * tanh(0.5) - 0.1)

    def test_degrau_no_zero_e_prioridade_abaixar(self):
        ambiente = Ambiente(123)
        parametros = [0] * QUANTIDADE_PARAMETROS
        self.assertEqual(decidir_acoes(ambiente, parametros), (False, False))
        parametros[28] = 1
        self.assertEqual(decidir_acoes(ambiente, parametros), (True, False))
        parametros[33] = 1
        self.assertEqual(decidir_acoes(ambiente, parametros), (False, True))

    def test_observacao_normalizada_sem_tipo_de_obstaculo(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        self.assertEqual(observar(ambiente), (751/900, 50/400, 30/900, 350/650, 0))
        ambiente._alvo = ambiente._sortear_obstaculo(900)
        self.assertEqual(observar(ambiente)[4], 42/400)
        ambiente._alvo = ambiente._sortear_obstaculo(900)
        self.assertEqual(observar(ambiente)[4], 92/400)

    def test_rede_pode_distinguir_saltar_abaixar_e_correr(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        ambiente.obstaculo_x = ambiente.personagem.right + 30
        ambiente.obstaculo.x = round(ambiente.obstaculo_x)
        pesos = politica_conhecida()
        self.assertEqual(decidir_acoes(ambiente, pesos), (True, False))
        tunel = ambiente._sortear_obstaculo(180)
        passarinho = ambiente._sortear_obstaculo(180)
        ambiente._alvo = tunel
        ambiente.grupos = [tunel]
        self.assertEqual(decidir_acoes(ambiente, pesos), (False, True))
        aplicar_politica(ambiente, pesos)
        self.assertTrue(ambiente.abaixada)
        ambiente._alvo = passarinho
        ambiente.grupos = [passarinho]
        self.assertEqual(decidir_acoes(ambiente, pesos), (False, False))
        aplicar_politica(ambiente, pesos)
        self.assertFalse(ambiente.abaixada)

    def test_politica_conhecida_sobrevive_a_mistura_em_velocidades_distintas(self):
        for tempo in (0, 120):
            ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
            ambiente.tempo_vivo = tempo
            for _ in range(2400):
                aplicar_politica(ambiente, politica_conhecida())
                self.assertFalse(ambiente.fim_de_jogo)

    def test_populacao_tem_34_parametros_e_mesmo_desafio_do_humano(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            treino = TreinoGeracoes(Path(pasta) / "campeao.json")
            humano = Ambiente(SEMENTE_TREINO, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
            referencia = [(g.tipo, tuple(g.retangulo))
                          for g in (humano._sortear_obstaculo(900) for _ in range(20))]
            for poppy in treino.individuos:
                self.assertEqual(len(poppy.parametros), 34)
                sequencia = [(g.tipo, tuple(g.retangulo))
                             for g in (poppy.ambiente._sortear_obstaculo(900) for _ in range(20))]
                self.assertEqual(sequencia, referencia)
            treino.proxima_geracao()
            self.assertTrue(all(len(p.parametros) == 34 for p in treino.individuos))

    def test_salvamento_rejeita_parametros_ausentes_invalidos_e_modelo_incorreto(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "campeao.json"
            for indice in range(34):
                salvar_campeao(caminho, politica_conhecida(), 12, None, 123)
                dados = json.loads(caminho.read_text())
                dados["parametros"][indice] = True
                caminho.write_text(json.dumps(dados))
                with self.assertRaises(ValueError):
                    carregar_campeao(caminho, None, 123)
            with self.assertRaises(ValueError):
                salvar_campeao(caminho, (0,) * 33, 12, None, 123)
            salvar_campeao(caminho, politica_conhecida(), 12, None, 123)
            dados = json.loads(caminho.read_text())
            dados["modelo"]["ocultos"] = 3
            caminho.write_text(json.dumps(dados))
            with self.assertRaises(ValueError):
                carregar_campeao(caminho, None, 123)

    def test_experimento_sete_real_e_arquivado_ao_salvar_atual(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            caminho = Path(pasta) / "campeao.json"
            dados = {"experimento": {"versao": 7, "limite_segundos": None, "semente_treino": 123},
                     "peso_distancia": -1, "peso_altura": 1, "peso_largura": 0,
                     "peso_velocidade": 0, "vies": 0.5, "tempo_segundos": 100, "geracao": 70}
            caminho.write_text(json.dumps(dados))
            treino = TreinoGeracoes(caminho)
            self.assertEqual(treino.geracao, 1)
            self.assertIsNone(treino.melhores_parametros)
            treino.salvar_melhor(forcar=True)
            self.assertEqual(VERSAO_EXPERIMENTO, 10)
            self.assertEqual(len(carregar_campeao(caminho, None, 123)[0]), 34)
            historico = json.loads(caminho.with_name("historico_experimentos.json").read_text())
            self.assertEqual((historico[0]["tempo_segundos"], historico[0]["geracao_final"]), (100, 70))
