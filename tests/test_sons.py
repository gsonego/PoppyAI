"""Áudio opcional, controle de silêncio e efeitos disparados por ações reais."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import wave

import pygame

import main
from humano import JogoHumano
from interface import RecursosInterface
from sons import Sons
from tests.apoio import RelogioTeste


class TestSons(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.addCleanup(pygame.quit)
        pygame.display.set_mode((900, 400))

    def test_wavs_validos_carregam_e_reproduzem_no_mixer(self):
        sons = Sons()
        self.assertTrue(sons.disponivel)
        pasta = Path(__file__).resolve().parents[1] / "audio"
        for nome in sons.efeitos:
            with wave.open(str(pasta / f"{nome}.wav")) as arquivo:
                self.assertEqual(arquivo.getnchannels(), 1)
                self.assertEqual(arquivo.getsampwidth(), 2)
                self.assertEqual(arquivo.getframerate(), 44100)
                self.assertGreater(arquivo.getnframes(), 1000)
            self.assertIsNotNone(sons.tocar(nome))

    def test_m_para_sons_em_execucao_e_bloqueia_novos_efeitos(self):
        recursos = RecursosInterface()
        efeitos = {nome: Mock() for nome in recursos.sons.efeitos}
        recursos.sons.efeitos = efeitos
        main.tratar_evento_visual(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m), recursos)
        for efeito in efeitos.values():
            efeito.stop.assert_called_once()
        recursos.sons.tocar("salto")
        recursos.sons.fim_partida(True)
        for efeito in efeitos.values():
            efeito.play.assert_not_called()
        main.tratar_evento_visual(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m), recursos)
        recursos.sons.tocar("salto")
        efeitos["salto"].play.assert_called_once()

    def test_recorde_toca_depois_da_colisao(self):
        sons = Sons()
        canal = Mock()
        sons.efeitos = {"colisao": Mock(), "recorde": Mock()}
        sons.efeitos["colisao"].play.return_value = canal
        sons.fim_partida(True)
        canal.queue.assert_called_once_with(sons.efeitos["recorde"])
        sons.efeitos["recorde"].play.assert_not_called()

    def test_sem_dispositivo_ou_arquivo_nao_interrompe(self):
        with patch("sons.pygame.mixer.get_init", return_value=None):
            sons = Sons()
        self.assertFalse(sons.disponivel)
        sons.tocar("salto")
        sons.fim_partida(True)
        with tempfile.TemporaryDirectory() as pasta:
            self.assertFalse(Sons(Path(pasta)).disponivel)

    def test_menu_toca_ao_navegar_e_confirmar(self):
        recursos = RecursosInterface()
        recursos.sons = Mock()
        eventos = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
                   pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
        with patch("main.pygame.event.get", return_value=eventos):
            modo = main.escolher_modo(pygame.display.get_surface(), recursos, RelogioTeste())
        self.assertEqual(modo, "treino")
        self.assertEqual([c.args[0] for c in recursos.sons.tocar.call_args_list],
                         ["menu_mover", "menu_confirmar"])

    def test_humano_nao_toca_salto_bloqueado_e_colisao_toca_uma_vez(self):
        recursos = RecursosInterface()
        recursos.sons = Mock()
        eventos = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)],
                   [pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN),
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)],
                   [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)]]
        eventos += [[] for _ in range(180)] + [[pygame.event.Event(pygame.QUIT)]]
        with tempfile.TemporaryDirectory() as pasta, \
                patch("main.JogoHumano", return_value=JogoHumano(Path(pasta) / "recorde.json")), \
                patch("main.pygame.event.get", side_effect=eventos), patch("main.desenhar"):
            main.jogar(pygame.display.get_surface(), recursos, RelogioTeste(), "humano", 123)
        self.assertEqual([c.args[0] for c in recursos.sons.tocar.call_args_list], ["salto"])
        recursos.sons.fim_partida.assert_called_once_with(novo_recorde=True)
