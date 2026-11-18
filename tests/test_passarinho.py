"""O passarinho alto permite correr e pune saltos na sua trajetória."""

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente
from apresentacao import VistaAmbiente
from art.passarinho import criar_quadros, quadro_passarinho
from config import PASSARINHO_CENTRO_Y, CHAO_Y
from interface import RecursosInterface, desenhar


class TestPassarinho(unittest.TestCase):
    def test_elevacao_distingue_caixa_tunel_e_passarinho(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        self.assertEqual(ambiente.elevacao_obstaculo, 0)
        ambiente._alvo = ambiente._sortear_obstaculo(900)
        self.assertEqual(ambiente.elevacao_obstaculo, 42)
        ambiente._alvo = ambiente._sortear_obstaculo(900)
        self.assertEqual(ambiente.elevacao_obstaculo, 92)

    @staticmethod
    def criar_perto(x=225, tempo=0):
        ambiente = Ambiente(123, incluir_passarinhos=True)
        grupo = ambiente._sortear_obstaculo(x)
        ambiente.grupos = [grupo]
        ambiente._alvo = grupo
        ambiente.tempo_vivo = tempo
        return ambiente

    def test_correr_e_abaixar_passam_sem_colisao(self):
        for abaixada in (False, True):
            ambiente = self.criar_perto()
            ambiente.definir_abaixada(abaixada)
            for _ in range(40):
                ambiente.avancar(False)
            self.assertFalse(ambiente.fim_de_jogo)
            self.assertEqual(ambiente.personagem.bottom, CHAO_Y)

    def test_salto_desnecessario_colide_em_velocidades_inicial_e_maxima(self):
        for tempo in (0, 120):
            ambiente = self.criar_perto(tempo=tempo)
            ambiente.pular_manualmente()
            for _ in range(30):
                ambiente.avancar(False)
            self.assertTrue(ambiente.fim_de_jogo)

    def test_primeiros_desafios_e_reinicio_da_mistura(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        self.assertEqual(ambiente.tipo_obstaculo, "simples")

        def sequencia():
            return [(g.tipo, tuple(g.retangulo))
                    for g in (ambiente._sortear_obstaculo(900) for _ in range(80))]

        primeira = sequencia()
        self.assertEqual([tipo for tipo, _ in primeira[:2]], ["tunel", "passarinho"])
        self.assertTrue({"simples", "tunel", "passarinho"}.issubset({t for t, _ in primeira}))
        ambiente.reiniciar(123)
        self.assertEqual(sequencia(), primeira)
        treino = Ambiente(123)
        self.assertFalse(any(treino._sortear_obstaculo(900).tipo in ("tunel", "passarinho")
                             for _ in range(100)))

    def test_interpolacao_e_separacao_das_caixas(self):
        ambiente = self.criar_perto()
        ambiente.avancar(False)
        self.assertFalse(ambiente.caixas_visiveis)
        self.assertFalse(ambiente.tuneis_visiveis)
        original = ambiente.obstaculo.copy()
        retangulo = VistaAmbiente(ambiente, 0).passarinhos_visiveis[0]
        self.assertGreater(retangulo.x, original.x)
        self.assertEqual(retangulo.centery, PASSARINHO_CENTRO_Y)
        self.assertEqual(ambiente.obstaculo, original)

    def test_ha_percurso_viavel_na_mistura_inclusive_na_velocidade_maxima(self):
        for tempo in (0, 120):
            for semente in range(5):
                ambiente = Ambiente(semente, incluir_tuneis=True, incluir_passarinhos=True)
                ambiente.tempo_vivo = tempo
                for quadro in range(2400):
                    ambiente.definir_abaixada(ambiente.tipo_obstaculo == "tunel"
                                              and ambiente.distancia < 250)
                    if ambiente.tipo_obstaculo not in ("tunel", "passarinho"):
                        if ambiente.distancia < ambiente.velocidade * 0.20:
                            ambiente.pular_manualmente()
                    ambiente.avancar(False)
                    self.assertFalse(ambiente.fim_de_jogo, (tempo, semente, quadro, ambiente.tipo_obstaculo))

    def test_asas_animadas_desenho_e_congelamento(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            pygame.init()
            try:
                tela = pygame.display.set_mode((900, 400))
                quadros = criar_quadros()
                self.assertEqual({q.get_size() for q in quadros}, {(40, 32)})
                self.assertEqual(len({pygame.image.tobytes(q, "RGBA") for q in quadros}), 4)
                self.assertEqual([quadro_passarinho(d) for d in (0, 24, 48, 72, 96)], [0, 1, 2, 3, 0])
                ambiente = self.criar_perto()
                recursos = RecursosInterface()
                with patch("interface.apresentar"), patch("interface.desenhar_caixa") as caixa:
                    desenhar(tela, recursos, ambiente, SimpleNamespace(melhor_tempo=0), "humano")
                    caixa.assert_not_called()
                ambiente.fim_de_jogo = True
                distancia = ambiente.distancia_percorrida
                ambiente.avancar(False)
                self.assertEqual(ambiente.distancia_percorrida, distancia)
            finally:
                pygame.quit()
