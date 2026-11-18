"""Aceleração reproduzível, observação da IA e obstáculos possíveis até o teto."""

from tests.apoio import rede_simples

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from ambiente import Ambiente
from campeao import carregar_campeao, salvar_campeao
from config import ACELERACAO_OBSTACULO, CHAO_Y, PASSO, SEMENTE_TREINO, VELOCIDADE_MAXIMA, VELOCIDADE_OBSTACULO
from geracoes import TreinoGeracoes
from politica import calcular_saidas


class TestVelocidade(unittest.TestCase):
    def test_sobe_gradualmente_ate_teto_e_reinicios_restauram_inicio(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        for tempo, velocidade in ((0, 350), (10, 375), (30, 425), (60, 500), (120, 650), (500, 650)):
            ambiente.tempo_vivo = tempo
            self.assertEqual(ambiente.velocidade, velocidade)
        ambiente.reiniciar_manualmente()
        self.assertEqual(ambiente.velocidade, VELOCIDADE_OBSTACULO)
        ambiente.tempo_vivo = 120
        ambiente.reiniciar(SEMENTE_TREINO)
        self.assertEqual(ambiente.velocidade, VELOCIDADE_OBSTACULO)

    def test_movimento_usa_velocidade_observada_e_morte_congela_aceleracao(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        ambiente.tempo_vivo = 60
        posicao = ambiente.obstaculo_x
        ambiente.avancar(False)
        self.assertAlmostEqual(posicao - ambiente.obstaculo_x, 500 * PASSO)
        self.assertAlmostEqual(ambiente.velocidade, 500 + ACELERACAO_OBSTACULO * PASSO)
        ambiente.fim_de_jogo = True
        velocidade = ambiente.velocidade
        ambiente.avancar(False)
        self.assertEqual(ambiente.velocidade, velocidade)

    def test_velocidade_pode_antecipar_salto_na_mesma_distancia(self):
        parametros = rede_simples((-1, 0, 0, 1, -0.5))
        self.assertLess(calcular_saidas((200/900, 50/400, 40/900, 350/650, 0), parametros)[0], 0)
        self.assertGreater(calcular_saidas((200/900, 50/400, 40/900, 1, 0), parametros)[0], 0)

    def test_50_poppys_compartilham_aceleracao_e_sequencia(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            treino = TreinoGeracoes(Path(pasta) / "campeao.json")
            # Afasta apenas as personagens para observar a evolução do mundo sem colisões.
            for poppy in treino.individuos:
                poppy.ambiente.personagem.x = -10000
            for _ in range(600):
                treino.avancar()
            referencia = treino.individuos[0].ambiente
            self.assertEqual(len(treino.vivos), 50)
            self.assertAlmostEqual(referencia.velocidade, 375)
            for poppy in treino.individuos:
                self.assertEqual(poppy.ambiente.velocidade, referencia.velocidade)
                self.assertEqual(poppy.ambiente.obstaculo, referencia.obstaculo)

    def test_campea_preserva_peso_velocidade_e_rejeita_valor_ausente(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados" / "campeoes" / "campeao.json"
            parametros = rede_simples((-1.5, 0.7, -0.4, 0.25, 0.45))
            salvar_campeao(caminho, parametros, 150, None, SEMENTE_TREINO)
            self.assertEqual(carregar_campeao(caminho, None, SEMENTE_TREINO), (parametros, 150))
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            del dados["parametros"][3]
            caminho.write_text(json.dumps(dados), encoding="utf-8")
            with self.assertRaises(ValueError):
                carregar_campeao(caminho, None, SEMENTE_TREINO)

    def test_maiores_obstaculos_sao_ultrapassaveis_em_toda_faixa_de_velocidade(self):
        # Busca um salto real para cada combinação máxima, incluindo aceleração
        # durante o salto, arredondamento dos retângulos e a nova colisão da Poppy.
        for velocidade in range(VELOCIDADE_OBSTACULO, VELOCIDADE_MAXIMA + 1, 25):
            for tipo, tamanho in (("simples", (50, 70)), ("lado_a_lado", (80, 70)), ("empilhadas", (40, 84))):
                with self.subTest(velocidade=velocidade, tipo=tipo):
                    passou = False
                    for distancia in range(20, 501, 2):
                        ambiente = Ambiente(SEMENTE_TREINO)
                        ambiente.tempo_vivo = (velocidade - VELOCIDADE_OBSTACULO) / ACELERACAO_OBSTACULO
                        ambiente.tipo_obstaculo = tipo
                        ambiente.obstaculo.size = tamanho
                        ambiente.obstaculo.bottom = CHAO_Y
                        ambiente.obstaculo_x = float(ambiente.personagem.right + distancia)
                        ambiente.obstaculo.x = round(ambiente.obstaculo_x)
                        alvo_testado = ambiente.obstaculo
                        for passo in range(100):
                            ambiente.avancar(passo == 0)
                            if ambiente.fim_de_jogo:
                                break
                            if alvo_testado.right <= ambiente.personagem.left:
                                passou = True
                                break
                        if passou:
                            break
                    self.assertTrue(passou, "Nenhum momento de salto permitiu ultrapassar")


if __name__ == "__main__":
    unittest.main()
