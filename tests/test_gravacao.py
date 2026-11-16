"""Verifica a gravação em segundo plano mesmo quando o disco demora ou falha."""

import contextlib
import io
import os
import tempfile
from pathlib import Path
from threading import Event, Thread
import unittest
from unittest.mock import patch

import pygame
import main
from campeao import GravadorCampeao, carregar_campeao, salvar_campeao
from config import SEMENTE_TREINO
from geracoes import TreinoGeracoes


class TestGravacao(unittest.TestCase):
    def test_jogo_avanca_enquanto_disco_esta_bloqueado_e_salva_ao_sair(self):
        iniciou = Event()
        liberar = Event()
        quadro = [0]
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            caminho = Path(pasta) / "campeao.json"

            def criar_treino(**opcoes):
                return TreinoGeracoes(caminho, **opcoes)

            def salvar_lento(*pedido):
                iniciou.set()
                if not liberar.wait(3):
                    raise TimeoutError("O laço do jogo ficou bloqueado")
                salvar_campeao(*pedido)

            def eventos():
                quadro[0] += 1
                if quadro[0] == 70:
                    self.assertTrue(iniciou.wait(2))
                if quadro[0] == 91:
                    # O jogo avançou mais 20 quadros com a gravação ainda parada.
                    self.assertFalse(liberar.is_set())
                    liberar.set()
                    return [pygame.event.Event(pygame.QUIT)]
                return []

            try:
                with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}), \
                        patch("main.TreinoGeracoes", side_effect=criar_treino), \
                        patch("campeao.salvar_campeao", side_effect=salvar_lento), \
                        patch("main.pygame.time.Clock"), \
                        patch("main.pygame.event.get", side_effect=eventos), \
                        patch("main.desenhar_populacao"):
                    main.main("treino")
            finally:
                liberar.set()
            _, tempo = carregar_campeao(caminho, None, SEMENTE_TREINO)
            self.assertAlmostEqual(tempo, 1.5)

    def test_disco_lento_nao_bloqueia_pedidos_e_preserva_ultimo_recorde(self):
        iniciou = Event()
        liberar = Event()
        encerrou = Event()
        chamadas = []
        erros = []
        gravador = GravadorCampeao()
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "campeao.json"

            def salvar_lento(*pedido):
                chamadas.append(pedido)
                if len(chamadas) == 1:
                    iniciou.set()
                    if not liberar.wait(3):
                        raise TimeoutError("Teste não liberou o disco simulado")
                salvar_campeao(*pedido)

            def fechar():
                try:
                    gravador.fechar()
                except Exception as erro:
                    erros.append(erro)
                finally:
                    encerrou.set()

            with patch("campeao.salvar_campeao", side_effect=salvar_lento):
                try:
                    parametros = [-1.5, 0.2, 0.3, 0.0, 0.5]
                    gravador.agendar(caminho, parametros, 65, None, SEMENTE_TREINO)
                    self.assertTrue(iniciou.wait(2))
                    parametros[1] = 9  # Não deve modificar o pedido já entregue.
                    gravador.agendar(caminho, (-1.4, 0.3, 0.4, 0.0, 0.6), 66, None, SEMENTE_TREINO)
                    gravador.agendar(caminho, (-1.3, 0.4, 0.5, 0.0, 0.7), 67, None, SEMENTE_TREINO)
                    # Os pedidos acima retornaram com a primeira gravação ainda parada.
                    self.assertEqual(len(chamadas), 1)
                    thread = Thread(target=fechar)
                    thread.start()
                    self.assertFalse(encerrou.wait(0.02))
                finally:
                    liberar.set()
                    if 'thread' in locals():
                        thread.join(3)
                    else:
                        gravador.fechar()
                self.assertTrue(encerrou.is_set())
                self.assertEqual(erros, [])
            self.assertEqual([pedido[2] for pedido in chamadas], [65, 67])
            self.assertEqual(chamadas[0][1], (-1.5, 0.2, 0.3, 0.0, 0.5))
            self.assertEqual(carregar_campeao(caminho, None, SEMENTE_TREINO),
                             ((-1.3, 0.4, 0.5, 0.0, 0.7), 67))

    def test_falha_de_gravacao_e_informada(self):
        falhou = Event()
        gravador = GravadorCampeao()

        def falhar(*pedido):
            falhou.set()
            raise PermissionError("Disco indisponível")

        with patch("campeao.salvar_campeao", side_effect=falhar):
            gravador.agendar("nao-deve-ser-criado.json", (-1, 0, 0, 0, 0.5), 65, None, SEMENTE_TREINO)
            self.assertTrue(falhou.wait(2))
            with self.assertRaisesRegex(OSError, "Disco indisponível"):
                gravador.fechar()
            with self.assertRaises(OSError):
                gravador.verificar_erro()

    def test_fechar_sem_gravacoes_nao_cria_thread(self):
        gravador = GravadorCampeao()
        gravador.fechar()
        with self.assertRaises(RuntimeError):
            gravador.agendar("nao-deve-ser-criado.json", (-1, 0, 0, 0, 0.5), 65, None, SEMENTE_TREINO)


if __name__ == "__main__":
    unittest.main()
