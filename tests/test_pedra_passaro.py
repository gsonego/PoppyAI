"""Pássaro separado, chegando pouco depois da pedra nos três modos."""

import unittest

from ambiente import Ambiente
from config import (INTERVALO_MINIMO_PX, PEDRA_PASSARO_ATRASO,
                    PEDRA_PASSARO_INTERVALO_MINIMO)


class TestPedraPassaro(unittest.TestCase):
    @staticmethod
    def criar_sequencia(tempo=0, distancia=76):
        ambiente = Ambiente(123, incluir_pedras=True, incluir_passarinhos=True, incluir_tuneis=True)
        pedra = ambiente._sortear_obstaculo(ambiente.personagem.right + distancia)
        ambiente.grupos = [pedra]
        ambiente._alvo = pedra
        ambiente.tempo_vivo = tempo
        ambiente._completar_pista()
        return ambiente, pedra, ambiente.grupos[1]

    def test_pedra_e_passaro_sao_separados_com_atraso_consistente(self):
        for tempo in (0, 60, 120):
            ambiente, pedra, passaro = self.criar_sequencia(tempo)
            esperado = max(PEDRA_PASSARO_INTERVALO_MINIMO,
                           round(ambiente.velocidade * PEDRA_PASSARO_ATRASO))
            self.assertEqual((pedra.tipo, passaro.tipo), ("pedra", "passarinho"))
            self.assertEqual(passaro.retangulo.left - pedra.retangulo.right, esperado)
            self.assertEqual(passaro.intervalo_anterior, esperado)
            self.assertFalse(pedra.retangulo.colliderect(passaro.retangulo))
            seguinte = ambiente.grupos[2]
            self.assertGreaterEqual(seguinte.retangulo.left - passaro.retangulo.right, INTERVALO_MINIMO_PX)

    def test_correndo_passa_sem_mudar_altura(self):
        for tempo in (0, 120):
            ambiente, _, passaro = self.criar_sequencia(tempo)
            y = ambiente.posicao_y
            while passaro.retangulo.right > ambiente.personagem.left:
                ambiente.avancar(False)
                self.assertFalse(ambiente.fim_de_jogo)
                self.assertEqual(ambiente.posicao_y, y)

    def test_agachada_bate_na_pedra(self):
        ambiente, pedra, _ = self.criar_sequencia()
        ambiente.definir_abaixada(True)
        for _ in range(30):
            ambiente.avancar(False)
            if ambiente.fim_de_jogo:
                break
        self.assertTrue(ambiente.fim_de_jogo)
        self.assertTrue(ambiente._colidiu(pedra))

    def test_salto_perto_da_pedra_encontra_passaro_em_toda_faixa_de_velocidade(self):
        for velocidade in range(350, 651, 25):
            tempo = (velocidade - 350) / 2.5
            for distancia in (0, round(velocidade * 0.2)):
                ambiente, _, passaro = self.criar_sequencia(tempo, distancia)
                ambiente.pular_manualmente()
                for _ in range(80):
                    ambiente.avancar(False)
                    if ambiente.fim_de_jogo:
                        break
                self.assertTrue(ambiente.fim_de_jogo, (velocidade, distancia))
                self.assertTrue(ambiente._colidiu(passaro), (velocidade, distancia))

    def test_primeiros_desafios_repetem_no_mundo_e_opcao_desabilita_pedras(self):
        def percurso():
            ambiente = Ambiente(123, incluir_pedras=True, incluir_passarinhos=True, incluir_tuneis=True)
            ambiente.personagem.x = -10000
            vistos = {}
            sequencia = []
            for _ in range(900):
                for grupo in ambiente.grupos:
                    if id(grupo) not in vistos:
                        vistos[id(grupo)] = grupo
                        sequencia.append((grupo.tipo, grupo.retangulo.size, grupo.intervalo_anterior))
                ambiente.avancar(False)
            return sequencia
        primeira = percurso()
        self.assertEqual([tipo for tipo, _, _ in primeira[:4]], ["simples", "pedra", "passarinho", "tunel"])
        self.assertEqual(percurso(), primeira)
        ia = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        ia.personagem.x = -10000
        for _ in range(900):
            ia.avancar(False)
            self.assertNotIn("pedra", [g.tipo for g in ia.grupos])
