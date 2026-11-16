"""Verificações da política de três entradas e do ciclo de treino/avaliação."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame
import main

from ambiente import Ambiente
from avaliacao import Avaliacao
from campeao import carregar_campeao, salvar_campeao
from config import ALTURA, LARGURA, LIMITE_TENTATIVA, SEMENTE_TREINO
from politica import decidir_salto, limiar_salto
from treino import Treino
from geracoes import TreinoGeracoes


class TestPolitica(unittest.TestCase):
    def test_largura_maior_pode_adiar_salto_sem_mudar_distancia_ou_altura(self):
        parametros = (-1, 0, -1, 0.3)
        self.assertTrue(decidir_salto(200, 50, 40, parametros))
        self.assertFalse(decidir_salto(200, 50, 80, parametros))
        self.assertTrue(decidir_salto(180, 50, 80, parametros))
        self.assertLess(limiar_salto(50, 80, parametros), limiar_salto(50, 40, parametros))

    def test_altura_pode_mudar_a_decisao_na_mesma_distancia(self):
        parametros = (-1.0, 2.0, 0.0, 0.0)
        self.assertFalse(decidir_salto(LARGURA / 4, ALTURA / 16, 30, parametros))
        self.assertTrue(decidir_salto(LARGURA / 4, ALTURA / 4, 30, parametros))

    def test_limiar_acompanha_altura_e_sentido_do_peso(self):
        for peso in (-2.0, 2.0):
            parametros = (peso, 1.0, 0.0, -0.5 if peso > 0 else 0.5)
            for altura in (30, 50, 70):
                limiar = limiar_salto(altura, 30, parametros)
                self.assertEqual(decidir_salto(limiar - 1, altura, 30, parametros), peso < 0)
                self.assertEqual(decidir_salto(limiar + 1, altura, 30, parametros), peso > 0)

    def test_degrau_nao_dispara_no_zero(self):
        self.assertFalse(decidir_salto(LARGURA / 2, ALTURA / 2, 30, (-1, 1, 0, 0)))

    def test_peso_distancia_zero_ainda_considera_altura(self):
        parametros = (0, 1, 0, -0.125)
        self.assertIsNone(limiar_salto(70, 30, parametros))
        self.assertFalse(decidir_salto(100, 30, 30, parametros))
        self.assertTrue(decidir_salto(100, 70, 30, parametros))


class TestCiclo(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.caminho = Path(self.temporario.name) / "campeao.json"

    def test_salva_e_carrega_quatro_parametros(self):
        parametros = (-1.2, 0.7, 0.2, 0.4)
        salvar_campeao(self.caminho, parametros, 12.5, LIMITE_TENTATIVA, SEMENTE_TREINO)
        self.assertEqual(
            carregar_campeao(self.caminho, LIMITE_TENTATIVA, SEMENTE_TREINO),
            (parametros, 12.5),
        )
        dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        del dados["peso_altura"]
        self.caminho.write_text(json.dumps(dados), encoding="utf-8")
        with self.assertRaises(ValueError):
            carregar_campeao(self.caminho, LIMITE_TENTATIVA, SEMENTE_TREINO)

    def test_rejeita_peso_largura_ausente_ou_invalido(self):
        for valor in (None, "0.2", float("nan"), float("inf")):
            with self.subTest(valor=valor):
                salvar_campeao(self.caminho, (-1, 0.7, 0.2, 0.4), 12.5, None, SEMENTE_TREINO)
                dados = json.loads(self.caminho.read_text(encoding="utf-8"))
                if valor is None:
                    del dados["peso_largura"]
                else:
                    dados["peso_largura"] = valor
                self.caminho.write_text(json.dumps(dados), encoding="utf-8")
                with self.assertRaises(ValueError):
                    carregar_campeao(self.caminho, None, SEMENTE_TREINO)

    def test_mutacao_inclui_peso_da_largura(self):
        with contextlib.redirect_stdout(io.StringIO()):
            treino = Treino(self.caminho)
        treino.melhores_parametros = (1, 2, 3, 4)
        with patch.object(treino.sorteio, "random", return_value=0.5), \
                patch.object(treino.sorteio, "gauss", side_effect=(0.1, 0.2, 0.3, 0.4)):
            self.assertEqual(treino._proxima_candidata(), (1.1, 2.2, 3.3, 4.4))

    def test_so_termina_na_colisao_e_salva_tempo_acima_de_30(self):
        with contextlib.redirect_stdout(io.StringIO()):
            treino = Treino(self.caminho)
            parametros = treino.parametros
            salvar_campeao(self.caminho, parametros, 120.5, None, SEMENTE_TREINO)
            avaliacao = Avaliacao(self.caminho)
            self.assertEqual(avaliacao.recorde_treino, 120.5)
            ambiente = SimpleNamespace(fim_de_jogo=False, tempo_vivo=120.5,
                                       tentativa_manual=False)
            for tempo in (30.0, 30.1, 120.5, 10000.0):
                ambiente.tempo_vivo = tempo
                self.assertFalse(treino.terminou(ambiente))
                self.assertFalse(avaliacao.terminou(ambiente))
            ambiente.tempo_vivo = 120.5
            ambiente.fim_de_jogo = True
            self.assertTrue(treino.terminou(ambiente))
            self.assertTrue(avaliacao.terminou(ambiente))
            treino.concluir_tentativa(ambiente)
            avaliacao.concluir_tentativa(ambiente)
            self.assertEqual(treino.melhor_tempo, 120.5)
            self.assertEqual(
                carregar_campeao(self.caminho, None, SEMENTE_TREINO),
                (parametros, 120.5),
            )
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            self.assertIsNone(dados["experimento"]["limite_segundos"])

    def test_preserva_campea_do_antigo_limite_de_30_segundos(self):
        parametros = (-1.5, 0.1, 0.2, 0.5)
        salvar_campeao(self.caminho, parametros, 30.0, 30.0, SEMENTE_TREINO)
        original = self.caminho.read_bytes()
        self.assertEqual(
            carregar_campeao(self.caminho, None, SEMENTE_TREINO),
            (parametros, 30.0),
        )
        self.assertEqual(self.caminho.read_bytes(), original)
        with self.assertRaises(ValueError):
            carregar_campeao(self.caminho, None, SEMENTE_TREINO + 1)

    def test_salva_progresso_sem_mudar_candidata_e_ignora_intervencao(self):
        with contextlib.redirect_stdout(io.StringIO()):
            treino = Treino(self.caminho)
            parametros = treino.parametros
            ambiente = SimpleNamespace(tempo_vivo=65.0, tentativa_manual=False)
            self.assertTrue(treino.registrar_progresso(ambiente))
            self.assertEqual(treino.parametros, parametros)
            self.assertEqual(treino.tentativa, 1)
            self.assertEqual(carregar_campeao(self.caminho, None, SEMENTE_TREINO),
                             (parametros, 65.0))
            ambiente.tempo_vivo = 65.5
            self.assertFalse(treino.registrar_progresso(ambiente))
            self.assertTrue(treino.registrar_progresso(ambiente, forcar=True))
            original = self.caminho.read_bytes()
            ambiente.tempo_vivo = 100
            ambiente.tentativa_manual = True
            self.assertFalse(treino.registrar_progresso(ambiente, forcar=True))
            ambiente.tentativa_manual = False
            ambiente.tempo_vivo = 10
            self.assertFalse(treino.registrar_progresso(ambiente, forcar=True))
            self.assertEqual(self.caminho.read_bytes(), original)

    def test_fechar_janela_salva_candidata_viva_e_reabertura_carrega(self):
        with contextlib.redirect_stdout(io.StringIO()):
            treino = TreinoGeracoes(self.caminho)
            parametros = treino.parametros
            # Fecha antes do primeiro salvamento periódico (menos de 1 s).
            eventos = [[] for _ in range(30)] + [[pygame.event.Event(pygame.QUIT)]]
            with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}), \
                    patch("main.TreinoGeracoes", return_value=treino), \
                    patch("main.pygame.time.Clock"), \
                    patch("main.pygame.event.get", side_effect=eventos), \
                    patch("main.desenhar_populacao"):
                main.main("treino")
            self.assertEqual(treino.geracao, 1)
            reaberto = Treino(self.caminho)
            self.assertEqual(reaberto.parametros, parametros)
            self.assertAlmostEqual(reaberto.melhor_tempo, 0.5)

    def test_rejeita_tempo_negativo_sem_teto(self):
        salvar_campeao(self.caminho, (-1.5, 0.1, 0.2, 0.5), -1, None, SEMENTE_TREINO)
        with self.assertRaises(ValueError):
            carregar_campeao(self.caminho, None, SEMENTE_TREINO)

    def test_rejeita_modelo_antigo(self):
        dados = {
            "experimento": {"versao": 4, "limite_segundos": LIMITE_TENTATIVA,
                            "semente_treino": SEMENTE_TREINO},
            "peso": -1.5, "vies": 0.5, "tempo_segundos": 30,
        }
        self.caminho.write_text(json.dumps(dados), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outro experimento"):
            carregar_campeao(self.caminho, LIMITE_TENTATIVA, SEMENTE_TREINO)

    def test_treino_salva_e_avaliacao_repete_sem_alterar_campea(self):
        with contextlib.redirect_stdout(io.StringIO()):
            treino = Treino(self.caminho)
            self.assertEqual(len(treino.parametros), 4)
            ambiente = Ambiente(SEMENTE_TREINO)
            while not treino.terminou(ambiente):
                ambiente.avancar(decidir_salto(
                    ambiente.distancia, ambiente.obstaculo.height, ambiente.obstaculo.width, treino.parametros,
                ))
            parametros_testados = treino.parametros
            treino.concluir_tentativa(ambiente)
            self.assertEqual(len(treino.parametros), 4)
            original = self.caminho.read_bytes()
            resultados = []
            for _ in range(2):
                avaliacao = Avaliacao(self.caminho, semente=456)
                self.assertEqual(avaliacao.parametros, parametros_testados)
                ambiente = Ambiente(avaliacao.semente)
                while not avaliacao.terminou(ambiente):
                    ambiente.avancar(decidir_salto(
                        ambiente.distancia, ambiente.obstaculo.height, ambiente.obstaculo.width, avaliacao.parametros,
                    ))
                avaliacao.concluir_tentativa(ambiente)
                resultados.append((ambiente.tempo_vivo, ambiente.fim_de_jogo))
                self.assertEqual(avaliacao.parametros, parametros_testados)
            self.assertEqual(resultados[0], resultados[1])
            self.assertEqual(self.caminho.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
