"""Sorteio, repetição e troca de sequências sem alterar a campeã."""

from tests.apoio import rede_simples

import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

import main
from ambiente import Ambiente
from avaliacao import Avaliacao
from campeao import salvar_campeao
from config import SEMENTE_TREINO
from tests.apoio import RelogioTeste


class TestAvaliacao(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "campeao.json"
        self.parametros = rede_simples((-1.5, 0.7, 0.2, 0.0, 0.5))
        salvar_campeao(self.caminho, self.parametros, 120, None, SEMENTE_TREINO)

    def test_sorteio_exclui_treino_e_semente_anterior(self):
        original = self.caminho.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), \
                patch("avaliacao.randbelow", side_effect=[SEMENTE_TREINO, 456, 456, SEMENTE_TREINO, 789]):
            sessao = Avaliacao(self.caminho)
            self.assertEqual(sessao.semente, 456)
            sessao.concluida = True
            self.assertEqual(sessao.sortear_semente(), 789)
        self.assertFalse(sessao.concluida)
        self.assertEqual(sessao.parametros, self.parametros)
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_r_repete_n_troca_e_cli_preserva_semente_explicita(self):
        original = self.caminho.read_bytes()
        eventos = [[], [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)],
                   [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n)],
                   [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)],
                   [pygame.event.Event(pygame.QUIT)]]
        sementes = []
        reiniciar = Ambiente.reiniciar

        def observar(ambiente, semente):
            sementes.append(semente)
            reiniciar(ambiente, semente)

        with contextlib.redirect_stdout(io.StringIO()), \
                patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}), \
                patch("main.Avaliacao", side_effect=lambda **opcoes: Avaliacao(self.caminho, **opcoes)), \
                patch("avaliacao.randbelow", return_value=789), \
                patch.object(Ambiente, "reiniciar", observar), \
                patch("main.RelogioQuadros", RelogioTeste), \
                patch("main.pygame.event.get", side_effect=eventos), \
                patch("main.desenhar"):
            main.main("avaliacao", semente=456)
        self.assertEqual(sementes, [456, 456, 789, 789])
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_entrada_pelo_menu_sorteia_semente(self):
        sementes = []

        def criar(**opcoes):
            self.assertIsNone(opcoes["semente"])
            sessao = Avaliacao(self.caminho, **opcoes)
            sementes.append(sessao.semente)
            return sessao

        with contextlib.redirect_stdout(io.StringIO()), \
                patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}), \
                patch("main.escolher_modo", return_value="avaliacao"), \
                patch("main.Avaliacao", side_effect=criar), \
                patch("avaliacao.randbelow", return_value=789), \
                patch("main.RelogioQuadros", RelogioTeste), \
                patch("main.pygame.event.get", return_value=[pygame.event.Event(pygame.QUIT)]):
            main.main()
        self.assertEqual(sementes, [789])
