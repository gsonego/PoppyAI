"""Postura, colisão e controles da Poppy abaixada no modo humano."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente
from apresentacao import VistaAmbiente
from config import CHAO_Y, POPPY_ALTURA, POPPY_ALTURA_ABAIXADA
from humano import JogoHumano
from interface import RecursosInterface, desenhar_poppy
import main
from tests.apoio import RelogioTeste


class TestAbaixar(unittest.TestCase):
    def test_postura_mantem_chao_largura_e_frente_do_sensor(self):
        ambiente = Ambiente(123)
        frente, largura = ambiente.personagem.right, ambiente.personagem.width
        ambiente.definir_abaixada(True)
        for _ in range(5):
            ambiente.avancar(False)
        self.assertTrue(ambiente.abaixada)
        self.assertEqual(ambiente.personagem.height, POPPY_ALTURA_ABAIXADA)
        self.assertEqual(ambiente.personagem.bottom, CHAO_Y)
        self.assertEqual((ambiente.personagem.right, ambiente.personagem.width), (frente, largura))
        self.assertEqual(VistaAmbiente(ambiente, 0.5).personagem.bottom, CHAO_Y)
        ambiente.definir_abaixada(False)
        self.assertEqual(ambiente.personagem.height, POPPY_ALTURA)
        self.assertEqual(VistaAmbiente(ambiente, 0).personagem.bottom, CHAO_Y)

    def test_abaixada_nao_salta_e_no_ar_so_abaixa_ao_pousar(self):
        ambiente = Ambiente(123)
        ambiente.definir_abaixada(True)
        ambiente.pular_manualmente()
        ambiente.avancar(True)
        self.assertTrue(ambiente.no_chao)
        ambiente.definir_abaixada(False)
        ambiente.pular_manualmente()
        ambiente.avancar(False)
        altura_no_ar = ambiente.posicao_y
        ambiente.definir_abaixada(True)
        self.assertFalse(ambiente.abaixada)
        self.assertEqual(ambiente.posicao_y, altura_no_ar)
        for _ in range(60):
            ambiente.avancar(False)
            if ambiente.no_chao:
                break
        self.assertTrue(ambiente.abaixada)
        self.assertEqual(ambiente.personagem.bottom, CHAO_Y)

    def test_colisao_respeita_altura_menor_e_caixa_no_chao_continua_perigosa(self):
        for abaixar, suspenso, colisao in ((False, True, True), (True, True, False), (True, False, True)):
            with self.subTest(abaixar=abaixar, suspenso=suspenso):
                ambiente = Ambiente(123)
                ambiente.definir_abaixada(abaixar)
                ambiente.obstaculo.update(110, CHAO_Y - (52 if suspenso else 20), 40, 12 if suspenso else 20)
                ambiente.obstaculo_x = 110
                ambiente.avancar(False)
                self.assertEqual(ambiente.fim_de_jogo, colisao)

    def test_reinicio_restaura_postura_e_colisao_congela_pose(self):
        ambiente = Ambiente(123)
        ambiente.definir_abaixada(True)
        ambiente.fim_de_jogo = True
        ambiente.definir_abaixada(False)
        self.assertTrue(ambiente.abaixada)
        ambiente.reiniciar(123)
        self.assertFalse(ambiente.abaixada)
        self.assertFalse(ambiente.pedido_abaixar)
        self.assertEqual(ambiente.personagem.height, POPPY_ALTURA)

    def test_controles_soltar_e_perder_foco_levantam_poppy(self):
        with tempfile.TemporaryDirectory() as pasta, \
                patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            eventos = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)],
                       [pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN)],
                       [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)],
                       [pygame.event.Event(pygame.WINDOWFOCUSLOST)],
                       [pygame.event.Event(pygame.QUIT)]]
            estados = []
            with patch("main.JogoHumano", return_value=JogoHumano(Path(pasta) / "recorde.json")), \
                    patch("main.RelogioQuadros", RelogioTeste), \
                    patch("main.pygame.event.get", side_effect=eventos), \
                    patch("main.desenhar", side_effect=lambda tela, recursos, ambiente, *args:
                          estados.append(ambiente.abaixada)):
                main.main("humano")
            self.assertEqual(estados, [True, False, True, False])

    def test_sprite_abaixado_e_vermelho_sao_distintos_e_carregados_uma_vez(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            pygame.init()
            try:
                tela = pygame.display.set_mode((900, 400))
                recursos = RecursosInterface()
                normal = recursos.sprite_abaixada()
                atingida = recursos.sprite_abaixada(True)
                self.assertEqual(normal.get_height(), 38)
                self.assertIs(normal, recursos.sprite_abaixada())
                self.assertNotEqual(pygame.image.tobytes(normal, "RGBA"), pygame.image.tobytes(atingida, "RGBA"))
                ambiente = Ambiente(123)
                ambiente.definir_abaixada(True)
                ambiente.fim_de_jogo = True
                with patch.object(recursos, "sprite_abaixada", wraps=recursos.sprite_abaixada) as sprite:
                    desenhar_poppy(tela, recursos, ambiente)
                sprite.assert_called_once_with(atingida=True, indice=0)
                quadros = [recursos.sprite_abaixada(indice=i) for i in range(4)]
                self.assertEqual(len({q.get_size() for q in quadros}), 1)
                self.assertEqual(len({pygame.image.tobytes(q, "RGBA") for q in quadros}), 4)
                ambiente.fim_de_jogo = False
                with patch.object(recursos, "sprite_abaixada", wraps=recursos.sprite_abaixada) as sprite:
                    for indice, distancia in enumerate((0, 32, 64, 96, 128)):
                        ambiente.distancia_percorrida = distancia
                        desenhar_poppy(tela, recursos, ambiente)
                        sprite.assert_called_with(atingida=False, indice=indice % 4)
                ambiente.fim_de_jogo = True
                distancia = ambiente.distancia_percorrida
                ambiente.avancar(False)
                self.assertEqual(ambiente.distancia_percorrida, distancia)
            finally:
                pygame.quit()
