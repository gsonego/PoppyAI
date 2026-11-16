"""Seleção, eliminação, persistência e controles do treino visual de 50 Poppys."""

import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

import main
from campeao import carregar_campeao, salvar_campeao
from config import SEMENTE_TREINO
from geracoes import TreinoGeracoes
from interface import RecursosInterface, desenhar_populacao, desenhar_poppy


class TestGeracoes(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "campeao.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.treino = TreinoGeracoes(self.caminho)

    def test_cinquenta_poppys_tem_cores_unicas_e_pesos_independentes(self):
        self.assertEqual(len(self.treino.vivos), 50)
        self.assertEqual(len({p.cor for p in self.treino.individuos}), 50)
        self.assertEqual(len({id(p.ambiente) for p in self.treino.individuos}), 50)
        self.assertEqual(len({p.parametros for p in self.treino.individuos}), 50)

    def test_campea_existente_entra_na_populacao_sem_alterar_arquivo(self):
        parametros = (-1.5, 0.7, -0.4, 0.45)
        salvar_campeao(self.caminho, parametros, 120, None, SEMENTE_TREINO)
        original = self.caminho.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            treino = TreinoGeracoes(self.caminho)
        self.assertEqual(treino.individuos[0].parametros, parametros)
        self.assertEqual(treino.melhor_tempo, 120)
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_sobreviventes_enfrentam_mesmos_obstaculos_e_mortas_param(self):
        morta = self.treino.individuos[0]
        morta.ambiente.fim_de_jogo = True
        for _ in range(160):
            self.treino.avancar()
            vivos = self.treino.vivos
            if vivos:
                referencia = vivos[0].ambiente
                for poppy in vivos[1:]:
                    self.assertEqual(poppy.ambiente.obstaculo, referencia.obstaculo)
                    self.assertEqual(poppy.ambiente.tempo_vivo, referencia.tempo_vivo)
        self.assertEqual(morta.ambiente.tempo_vivo, 0)
        self.assertEqual(morta.ambiente.distancia_percorrida, 0)
        self.assertNotIn(morta, self.treino.vivos)

    def test_proxima_geracao_preserva_cinco_melhores_e_campea(self):
        for indice, poppy in enumerate(self.treino.individuos):
            poppy.ambiente.tempo_vivo = indice + 1.0
            poppy.ambiente.fim_de_jogo = True
        melhores = [p.parametros for p in self.treino.individuos[-5:]]
        cores = [p.cor for p in self.treino.individuos]
        campea = self.treino.individuos[-1].parametros
        with contextlib.redirect_stdout(io.StringIO()):
            self.treino.avancar()
        self.assertEqual(self.treino.geracao, 2)
        self.assertEqual(len(self.treino.individuos), 50)
        self.assertEqual(set(p.parametros for p in self.treino.individuos[:5]), set(melhores))
        self.assertEqual([p.cor for p in self.treino.individuos], cores)
        self.assertEqual(carregar_campeao(self.caminho, None, SEMENTE_TREINO), (campea, 50.0))

    def test_cores_e_poppys_mortas_desaparecem_do_desenho(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            pygame.init()
            try:
                tela = pygame.display.set_mode((900, 400))
                recursos = RecursosInterface()
                self.treino.individuos[0].ambiente.fim_de_jogo = True
                with patch("interface.pygame.draw.line", wraps=pygame.draw.line) as linha, \
                        patch("interface.desenhar_poppy", wraps=desenhar_poppy) as poppy:
                    desenhar_populacao(tela, recursos, self.treino)
                cores = {c.args[1] for c in linha.call_args_list if isinstance(c.args[1], tuple)}
                self.assertEqual(cores, {p.cor for p in self.treino.vivos})
                ambientes = [c.args[2] for c in poppy.call_args_list]
                self.assertEqual(len(ambientes), 49)
                self.assertNotIn(self.treino.individuos[0].ambiente, ambientes)
            finally:
                pygame.quit()

    def test_n_avanca_com_sobreviventes_e_fecha_salvando_campea(self):
        eventos = [[] for _ in range(90)]
        eventos += [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n)], [pygame.event.Event(pygame.QUIT)]]
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}), \
                contextlib.redirect_stdout(io.StringIO()), \
                patch("main.TreinoGeracoes", return_value=self.treino), \
                patch("main.pygame.time.Clock"), \
                patch("main.pygame.event.get", side_effect=eventos), \
                patch("main.desenhar_populacao"):
            main.main("treino")
        self.assertEqual(self.treino.geracao, 2)
        _, tempo = carregar_campeao(self.caminho, None, SEMENTE_TREINO)
        self.assertAlmostEqual(tempo, 1.5)


if __name__ == "__main__":
    unittest.main()
