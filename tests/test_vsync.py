"""Solicitação de VSync, alternativa sem renderer e coordenadas da tela lógica."""

import os
import unittest
from unittest.mock import patch

import pygame

import janela
from temporizacao import RelogioQuadros


class TestVSync(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        pygame.init()
        self.addCleanup(pygame.quit)
        pygame.display.set_mode((900, 400))
        modo = patch("janela._modo_escalado", False)
        modo.start()
        self.addCleanup(modo.stop)

    def test_solicita_renderer_com_vsync_e_resolucao_logica(self):
        with patch("janela.pygame.display.get_driver", return_value="windows"), \
                patch("janela.pygame.display.set_mode") as abrir:
            janela._abrir_modo(True)
        abrir.assert_called_once_with((900, 400), pygame.FULLSCREEN | pygame.SCALED, vsync=1)
        self.assertTrue(janela._modo_escalado)

    def test_falha_do_renderer_abre_modo_anterior(self):
        with patch("janela.pygame.display.get_driver", return_value="windows"), \
                patch("janela.pygame.display.set_mode", side_effect=[pygame.error("Sem renderer"), None]) as abrir:
            janela._abrir_modo(True)
        self.assertFalse(janela._modo_escalado)
        self.assertEqual(abrir.call_count, 2)
        self.assertEqual(abrir.call_args.args, ((0, 0), pygame.FULLSCREEN))

    def test_diagnostico_so_confirma_vsync_com_suporte_do_renderer(self):
        with patch("janela._modo_escalado", True), \
                patch("janela.pygame.display.get_driver", return_value="windows"), \
                patch("janela._consulta_renderer", return_value=("direct3d", 14)):
            self.assertTrue(janela.vsync_ativo())
            self.assertEqual(janela.estado_apresentacao(), "VSYNC ATIVO")
        with patch("janela._modo_escalado", True), \
                patch("janela.pygame.display.get_driver", return_value="windows"), \
                patch("janela._consulta_renderer", return_value=("software", 1)):
            self.assertFalse(janela.vsync_ativo())
            self.assertEqual(janela.estado_apresentacao(), "VSYNC SOLICITADO")

    def test_relogio_nao_adiciona_espera_quando_renderer_sincroniza(self):
        with patch("temporizacao.vsync_ativo", return_value=True), \
                patch("temporizacao.perf_counter", side_effect=[0, 0.005, 0.006]), \
                patch("temporizacao.sleep") as dormir:
            relogio = RelogioQuadros(60)
            self.assertAlmostEqual(relogio.tick(), 0.006)
            dormir.assert_not_called()

    def test_coordenadas_escaladas_nao_sao_convertidas_duas_vezes(self):
        with patch("janela._usando_escalado", return_value=True):
            self.assertEqual(janela.posicao_logica((500, 180)), (500, 180))
            self.assertIsNone(janela.posicao_logica((-1, 180)))
            self.assertIsNone(janela.posicao_logica((900, 180)))

    def test_renderer_recebe_imagem_logica_sem_escala_por_cpu(self):
        tela = pygame.Surface((900, 400))
        tela.fill("#DC7189")
        with patch("janela._usando_escalado", return_value=True), \
                patch("janela.pygame.transform.scale") as escala:
            janela.apresentar(tela)
        escala.assert_not_called()
        self.assertEqual(pygame.display.get_surface().get_at((10, 10))[:3], (220, 113, 137))


if __name__ == "__main__":
    unittest.main()
