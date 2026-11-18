"""Coleta fiel ao jogo, agregação das tentativas e relatório fora da simulação."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from analise_treino import diagnosticar_campea, ler_eventos, resumir
from campeao import salvar_campeao
from config import SEMENTE_TREINO
from geracoes import TreinoGeracoes
from metricas import GravadorMetricas


class TestMetricas(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)

    def criar_treino(self, registrar=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return TreinoGeracoes(self.pasta / "campeao.json", tamanho=4,
                                  salvar=lambda *args: None, registrar=registrar)

    def test_coleta_nao_muda_simulacao_ou_sorteio(self):
        eventos = []
        com, sem = self.criar_treino(eventos.append), self.criar_treino()
        with contextlib.redirect_stdout(io.StringIO()):
            for _ in range(900):
                com.avancar()
                sem.avancar()
        self.assertEqual(com.geracao, sem.geracao)
        self.assertEqual(com.sorteio.getstate(), sem.sorteio.getstate())
        self.assertEqual(com.melhores_parametros, sem.melhores_parametros)
        self.assertEqual(com.melhor_tempo, sem.melhor_tempo)
        for a, b in zip(com.individuos, sem.individuos):
            self.assertEqual(a.parametros, b.parametros)
            self.assertEqual(a.ambiente.personagem, b.ambiente.personagem)
            self.assertEqual(a.ambiente.tempo_vivo, b.ambiente.tempo_vivo)
        mortes = [e for e in eventos if e["tipo"] == "colisao"]
        self.assertTrue(mortes)
        chaves = [(e["geracao"], e["individuo"]) for e in mortes]
        self.assertEqual(len(chaves), len(set(chaves)))
        for morte in mortes:
            self.assertTrue(any(e["tipo"] == "encontro" and e["geracao"] == morte["geracao"]
                                and e["individuo"] == morte["individuo"]
                                and e["obstaculo"] == morte["obstaculo"] for e in eventos))

    def test_conflito_e_entradas_sao_os_do_quadro_da_decisao(self):
        eventos = []
        treino = self.criar_treino(eventos.append)
        # Duas saídas sempre ativas: prioridade de abaixar, sem saltar.
        pesos = (0,) * 28 + (1,) + (0,) * 4 + (1,)
        treino._criar_individuos([pesos] * 4)
        while treino.vivos:
            treino.avancar()
        mortes = [e for e in eventos if e["tipo"] == "colisao"]
        self.assertEqual(len(mortes), 4)
        for e in mortes:
            self.assertTrue(e["conflito"])
            self.assertFalse(e["pediu_salto"])
            self.assertTrue(e["pediu_abaixar"])
            self.assertEqual(e["saida_salto"], 1)
            self.assertEqual(e["saida_abaixar"], 1)
            self.assertEqual(len(e["entradas"]), 5)
            self.assertEqual(e["obstaculo"]["numero"], 1)
        conclusoes = [e for e in eventos if e["tipo"] == "geracao"]
        self.assertEqual(len(conclusoes), 1)
        self.assertTrue(conclusoes[0]["concluida"])
        treino.finalizar_registro()
        self.assertEqual(len([e for e in eventos if e["tipo"] == "geracao"]), 1)

    def test_checkpoint_substituido_e_sobreviventes_nao_sao_mortes(self):
        eventos = []
        treino = self.criar_treino(eventos.append)
        treino.registrar_geracao("grafico", definitiva=False)
        treino.registrar_geracao("grafico", definitiva=False)
        with contextlib.redirect_stdout(io.StringIO()):
            treino.proxima_geracao()
        treino.finalizar_registro()
        resumo = resumir(eventos)
        self.assertEqual(len(resumo["geracoes"]), 2)
        self.assertEqual(resumo["geracoes"][0]["motivo"], "antecipada")
        self.assertEqual(resumo["geracoes"][0]["mortos"], 0)
        self.assertFalse(resumo["geracoes"][0]["concluida"])
        self.assertEqual(resumo["colisoes"], [])
        self.assertEqual(resumo["sem_recorde"], 0)

    def test_taxa_distingue_sementes_sessoes_e_nao_duplica_eventos(self):
        base = {"schema": 1, "experimento": 12, "semente": 123, "sessao": "a", "geracao": 140,
                "individuo": 1, "tempo": 62.95, "pediu_salto": False, "pediu_abaixar": True,
                "conflito": True, "obstaculo": {"numero": 44, "tipo": "empilhadas",
                    "largura": 40, "altura": 72, "elevacao": 0}}
        encontro = dict(base, tipo="encontro")
        morte = dict(base, tipo="colisao")
        eventos = [encontro, morte, encontro, morte, dict(encontro, individuo=2),
                   dict(encontro, sessao="b"), dict(morte, sessao="b"),
                   dict(encontro, semente=456), dict(morte, semente=456)]
        resumo = resumir(eventos)
        self.assertEqual(len(resumo["casos"]), 2)
        caso = resumo["casos"][0]
        self.assertEqual((caso["encontros"], caso["mortes"]), (3, 2))
        self.assertAlmostEqual(caso["taxa"], 2 / 3)
        self.assertEqual(caso["conflitos"], 2)
        self.assertEqual(caso["acoes"]["abaixar"], 2)

    def test_fila_preserva_todos_eventos_e_flush_antes_do_grafico(self):
        caminho = self.pasta / "treino.jsonl"
        vistos = []
        with patch.object(GravadorMetricas, "_abrir_graficos",
                          lambda gravador: vistos.append(len(ler_eventos(gravador.caminho)[0]))):
            gravador = GravadorMetricas(caminho, self.pasta / "campeao.json")
            for i in range(100):
                e = {"schema": 1, "numero": i, "dados": [i]}
                gravador.agendar(e)
                e["dados"].append("alterado")
            gravador.solicitar_graficos()
            gravador.fechar()
            gravador.fechar()
        eventos, ignoradas = ler_eventos(caminho)
        self.assertEqual(vistos, [100])
        self.assertEqual(ignoradas, 0)
        self.assertEqual([e["numero"] for e in eventos], list(range(100)))
        self.assertEqual(eventos[-1]["dados"], [99])

    def test_falha_de_gravacao_nao_derruba_jogo_e_linha_parcial_e_ignorada(self):
        bloqueado = self.pasta / "arquivo"
        bloqueado.write_text("nao e uma pasta")
        with patch("metricas.registro.exception"):
            gravador = GravadorMetricas(bloqueado / "treino.jsonl", self.pasta / "campeao.json")
            gravador.agendar({"schema": 1})
            gravador.fechar()
        self.assertIsInstance(gravador.erro, OSError)
        caminho = self.pasta / "parcial.jsonl"
        caminho.write_text('{"schema":1}\n{"schema":', encoding="utf-8")
        self.assertEqual(ler_eventos(caminho), ([{"schema": 1}], 1))

    def test_relatorio_com_eventos_reais_e_diagnostico_sem_alterar_campea(self):
        eventos = []
        treino = self.criar_treino(eventos.append)
        pesos = (0,) * 28 + (1,) + (0,) * 4 + (1,)
        treino._criar_individuos([pesos] * 4)
        while treino.vivos:
            treino.avancar()
        campeao = self.pasta / "campeao.json"
        salvar_campeao(campeao, pesos, treino.melhor_tempo, None, SEMENTE_TREINO, 140)
        antes = campeao.read_bytes()
        diagnostico = diagnosticar_campea(campeao, self.pasta / "diag.json", limite=10)
        self.assertEqual(campeao.read_bytes(), antes)
        self.assertEqual(diagnostico["obstaculo"]["numero"], 1)
        self.assertIsNotNone(diagnostico["alternativa_encontrada"])
        caminho = self.pasta / "treino.jsonl"
        caminho.write_text("".join(json.dumps(e) + "\n" for e in eventos), encoding="utf-8")
        saida = self.pasta / "graficos"
        ambiente = dict(os.environ, MPLCONFIGDIR=str(self.pasta / "matplotlib"))
        resultado = subprocess.run([sys.executable, "relatorio_treino.py", "--arquivo", str(caminho),
                                   "--campeao", str(campeao), "--saida", str(saida)],
                                  capture_output=True, text=True, env=ambiente, timeout=60,
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        for nome in ("treinamento.png", "diagnostico_campea.png", "relatorio.html",
                     "geracoes.csv", "colisoes_por_obstaculo.csv"):
            self.assertGreater((saida / nome).stat().st_size, 50)
        self.assertIn("as duas saídas estavam ativas", (saida / "relatorio.html").read_text(encoding="utf-8"))
        self.assertEqual(campeao.read_bytes(), antes)
