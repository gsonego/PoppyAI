"""Altura, mistura, repetição, desenho e colisão do bumerangue humano."""

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente
from apresentacao import VistaAmbiente
from art.bumerangue import criar_quadros, quadro_bumerangue
from config import BUMERANGUE_CENTRO_Y, INTERVALO_MINIMO_PX
from interface import RecursosInterface, desenhar


class TestBumerangue(unittest.TestCase):
    @staticmethod
    def criar_perto(abaixada=False):
        ambiente = Ambiente(123, incluir_bumerangues=True)
        bumerangue = ambiente._sortear_obstaculo(125)
        ambiente.grupos = [bumerangue]
        ambiente._alvo = bumerangue
        ambiente.definir_abaixada(abaixada)
        return ambiente

    def test_atinge_em_pe_e_passa_abaixada(self):
        for abaixada in (False, True):
            ambiente = self.criar_perto(abaixada)
            ambiente.avancar(False)
            self.assertEqual(ambiente.fim_de_jogo, not abaixada)
            self.assertEqual(ambiente.tipo_obstaculo, "bumerangue")
            self.assertFalse(ambiente.caixas)
            self.assertTrue(ambiente.bumerangues_visiveis)
        ambiente = self.criar_perto(True)
        for _ in range(12):
            ambiente.avancar(False)
        self.assertFalse(ambiente.fim_de_jogo)

    def test_levantar_antes_de_passar_colide(self):
        ambiente = self.criar_perto(True)
        ambiente.avancar(False)
        ambiente.definir_abaixada(False)
        ambiente.avancar(False)
        self.assertTrue(ambiente.fim_de_jogo)

    def test_primeiro_voador_e_mistura_repetem_com_semente(self):
        def sequencia(ambiente):
            return [(g.tipo, tuple(g.retangulo))
                    for g in (ambiente._sortear_obstaculo(900) for _ in range(40))]
        ambiente = Ambiente(123, incluir_bumerangues=True)
        self.assertEqual(ambiente.tipo_obstaculo, "simples")
        primeira = sequencia(ambiente)
        self.assertEqual(primeira[0][0], "bumerangue")
        self.assertIn("simples", [tipo for tipo, _ in primeira])
        self.assertGreater([tipo for tipo, _ in primeira].count("bumerangue"), 1)
        ambiente.reiniciar(123)
        self.assertEqual(sequencia(ambiente), primeira)

    def test_ia_sem_voadores_e_espaco_para_reagir_no_humano(self):
        ambiente = Ambiente(123)
        self.assertNotIn("bumerangue", [ambiente._sortear_obstaculo(900).tipo for _ in range(100)])
        ambiente = Ambiente(123, incluir_bumerangues=True)
        ambiente.grupos[0].retangulo.x -= 1
        ambiente.grupos[0].x -= 1
        ambiente._completar_pista()
        primeiro, segundo = ambiente.grupos[:2]
        self.assertEqual(segundo.tipo, "bumerangue")
        self.assertGreaterEqual(segundo.retangulo.left - primeiro.retangulo.right, INTERVALO_MINIMO_PX)

    def test_interpolacao_move_voador_sem_modificar_colisao(self):
        ambiente = self.criar_perto(True)
        ambiente.avancar(False)
        original = ambiente.obstaculo.copy()
        retangulo = VistaAmbiente(ambiente, 0.5).bumerangues_visiveis[0]
        self.assertGreater(retangulo.x, original.x)
        self.assertEqual(retangulo.centery, BUMERANGUE_CENTRO_Y)
        self.assertEqual(ambiente.obstaculo, original)

    def test_arte_gira_e_congela_com_partida(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            pygame.init()
            try:
                tela = pygame.display.set_mode((900, 400))
                quadros = criar_quadros()
                self.assertEqual(len(quadros), 16)
                self.assertEqual({q.get_size() for q in quadros}, {(32, 32)})
                self.assertGreater(len({pygame.image.tobytes(q, "RGBA") for q in quadros}), 8)
                self.assertEqual(quadro_bumerangue(12), 1)
                self.assertEqual(quadro_bumerangue(192), 0)
                ambiente = self.criar_perto(True)
                recursos = RecursosInterface()
                with patch("interface.apresentar"), patch("interface.desenhar_caixa") as caixa:
                    desenhar(tela, recursos, ambiente, SimpleNamespace(melhor_tempo=0), "humano")
                    caixa.assert_not_called()
                ambiente.fim_de_jogo = True
                anterior = ambiente.distancia_percorrida
                ambiente.avancar(False)
                self.assertEqual(ambiente.distancia_percorrida, anterior)
            finally:
                pygame.quit()
