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
from ambiente import Ambiente
from humano import JogoHumano
from interface import RecursosInterface, desenhar, desenhar_menu, formatar_tempo
from janela import apresentar, area_conteudo, criar_janela, posicao_logica, tratar_redimensionamento


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
                patch("main.TreinoGeracoes", side_effect=AssertionError("Treino criado no modo humano")), \
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

    def test_menu_aceita_clique_ampliado_com_faixas(self):
        pygame.init()
        pygame.display.set_mode((1800, 1000), pygame.RESIZABLE)
        tela = pygame.Surface((900, 400))
        recursos = RecursosInterface()
        desenhar_menu(tela, recursos)
        # O conteúdo é ampliado 2×, com 100 pixels de faixa acima e abaixo.
        evento = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1000, 460), button=1)
        with patch("main.pygame.event.get", return_value=[evento]), patch("main.pygame.time.Clock"):
            self.assertEqual(main.escolher_modo(tela, recursos, pygame.time.Clock()), "treino")
        self.assertIsNone(posicao_logica((1000, 50)))

    def test_redimensionar_preserva_proporcao_e_pixels_sem_suavizacao(self):
        pygame.init()
        pygame.display.set_mode((900, 400), pygame.RESIZABLE)
        evento = pygame.event.Event(pygame.VIDEORESIZE, w=1800, h=1000)
        tratar_redimensionamento(evento)
        self.assertEqual(area_conteudo(), pygame.Rect(0, 100, 1800, 800))
        tela = pygame.Surface((900, 400))
        tela.fill("#B7E5F0")
        tela.set_at((500, 180), "#DC7189")
        apresentar(tela)
        janela = pygame.display.get_surface()
        for x, y in ((1000, 460), (1001, 460), (1000, 461), (1001, 461)):
            self.assertEqual(janela.get_at((x, y))[:3], (220, 113, 137))
        self.assertEqual(janela.get_at((1000, 50))[:3], (73, 59, 69))

    def test_abre_em_tela_cheia_e_f11_alterna_sem_perder_o_desenho(self):
        pygame.init()
        tela = criar_janela()
        self.assertTrue(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        self.assertEqual(pygame.display.get_surface().get_size(), pygame.display.get_desktop_sizes()[0])
        self.assertEqual(tela.get_size(), (900, 400))
        tratar_redimensionamento(tecla(pygame.K_F11))
        self.assertFalse(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        tamanho = pygame.display.get_surface().get_size()
        tratar_redimensionamento(tecla(pygame.K_F11))
        self.assertTrue(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        # Eventos antigos de resize não devem fazer sair da tela cheia.
        tratar_redimensionamento(pygame.event.Event(pygame.VIDEORESIZE, w=900, h=400))
        self.assertTrue(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        tratar_redimensionamento(tecla(pygame.K_F11))
        self.assertEqual(pygame.display.get_surface().get_size(), tamanho)

    def test_tab_alterna_detalhes_sem_mudar_parametros(self):
        sessao = SimpleNamespace(concluida=False, parametros=(-1.5, 0.7, 0.2, 0.0, 0.5), recorde_treino=30,
                                 terminou=lambda ambiente: False)
        eventos = [[tecla(pygame.K_TAB)], [tecla(pygame.K_TAB)], [pygame.event.Event(pygame.QUIT)]]
        detalhes = []
        with patch("main.Avaliacao", return_value=sessao), patch("main.pygame.time.Clock"), \
                patch("main.pygame.event.get", side_effect=eventos), \
                patch("main.desenhar", side_effect=lambda *args: detalhes.append(args[-1])):
            main.main("avaliacao")
        self.assertEqual(detalhes, [True, False])
        self.assertEqual(sessao.parametros, (-1.5, 0.7, 0.2, 0.0, 0.5))

    def test_relogio_mostra_horas_sem_voltar_a_zero(self):
        self.assertEqual(formatar_tempo(65), "01:05")
        self.assertEqual(formatar_tempo(3665), "1:01:05")

    def test_colisao_seleciona_sprite_vermelho_e_reinicio_volta_ao_normal(self):
        pygame.init()
        tela = pygame.display.set_mode((900, 400))
        recursos = RecursosInterface()
        ambiente = Ambiente(123)
        sessao = JogoHumano(self.caminho)
        with patch.object(recursos, "sprite", wraps=recursos.sprite) as sprite, \
                patch.object(recursos, "sprite_corrida", wraps=recursos.sprite_corrida) as corrida:
            ambiente.fim_de_jogo = True
            desenhar(tela, recursos, ambiente, sessao, "humano")
            sprite.assert_called_with(76, atingida=True)
            corrida.assert_not_called()
            sprite.reset_mock()
            ambiente.reiniciar(123)
            desenhar(tela, recursos, ambiente, sessao, "humano")
            sprite.assert_not_called()
            corrida.assert_called_with(76, 0)
        self.assertEqual(recursos.sprite(76).get_size(), recursos.sprite(76, True).get_size())
        self.assertIsNot(recursos.sprite(76), recursos.sprite(76, True))



if __name__ == "__main__":
    unittest.main()
