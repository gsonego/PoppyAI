"""Fluxos do menu e do modo humano, com arquivos temporários e vídeo sem janela."""

import contextlib
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

import main
from humano import JogoHumano
from interface import RecursosInterface, desenhar_menu, formatar_tempo


def tecla(codigo):
    return pygame.event.Event(pygame.KEYDOWN, key=codigo)


class TestJogo(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "recorde_humano.json"
        ambiente = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        self.addCleanup(pygame.quit)

    def test_recorde_pessoal_persiste_e_nao_regride(self):
        sessao = JogoHumano(self.caminho)
        sessao.salvar_recorde(SimpleNamespace(tempo_vivo=65.5))
        self.assertEqual(JogoHumano(self.caminho).melhor_tempo, 65.5)
        original = self.caminho.read_bytes()
        sessao.salvar_recorde(SimpleNamespace(tempo_vivo=10))
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_humano_salta_morre_reinicia_e_nao_consulta_ia(self):
        sessao = JogoHumano(self.caminho)
        eventos = [[tecla(pygame.K_SPACE)]] + [[] for _ in range(179)]
        eventos += [[tecla(pygame.K_r)], [tecla(pygame.K_SPACE)], [pygame.event.Event(pygame.QUIT)]]
        estados = []
        desenho = main.desenhar

        def observar(tela, recursos, ambiente, atual, modo, detalhes):
            estados.append((ambiente.no_chao, ambiente.fim_de_jogo, ambiente.tempo_vivo))
            desenho(tela, recursos, ambiente, atual, modo, detalhes)

        with patch("main.JogoHumano", return_value=sessao), \
                patch("main.decidir_salto", side_effect=AssertionError("IA chamada no modo humano")), \
                patch("main.Treino", side_effect=AssertionError("Treino criado no modo humano")), \
                patch("main.pygame.time.Clock"), \
                patch("main.pygame.event.get", side_effect=eventos), \
                patch("main.desenhar", side_effect=observar):
            main.main("humano")
        self.assertFalse(estados[0][0])
        self.assertTrue(estados[179][1])
        self.assertFalse(estados[180][1])
        self.assertLess(estados[180][2], 0.1)
        self.assertFalse(estados[181][0])
        self.assertGreater(JogoHumano(self.caminho).melhor_tempo, 2)

    def test_menu_jogar_voltar_e_tratar_ausencia_de_campea(self):
        eventos = [[], [tecla(pygame.K_RETURN)], [], [tecla(pygame.K_ESCAPE)],
                   [tecla(pygame.K_DOWN), tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)],
                   [], [pygame.event.Event(pygame.QUIT)]]
        avisos = []

        def observar(tela, recursos, selecionado, aviso):
            avisos.append(aviso)
            desenhar_menu(tela, recursos, selecionado, aviso)

        with contextlib.redirect_stdout(io.StringIO()), \
                patch("main.JogoHumano", return_value=JogoHumano(self.caminho)), \
                patch("main.Avaliacao", side_effect=SystemExit("Nenhuma campeã salva")), \
                patch("main.pygame.time.Clock"), \
                patch("main.pygame.event.get", side_effect=eventos), \
                patch("main.desenhar_menu", side_effect=observar):
            main.main()
        self.assertTrue(any("CAMPEA INDISPONIVEL" in aviso for aviso in avisos))
        self.assertGreater(JogoHumano(self.caminho).melhor_tempo, 0)

    def test_menu_aceita_clique(self):
        pygame.init()
        tela = pygame.display.set_mode((900, 400))
        evento = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(500, 180), button=1)
        with patch("main.pygame.event.get", return_value=[evento]), patch("main.pygame.time.Clock"):
            self.assertEqual(main.escolher_modo(tela, RecursosInterface(), pygame.time.Clock()), "treino")

    def test_tab_alterna_detalhes_sem_mudar_parametros(self):
        sessao = SimpleNamespace(concluida=False, parametros=(-1.5, 0.7, 0.5), recorde_treino=30,
                                 terminou=lambda ambiente: False)
        eventos = [[tecla(pygame.K_TAB)], [tecla(pygame.K_TAB)], [pygame.event.Event(pygame.QUIT)]]
        detalhes = []
        with patch("main.Avaliacao", return_value=sessao), patch("main.pygame.time.Clock"), \
                patch("main.pygame.event.get", side_effect=eventos), \
                patch("main.desenhar", side_effect=lambda *args: detalhes.append(args[-1])):
            main.main("avaliacao")
        self.assertEqual(detalhes, [True, False])
        self.assertEqual(sessao.parametros, (-1.5, 0.7, 0.5))

    def test_relogio_mostra_horas_sem_voltar_a_zero(self):
        self.assertEqual(formatar_tempo(65), "01:05")
        self.assertEqual(formatar_tempo(3665), "1:01:05")


if __name__ == "__main__":
    unittest.main()
