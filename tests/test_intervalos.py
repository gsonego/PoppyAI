"""Sequências próximas, visíveis antes da chegada e com espaço para novos saltos."""

from itertools import cycle
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente, GrupoObstaculo
from config import CHAO_Y, INTERVALO_MINIMO_PX, LARGURA, SEMENTE_TREINO


class TestIntervalos(unittest.TestCase):
    def test_intervalo_varia_encurta_em_tempo_e_respeita_piso(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        amostras = [ambiente._sortear_intervalo() for _ in range(100)]
        self.assertGreater(len(set(amostras)), 1)
        ambiente.gerador_obstaculos.seed(123)
        inicial = ambiente._sortear_intervalo() / ambiente.velocidade
        ambiente.tempo_vivo = 120
        ambiente.gerador_obstaculos.seed(123)
        final = ambiente._sortear_intervalo() / ambiente.velocidade
        self.assertLess(final, inicial)
        self.assertTrue(all(ambiente._sortear_intervalo() >= INTERVALO_MINIMO_PX for _ in range(100)))

    def test_conjuntos_surgem_fora_da_tela_e_sensor_avanca_para_proximo(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        primeiro = ambiente.obstaculo
        ambiente.avancar(False)
        self.assertGreaterEqual(len(ambiente.grupos), 2)
        segundo = ambiente.grupos[1].retangulo
        self.assertGreaterEqual(segundo.left, LARGURA)
        self.assertEqual(segundo.left - primeiro.right, ambiente.grupos[1].intervalo_anterior)
        # O alvo muda quando o conjunto passou completamente pela personagem,
        # mas a caixa anterior continua desenhada até sair da tela.
        ambiente._alvo.x = ambiente.personagem.left - primeiro.width - 1
        ambiente.avancar(False)
        self.assertIs(ambiente.obstaculo, segundo)
        self.assertIn(primeiro, [g.retangulo for g in ambiente.grupos])
        self.assertTrue(any(c.right == primeiro.right for c in ambiente.caixas_visiveis))

    def test_caixas_futuras_ficam_visiveis_enquanto_anterior_ainda_esta_na_pista(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        ambiente.personagem.x = -10000  # Observa a pista sem sofrer colisões.
        encontrou = False
        for _ in range(400):
            ambiente.avancar(False)
            visiveis = [g for g in ambiente.grupos if 0 < g.retangulo.right and g.retangulo.left < LARGURA]
            if len(visiveis) >= 2:
                encontrou = True
                break
        self.assertTrue(encontrou)

    def test_pares_maximos_consecutivos_no_menor_intervalo_permitem_saltos(self):
        # Alterna os pares mais altos e mais largos, no menor vão permitido.
        # Usa uma política de referência só no teste, para verificar a física.
        for velocidade in (350, 500, 650):
            with self.subTest(velocidade=velocidade):
                ambiente = Ambiente(SEMENTE_TREINO)
                ambiente.tempo_vivo = (velocidade - 350) / 2.5
                ambiente.tipo_obstaculo = "lado_a_lado"
                ambiente.obstaculo.size = (80, 70)
                ambiente.obstaculo.bottom = CHAO_Y
                tipos = cycle((("empilhadas", 40, 84), ("lado_a_lado", 80, 70)))
                surgimentos = []

                def criar(x):
                    tipo, largura, altura = next(tipos)
                    surgimentos.append(x)
                    return GrupoObstaculo(pygame.Rect(round(x), CHAO_Y - altura, largura, altura), x, tipo)

                passados = 0
                with patch.object(ambiente, "_sortear_intervalo", return_value=INTERVALO_MINIMO_PX), \
                        patch.object(ambiente, "_sortear_obstaculo", side_effect=criar):
                    for _ in range(2400):
                        anterior = ambiente.obstaculo
                        limiar = ambiente.velocidade * 0.35 - (ambiente.obstaculo.width + ambiente.personagem.width) / 2
                        ambiente.avancar(0 <= ambiente.distancia <= limiar)
                        self.assertFalse(ambiente.fim_de_jogo)
                        if ambiente.obstaculo is not anterior:
                            passados += 1
                self.assertGreater(passados, 15)
                self.assertTrue(all(x >= LARGURA for x in surgimentos))


if __name__ == "__main__":
    unittest.main()
