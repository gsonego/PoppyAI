"""Os registros distinguem encerramento normal e erro sem esconder a falha."""

from pathlib import Path
import tempfile
import unittest

from diagnostico import registrar_execucao, registro


class TestDiagnostico(unittest.TestCase):
    def test_saida_normal_e_historico_preservado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "logs" / "jogo.log"
            for _ in range(2):
                with registrar_execucao(caminho):
                    registro.info("Pedido de fechar a janela no treino")
            conteudo = caminho.read_text(encoding="utf-8")
            self.assertEqual(conteudo.count("Iniciando jogo"), 2)
            self.assertEqual(conteudo.count("Jogo encerrado normalmente"), 2)
            self.assertIn("Pedido de fechar a janela no treino", conteudo)

    def test_falha_grava_detalhes_e_continua_visivel(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "jogo.log"
            with self.assertRaisesRegex(RuntimeError, "falha simulada"):
                with registrar_execucao(caminho):
                    raise RuntimeError("falha simulada")
            conteudo = caminho.read_text(encoding="utf-8")
            self.assertIn("Traceback", conteudo)
            self.assertIn("RuntimeError: falha simulada", conteudo)
            self.assertNotIn("Jogo encerrado normalmente", conteudo)
