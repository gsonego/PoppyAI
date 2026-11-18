"""Animação visual determinística e transições entre corrida, salto e colisão."""

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente
from art.animacao_poppy import quadro_corrida
from config import ACELERACAO_OBSTACULO, PASSO, VELOCIDADE_OBSTACULO
from interface import RecursosInterface, desenhar


class TestAnimacao(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        pygame.init()
        self.addCleanup(pygame.quit)
        self.tela = pygame.display.set_mode((900, 400))
        self.recursos = RecursosInterface()

    def test_quatro_poses_distintas_com_mesmo_tamanho_e_alpha(self):
        quadros = [self.recursos.sprite_corrida(76, indice) for indice in range(4)]
        self.assertEqual(len({quadro.get_size() for quadro in quadros}), 1)
        self.assertEqual(len({pygame.image.tostring(quadro, "RGBA") for quadro in quadros}), 4)
        for quadro in quadros:
            self.assertEqual(quadro.get_at((0, 0)).a, 0)
        self.assertIs(self.recursos.sprite_corrida(76, 0), quadros[0])

    def test_ciclo_depende_da_distancia_e_se_repete(self):
        self.assertEqual([quadro_corrida(d) for d in (0, 31, 32, 64, 96, 128)], [0, 0, 1, 2, 3, 0])
        for distancia in (10.5, 40.5, 200):
            self.assertEqual(quadro_corrida(distancia), quadro_corrida(distancia + 128))

    def test_chao_desliza_para_esquerda_e_repete_sem_emenda(self):
        self.recursos.desenhar_fundo(self.tela, 0)
        inicial = self.tela.copy()
        self.recursos.desenhar_fundo(self.tela, 12)
        self.assertEqual(inicial.get_at((26, 345)), self.tela.get_at((14, 345)))
        self.assertNotEqual(inicial.get_at((26, 345)), self.tela.get_at((26, 345)))
        solo = pygame.image.tostring(self.tela.subsurface((0, 330, 900, 38)), "RGB")
        self.recursos.desenhar_fundo(self.tela, 12 + 144)
        self.assertEqual(solo, pygame.image.tostring(self.tela.subsurface((0, 330, 900, 38)), "RGB"))

    def test_nuvens_e_colinas_movem_em_velocidades_diferentes(self):
        self.recursos.desenhar_fundo(self.tela, 0)
        inicial = self.tela.copy()
        self.recursos.desenhar_fundo(self.tela, 100)
        for y, cor, deslocamento in ((106, "#FFF3D9", 8), (245, "#92C8A0", 18), (295, "#7CB66E", 38)):
            with self.subTest(camada=cor):
                cor = pygame.Color(cor)
                for x in range(800):
                    self.assertEqual(inicial.get_at((x + deslocamento, y)) == cor,
                                     self.tela.get_at((x, y)) == cor)

    def test_paisagem_repete_sem_vazios_e_reinicio_recupera_cena_inicial(self):
        self.recursos.desenhar_fundo(self.tela, 0)
        inicial = pygame.image.tostring(self.tela, "RGB")
        self.recursos.desenhar_fundo(self.tela, 90000)
        self.assertEqual(inicial, pygame.image.tostring(self.tela, "RGB"))
        self.recursos.desenhar_fundo(self.tela, 1800 / 0.38)
        self.recursos.desenhar_fundo(self.tela, 0)
        self.assertEqual(inicial, pygame.image.tostring(self.tela, "RGB"))

    def test_distancia_acompanha_mundo_para_na_morte_e_zera_ao_reiniciar(self):
        ambiente = Ambiente(123)
        for _ in range(10):
            ambiente.avancar(False)
        esperado = 10 * VELOCIDADE_OBSTACULO * PASSO + ACELERACAO_OBSTACULO * PASSO ** 2 * sum(range(10))
        self.assertAlmostEqual(ambiente.distancia_percorrida, esperado)
        anterior = ambiente.distancia_percorrida
        ambiente.fim_de_jogo = True
        ambiente.avancar(False)
        self.assertEqual(ambiente.distancia_percorrida, anterior)
        ambiente.reiniciar(123)
        self.assertEqual(ambiente.distancia_percorrida, 0)

    def test_salto_mantem_pose_e_colisao_interrompe_corrida(self):
        ambiente = Ambiente(123)
        ambiente.no_chao = False
        sessao = SimpleNamespace(melhor_tempo=0)
        with patch.object(self.recursos, "sprite_corrida", wraps=self.recursos.sprite_corrida) as corrida, \
                patch.object(self.recursos, "sprite", wraps=self.recursos.sprite) as parada:
            for distancia in (0, 64, 96):
                ambiente.distancia_percorrida = distancia
                desenhar(self.tela, self.recursos, ambiente, sessao, "humano")
                corrida.assert_called_with(76, 1)
            corrida.reset_mock()
            ambiente.fim_de_jogo = True
            desenhar(self.tela, self.recursos, ambiente, sessao, "humano")
            corrida.assert_not_called()
            parada.assert_called_with(76, atingida=True)


if __name__ == "__main__":
    unittest.main()
