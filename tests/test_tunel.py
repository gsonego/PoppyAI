"""Três comprimentos, passagem obrigatória por baixo e continuidade do alvo."""

import contextlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente
from apresentacao import VistaAmbiente
from campeao import salvar_campeao, VERSAO_EXPERIMENTO
from config import CHAO_Y, INTERVALO_MINIMO_PX, TUNEL_COMPRIMENTOS, TUNEL_PASSAGEM_ALTURA
from geracoes import TreinoGeracoes
from interface import RecursosInterface, desenhar
from tests.test_rede import politica_conhecida


class TestTunel(unittest.TestCase):
    @staticmethod
    def criar_perto(comprimento, distancia=110, tempo=0):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        with patch.object(ambiente.gerador_obstaculos, "choice", return_value=comprimento):
            grupo = ambiente._sortear_obstaculo(ambiente.personagem.right + distancia)
        ambiente.grupos = [grupo]
        ambiente._alvo = grupo
        ambiente.tempo_vivo = tempo
        return ambiente, grupo

    def test_todos_comprimentos_exigem_abaixar_e_manter_ate_saida(self):
        for comprimento in TUNEL_COMPRIMENTOS:
            for tempo in (0, 120):
                ambiente, grupo = self.criar_perto(comprimento, tempo=tempo)
                ambiente.definir_abaixada(True)
                viu_distancia_negativa = False
                while grupo.retangulo.right > ambiente.personagem.left:
                    ambiente.avancar(False)
                    self.assertFalse(ambiente.fim_de_jogo)
                    if grupo.retangulo.right > ambiente.personagem.left:
                        self.assertIs(ambiente._alvo, grupo)
                        self.assertEqual(ambiente.elevacao_obstaculo, TUNEL_PASSAGEM_ALTURA)
                        viu_distancia_negativa |= ambiente.distancia < 0
                self.assertTrue(viu_distancia_negativa)
                self.assertIsNot(ambiente._alvo, grupo)
                ambiente.definir_abaixada(False)
                ambiente.avancar(False)
                self.assertFalse(ambiente.fim_de_jogo)

    def test_em_pe_ou_levantando_dentro_colide(self):
        for comprimento in TUNEL_COMPRIMENTOS:
            for levantou in (False, True):
                ambiente, _ = self.criar_perto(comprimento, distancia=-30)
                if levantou:
                    ambiente.definir_abaixada(True)
                    ambiente.avancar(False)
                    self.assertFalse(ambiente.fim_de_jogo)
                    ambiente.definir_abaixada(False)
                ambiente.avancar(False)
                self.assertTrue(ambiente.fim_de_jogo)

    def test_salto_nao_burla_tunel_em_nenhuma_altura_da_trajetoria(self):
        for comprimento in TUNEL_COMPRIMENTOS:
            for tempo in (0, 120):
                for distancia in range(0, 501, 10):
                    ambiente, _ = self.criar_perto(comprimento, distancia, tempo)
                    for passo in range(100):
                        ambiente.avancar(passo == 0)
                        if ambiente.fim_de_jogo:
                            break
                    self.assertTrue(ambiente.fim_de_jogo, (comprimento, tempo, distancia))

    def test_comprimentos_sorteados_repetem_e_intervalo_parte_da_saida(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)

        def sequencia():
            return [(g.tipo, tuple(g.retangulo))
                    for g in (ambiente._sortear_obstaculo(900) for _ in range(150))]

        primeira = sequencia()
        self.assertEqual(primeira[0][0], "tunel")
        self.assertEqual({r[2] for tipo, r in primeira if tipo == "tunel"}, set(TUNEL_COMPRIMENTOS))
        self.assertNotIn("bumerangue", [tipo for tipo, _ in primeira])
        ambiente.reiniciar(123)
        self.assertEqual(sequencia(), primeira)
        ambiente, grupo = self.criar_perto(280)
        ambiente._completar_pista()
        proximo = ambiente.grupos[1]
        self.assertGreaterEqual(proximo.retangulo.left - grupo.retangulo.right, INTERVALO_MINIMO_PX)

    def test_interpolacao_move_desenho_sem_alterar_colisao(self):
        ambiente, grupo = self.criar_perto(200)
        ambiente.definir_abaixada(True)
        ambiente.avancar(False)
        original = grupo.retangulo.copy()
        visual = VistaAmbiente(ambiente, 0)
        self.assertGreater(visual.tuneis_visiveis[0].left, grupo.retangulo.left)
        self.assertEqual(visual.tuneis_visiveis[0].bottom, CHAO_Y - TUNEL_PASSAGEM_ALTURA)
        self.assertEqual(grupo.retangulo, original)
        self.assertFalse(ambiente.caixas_visiveis)

    def test_sprites_tres_medidas_carregados_e_desenho_dos_tres_modos(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            pygame.init()
            try:
                tela = pygame.display.set_mode((900, 400))
                recursos = RecursosInterface()
                for comprimento in TUNEL_COMPRIMENTOS:
                    self.assertEqual(recursos.tuneis[comprimento].get_size(), (comprimento, 162))
                    self.assertGreaterEqual(recursos.tuneis[comprimento].get_at((comprimento // 2, 70)).a, 250)
                ambiente, _ = self.criar_perto(200)
                ambiente.definir_abaixada(True)
                sessao = SimpleNamespace(melhor_tempo=0, recorde_treino=0, tentativa=1,
                                         parametros=politica_conhecida(), semente=123)
                with patch("interface.apresentar"), patch("interface.desenhar_caixa") as caixa:
                    for modo in ("humano", "treino", "avaliacao"):
                        desenhar(tela, recursos, ambiente, sessao, modo, detalhes=modo != "humano")
                    caixa.assert_not_called()
            finally:
                pygame.quit()

    def test_experimento_oito_e_arquivado_antes_da_nova_campea(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            caminho = Path(pasta) / "campeao.json"
            with patch("campeao.VERSAO_EXPERIMENTO", 8):
                salvar_campeao(caminho, politica_conhecida(), 50, None, 123, 73)
            treino = TreinoGeracoes(caminho)
            self.assertEqual(treino.geracao, 1)
            self.assertIsNone(treino.melhores_parametros)
            treino.salvar_melhor(forcar=True)
            self.assertEqual(VERSAO_EXPERIMENTO, 12)
            historico = json.loads(caminho.with_name("historico_experimentos.json").read_text())
            self.assertEqual((historico[0]["experimento"]["versao"], historico[0]["tempo_segundos"],
                              historico[0]["geracao_final"]), (8, 50, 73))
