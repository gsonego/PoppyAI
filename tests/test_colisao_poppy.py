"""Colisão ampliada para a cabeça e o corpo, preservando tolerância nas extremidades."""

import unittest

from ambiente import Ambiente
from config import CHAO_Y


class TestColisaoPoppy(unittest.TestCase):
    def test_area_cobre_corpo_e_cabeca_e_sensor_usa_nova_frente(self):
        ambiente = Ambiente(123)
        self.assertEqual(ambiente.personagem.size, (48, 56))
        self.assertEqual(ambiente.personagem.bottom, CHAO_Y)
        self.assertTrue(ambiente.personagem.collidepoint(140, CHAO_Y - 50))
        self.assertFalse(ambiente.personagem.collidepoint(115, CHAO_Y - 70))
        self.assertFalse(ambiente.personagem.collidepoint(95, CHAO_Y - 30))
        self.assertEqual(ambiente.distancia, ambiente.obstaculo.left - ambiente.personagem.right)

    def test_contato_apenas_na_cabeca_encerra_partida(self):
        ambiente = Ambiente(123)
        ambiente.obstaculo.size = (10, 8)
        ambiente.obstaculo.topleft = (135, CHAO_Y - 50)
        ambiente.obstaculo_x = 135.0
        # Não alcança a antiga caixa de 40 px de altura.
        self.assertLess(ambiente.obstaculo.bottom, CHAO_Y - 40)
        ambiente.avancar(False)
        self.assertTrue(ambiente.fim_de_jogo)

    def test_contato_nas_pontas_das_orelhas_nao_encerra_partida(self):
        ambiente = Ambiente(123)
        ambiente.obstaculo.size = (8, 8)
        ambiente.obstaculo.topleft = (125, CHAO_Y - 72)
        ambiente.obstaculo_x = 125.0
        ambiente.avancar(False)
        self.assertFalse(ambiente.fim_de_jogo)

    def test_salto_e_reinicio_preservam_tamanho_e_alinhamento_com_chao(self):
        ambiente = Ambiente(123)
        original = ambiente.personagem.copy()
        ambiente.avancar(True)
        self.assertLess(ambiente.personagem.bottom, CHAO_Y)
        self.assertEqual(ambiente.personagem.size, original.size)
        ambiente.reiniciar(123)
        self.assertEqual(ambiente.personagem, original)


if __name__ == "__main__":
    unittest.main()
