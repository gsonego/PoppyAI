"""A pedra permite corrida normal e salto; só o focinho abaixado colide."""

import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from ambiente import Ambiente
from apresentacao import VistaAmbiente
from config import CHAO_Y, PEDRA_ALTURA, PEDRA_LARGURA
from humano import JogoHumano
from interface import RecursosInterface, desenhar
import main
from tests.apoio import RelogioTeste


class TestPedra(unittest.TestCase):
    @staticmethod
    def criar_perto(x=225):
        ambiente = Ambiente(123, incluir_pedras=True)
        pedra = ambiente._sortear_obstaculo(x)
        ambiente.grupos = [pedra]
        ambiente._alvo = pedra
        return ambiente, pedra

    def test_em_pe_passa_sem_mudar_altura_ou_velocidade_vertical(self):
        for tempo in (0, 120):
            ambiente, pedra = self.criar_perto()
            ambiente.tempo_vivo = tempo
            viu_sobreposicao = False
            altura_inicial = ambiente.posicao_y
            for _ in range(40):
                ambiente.avancar(False)
                viu_sobreposicao |= ambiente.personagem.colliderect(pedra.retangulo)
                self.assertFalse(ambiente.fim_de_jogo)
                self.assertEqual(ambiente.posicao_y, altura_inicial)
                self.assertEqual(ambiente.velocidade_y, 0)
                self.assertEqual(ambiente.personagem.bottom, CHAO_Y)
                self.assertTrue(ambiente.no_chao)
            self.assertTrue(viu_sobreposicao)

    def test_abaixada_bate_o_focinho(self):
        for tempo in (0, 120):
            ambiente, _ = self.criar_perto()
            ambiente.tempo_vivo = tempo
            ambiente.definir_abaixada(True)
            for _ in range(30):
                ambiente.avancar(False)
            self.assertTrue(ambiente.fim_de_jogo)

    def test_levantar_antes_da_pedra_e_abaixar_depois_do_focinho_passar(self):
        ambiente, pedra = self.criar_perto(180)
        ambiente.definir_abaixada(True)
        ambiente.avancar(False)
        self.assertFalse(ambiente.fim_de_jogo)
        ambiente.definir_abaixada(False)
        while pedra.retangulo.right > ambiente.personagem.right - 12:
            ambiente.avancar(False)
        self.assertGreater(pedra.retangulo.right, ambiente.personagem.left)
        ambiente.definir_abaixada(True)
        ambiente.avancar(False)
        self.assertFalse(ambiente.fim_de_jogo)

    def test_salto_tambem_passa(self):
        ambiente, _ = self.criar_perto()
        ambiente.pular_manualmente()
        for _ in range(40):
            ambiente.avancar(False)
        self.assertFalse(ambiente.fim_de_jogo)

    def test_apresentacao_repetivel_e_pedras_ausentes_sem_opcao(self):
        ambiente = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)

        def sequencia():
            return [(g.tipo, tuple(g.retangulo))
                    for g in (ambiente._sortear_obstaculo(900) for _ in range(80))]

        primeira = sequencia()
        self.assertEqual([tipo for tipo, _ in primeira[:3]], ["pedra", "tunel", "passarinho"])
        self.assertGreater([tipo for tipo, _ in primeira].count("pedra"), 1)
        ambiente.reiniciar(123)
        self.assertEqual(sequencia(), primeira)
        ia = Ambiente(123, incluir_tuneis=True, incluir_passarinhos=True)
        self.assertNotIn("pedra", [ia._sortear_obstaculo(900).tipo for _ in range(100)])

    def test_interpolacao_e_sprite_da_pedra(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}):
            pygame.init()
            try:
                tela = pygame.display.set_mode((900, 400))
                ambiente, pedra = self.criar_perto()
                ambiente.avancar(False)
                original = pedra.retangulo.copy()
                self.assertGreater(VistaAmbiente(ambiente, 0).pedras_visiveis[0].x, original.x)
                self.assertFalse(any(c.colliderect(pedra.retangulo) for c in ambiente.caixas_visiveis))
                recursos = RecursosInterface()
                self.assertEqual(recursos.pedra.get_size(), (PEDRA_LARGURA, PEDRA_ALTURA))
                with patch("interface.apresentar"), patch("interface.desenhar_caixa") as caixa:
                    desenhar(tela, recursos, ambiente, SimpleNamespace(melhor_tempo=0), "humano")
                    self.assertEqual(caixa.call_count, len(ambiente.caixas_visiveis))
                self.assertEqual(pedra.retangulo, original)
            finally:
                pygame.quit()

    def test_humano_e_avaliacao_habilitam_pedras(self):
        with patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}), \
                tempfile.TemporaryDirectory() as pasta:
            for modo in ("humano", "avaliacao"):
                with patch("main.JogoHumano", return_value=JogoHumano(Path(pasta) / "recorde.json")), \
                        patch("main.Avaliacao", return_value=SimpleNamespace(semente=456)), \
                        patch("main.Ambiente", wraps=Ambiente) as criar, \
                        patch("main.RelogioQuadros", RelogioTeste), \
                        patch("main.pygame.event.get", return_value=[pygame.event.Event(pygame.QUIT)]):
                    main.main(modo)
                self.assertTrue(criar.call_args.kwargs["incluir_pedras"])
