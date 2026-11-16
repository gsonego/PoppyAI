"""Geometria, colisões, repetição e possibilidade de salto nos pares de caixas."""

import unittest

from ambiente import Ambiente
from config import CHAO_Y, SEMENTE_TREINO


class TestCaixasDuplas(unittest.TestCase):
    def test_pares_formam_um_conjunto_sem_vaos_ou_sobreposicao(self):
        for tipo, tamanho in (("lado_a_lado", (80, 70)), ("empilhadas", (40, 84))):
            with self.subTest(tipo=tipo):
                ambiente = Ambiente(SEMENTE_TREINO)
                ambiente.tipo_obstaculo = tipo
                ambiente.obstaculo.size = tamanho
                ambiente.obstaculo.bottom = CHAO_Y
                caixas = ambiente.caixas
                self.assertEqual(len(caixas), 2)
                self.assertFalse(caixas[0].colliderect(caixas[1]))
                self.assertEqual(caixas[0].union(caixas[1]), ambiente.obstaculo)
                self.assertEqual(sum(c.width * c.height for c in caixas), tamanho[0] * tamanho[1])
                self.assertEqual(caixas[0].size, caixas[1].size)

    def test_colisao_detecta_caixa_de_cima_e_segunda_caixa_lateral(self):
        for tipo, tamanho, indice in (("empilhadas", (40, 84), 0), ("lado_a_lado", (80, 70), 1)):
            with self.subTest(tipo=tipo):
                ambiente = Ambiente(SEMENTE_TREINO)
                ambiente.tipo_obstaculo = tipo
                ambiente.obstaculo.size = tamanho
                ambiente.obstaculo.bottom = CHAO_Y
                alvo = ambiente.caixas[indice]
                ambiente.personagem.x = alvo.left + 2
                ambiente.posicao_y = float(alvo.top - 20)
                ambiente.personagem.y = round(ambiente.posicao_y)
                ambiente.no_chao = False
                ambiente.avancar(False)
                self.assertTrue(ambiente.fim_de_jogo)

    def test_semente_repete_tipos_tamanhos_e_intervalos(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        sequencias = []
        for _ in range(2):
            ambiente.reiniciar(SEMENTE_TREINO)
            self.assertEqual(ambiente.tipo_obstaculo, "simples")
            self.assertEqual(ambiente.obstaculo.size, (30, 50))
            sequencia = []
            for _ in range(100):
                ambiente.obstaculo_x = -100.0
                ambiente.avancar(False)
                sequencia.append((ambiente.tipo_obstaculo, ambiente.obstaculo.size, ambiente.obstaculo.x))
            sequencias.append(sequencia)
        self.assertEqual(sequencias[0], sequencias[1])
        self.assertEqual({item[0] for item in sequencias[0]}, {"simples", "lado_a_lado", "empilhadas"})
        for tipo, (largura, altura), _ in sequencias[0]:
            if tipo == "lado_a_lado":
                self.assertTrue(40 <= largura <= 80 and 30 <= altura <= 70)
            elif tipo == "empilhadas":
                self.assertTrue(20 <= largura <= 40 and 60 <= altura <= 84)

    def test_r_manual_preserva_par_e_sequencia_atual(self):
        ambiente = Ambiente(SEMENTE_TREINO)
        ambiente.tipo_obstaculo = "empilhadas"
        ambiente.obstaculo.size = (40, 84)
        ambiente.obstaculo.bottom = CHAO_Y
        estado_aleatorio = ambiente.gerador_obstaculos.getstate()
        ambiente.reiniciar_manualmente()
        self.assertEqual(ambiente.tipo_obstaculo, "empilhadas")
        self.assertEqual(ambiente.obstaculo.size, (40, 84))
        self.assertEqual(ambiente.gerador_obstaculos.getstate(), estado_aleatorio)
        self.assertTrue(ambiente.tentativa_manual)

    def test_maiores_conjuntos_podem_ser_ultrapassados_com_salto_atual(self):
        # Testa o salto de verdade, com movimento, arredondamento e colisão atuais.
        # Tamanhos menores estão contidos nestes retângulos máximos.
        for tipo, tamanho in (("simples", (50, 70)), ("lado_a_lado", (80, 70)), ("empilhadas", (40, 84))):
            with self.subTest(tipo=tipo):
                saltos_validos = []
                for distancia in range(20, 301, 2):
                    ambiente = Ambiente(SEMENTE_TREINO)
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
                            saltos_validos.append(distancia)
                            break
                self.assertTrue(saltos_validos, "Nenhum momento de salto permitiu passar")


if __name__ == "__main__":
    unittest.main()
