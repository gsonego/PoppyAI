"""Solicitação de VSync, alternativa sem renderer e coordenadas da tela lógica."""

import os
from pathlib import Path
import subprocess
import sys
import textwrap
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

    def test_mouse_nao_consulta_superficie_no_tratamento_de_resize(self):
        with patch("janela.pygame.display.get_surface") as superficie:
            janela.tratar_redimensionamento(pygame.event.Event(pygame.MOUSEMOTION, pos=(10, 20)))
            janela.tratar_redimensionamento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 20), button=1))
        superficie.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Verificação nativa da janela SDL no Windows")
    def test_referencia_sdl_permanece_viva_ao_processar_mouse_nativo(self):
        # Uma regressão pode corromper a memória do interpretador: isola a prova
        # em subprocesso, usando a DLL real e eventos SDL com windowID válido.
        codigo = textwrap.dedent('''
            import ctypes
            import gc
            from pathlib import Path
            import struct
            import pygame
            import janela

            pygame.init()
            pygame.display.set_mode((900, 400))
            sdl = ctypes.CDLL(str(Path(pygame.__file__).parent / "SDL2.dll"))
            sdl.SDL_GetWindowFromID.argtypes = [ctypes.c_uint32]
            sdl.SDL_GetWindowFromID.restype = ctypes.c_void_p
            sdl.SDL_GetWindowData.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            sdl.SDL_GetWindowData.restype = ctypes.c_void_p
            sdl.SDL_PushEvent.argtypes = [ctypes.c_void_p]
            sdl.SDL_PushEvent.restype = ctypes.c_int
            movimentos = 0
            for indice in range(2000):
                if indice % 250 == 0:
                    pygame.display.set_mode((900, 400))
                janela._consulta_renderer()
                dono = janela._janela_sdl
                ponteiro = sdl.SDL_GetWindowFromID(dono.id)
                assert sdl.SDL_GetWindowData(ponteiro, b"pg_window") == id(dono)
                if indice % 50 == 0:
                    gc.collect()
                evento = ctypes.create_string_buffer(56)
                struct.pack_into("<IIIIIiiii", evento, 0, pygame.MOUSEMOTION, 0,
                                 dono.id, 0, 0, indice % 900, 100, 1, 0)
                assert sdl.SDL_PushEvent(evento) == 1
                for recebido in pygame.event.get():
                    if recebido.type == pygame.MOUSEMOTION:
                        assert recebido.window is dono
                        movimentos += 1
            assert movimentos == 2000
            pygame.quit()
            print("2000 movimentos SDL processados com referencia valida")
        ''')
        resultado = subprocess.run([sys.executable, "-X", "faulthandler", "-c", codigo],
                                   cwd=Path(__file__).resolve().parents[1],
                                   env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertIn("2000 movimentos SDL", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
