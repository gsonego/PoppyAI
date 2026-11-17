"""Física idêntica em diferentes ritmos de apresentação e vistas sem mutações."""

import unittest
from unittest.mock import patch

from ambiente import Ambiente
from apresentacao import VistaAmbiente
from temporizacao import AvancoFixo, RelogioQuadros


class TestTemporizacao(unittest.TestCase):
    def test_fisica_e_sequencia_iguais_em_30_60_144_e_240_fps(self):
        estados = []
        for fps in (30, 60, 144, 240):
            ambiente = Ambiente(123)
            ambiente.personagem.x = -10000
            avanco = AvancoFixo()
            passos = 0
            for _ in range(fps * 10):
                for _ in range(avanco.acumular(1 / fps)):
                    ambiente.avancar(passos == 30)
                    passos += 1
            self.assertEqual(passos, 600)
            estados.append((ambiente.posicao_y, ambiente.tempo_vivo, ambiente.distancia_percorrida,
                            [(g.x, tuple(g.retangulo), g.tipo) for g in ambiente.grupos],
                            ambiente.gerador_obstaculos.getstate()))
        self.assertTrue(all(e == estados[0] for e in estados))

    def test_atrasos_irregulares_mantem_passos_e_pausa_longa_nao_explode(self):
        avanco = AvancoFixo()
        total = sum(avanco.acumular(dt) for dt in (0.005, 0.025, 0.010, 0.040, 0.020))
        self.assertEqual(total, 6)
        self.assertLess(avanco.fracao, 0.0001)
        self.assertEqual(avanco.acumular(10), 15)

    def test_vista_intermediaria_move_mundo_e_personagem_sem_alterar_fisica(self):
        ambiente = Ambiente(123)
        ambiente.avancar(True)
        original = (ambiente.posicao_y, tuple(ambiente.personagem), ambiente.distancia_percorrida,
                    [(g.x, tuple(g.retangulo)) for g in ambiente.grupos])
        inicio, meio, fim = [VistaAmbiente(ambiente, fracao) for fracao in (0, 0.5, 1)]
        self.assertGreater(inicio.personagem.y, meio.personagem.y)
        self.assertGreater(meio.personagem.y, fim.personagem.y)
        self.assertAlmostEqual(meio.distancia_percorrida, ambiente.distancia_percorrida / 2)
        self.assertGreater(inicio.obstaculo.x, meio.obstaculo.x)
        self.assertGreater(meio.obstaculo.x, fim.obstaculo.x)
        self.assertEqual(original, (ambiente.posicao_y, tuple(ambiente.personagem), ambiente.distancia_percorrida,
                                    [(g.x, tuple(g.retangulo)) for g in ambiente.grupos]))
        ambiente.reiniciar(123)
        vista = VistaAmbiente(ambiente, 0.5)
        self.assertEqual(vista.distancia_percorrida, 0)
        self.assertEqual(vista.personagem, ambiente.personagem)

    def test_relogio_mede_quadros_e_espera_prazo_com_precisao(self):
        with patch("temporizacao.perf_counter", side_effect=[0, 0.005, 0.010, 0.015, 0.020]), \
                patch("temporizacao.sleep") as dormir:
            relogio = RelogioQuadros(100)
            self.assertAlmostEqual(relogio.tick(), 0.010)
            self.assertAlmostEqual(relogio.tick(), 0.010)
            self.assertEqual(dormir.call_count, 2)
            self.assertEqual(relogio.resumo(), (100.0, 10.0, 10.0))


if __name__ == "__main__":
    unittest.main()
