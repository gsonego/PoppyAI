"""Persistência da campeã e da contagem de gerações do experimento."""

import json
import math
from pathlib import Path
from threading import Condition, Thread

from historico import registrar_resultado
from politica import MODELO, QUANTIDADE_PARAMETROS


# Incremente se mudar a física, observação, política ou geração de obstáculos.
VERSAO_EXPERIMENTO = 12


class GravadorCampeao:
    """Uma única thread grava no disco, mantendo só o pedido mais recente na fila."""

    def __init__(self):
        self._condicao = Condition()
        self._pendente = None
        self._erro = None
        self._fechado = False
        self._thread = None

    def verificar_erro(self):
        with self._condicao:
            erro = self._erro
        if erro is not None:
            raise OSError(f"Não foi possível salvar a campeã: {erro}") from erro

    def agendar(self, caminho, parametros, tempo, limite, semente, geracao=1):
        with self._condicao:
            self.verificar_erro()
            if self._fechado:
                raise RuntimeError("O gravador já foi fechado.")
            # Copia os parâmetros: o treino pode trocar de candidata antes da gravação.
            self._pendente = (Path(caminho), tuple(parametros), tempo, limite, semente, geracao)
            if self._thread is None:
                self._thread = Thread(target=self._gravar, name="salvar-campeao", daemon=True)
                self._thread.start()
            self._condicao.notify()

    def _gravar(self):
        while True:
            with self._condicao:
                self._condicao.wait_for(lambda: self._pendente is not None or self._fechado)
                if self._pendente is None:
                    return
                pedido = self._pendente
                self._pendente = None
            try:
                salvar_campeao(*pedido)
            except Exception as erro:
                with self._condicao:
                    self._erro = erro
                    self._pendente = None
                return

    def fechar(self):
        """Espera a última gravação antes de encerrar o programa."""
        with self._condicao:
            self._fechado = True
            self._condicao.notify()
        if self._thread is not None:
            self._thread.join()
        self.verificar_erro()


def carregar_campeao(caminho, limite, semente, *, incluir_geracao=False, novo_experimento=False):
    caminho = Path(caminho)
    if not caminho.exists():
        return None

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if (novo_experimento and isinstance(dados, dict)
            and isinstance(dados.get("experimento"), dict)
            and type(dados["experimento"].get("versao")) is int
            and dados["experimento"]["versao"] != VERSAO_EXPERIMENTO):
        return None
    experimento_atual = {
        "versao": VERSAO_EXPERIMENTO,
        "limite_segundos": limite,
        "semente_treino": semente,
    }
    # A política e a física são iguais: preserva os tempos já alcançados
    # pelas campeãs anteriores, mesmo que tenham parado no antigo teto de 30 s.
    experimento_anterior = {**experimento_atual, "limite_segundos": 30.0}
    if not isinstance(dados, dict) or not (
        dados.get("experimento") == experimento_atual
        or (limite is None and dados.get("experimento") == experimento_anterior)
    ):
        raise ValueError("A campeã salva pertence a outro experimento.")

    parametros = dados.get("parametros")
    if (dados.get("modelo") != MODELO or not isinstance(parametros, list)
            or len(parametros) != QUANTIDADE_PARAMETROS):
        raise ValueError("A campeã salva não contém a rede 5/4/2 completa.")
    valores = parametros + [dados.get("tempo_segundos")]
    if any(
        type(valor) not in (int, float) or not math.isfinite(valor)
        for valor in valores
    ):
        raise ValueError("A campeã salva contém parâmetros ou tempo inválidos.")
    tempo = valores[-1]
    limite_salvo = dados["experimento"]["limite_segundos"]
    if tempo < 0 or (limite_salvo is not None and tempo > limite_salvo):
        raise ValueError("O tempo salvo está fora do limite do experimento.")
    geracao = dados.get("geracao", 1)
    if type(geracao) is not int or geracao < 1:
        raise ValueError("A geração salva deve ser um inteiro positivo.")
    campeao = (tuple(parametros), tempo)
    return (*campeao, geracao) if incluir_geracao else campeao


def salvar_campeao(caminho, parametros, tempo, limite, semente, geracao=1):
    if type(geracao) is not int or geracao < 1:
        raise ValueError("A geração salva deve ser um inteiro positivo.")
    if len(parametros) != QUANTIDADE_PARAMETROS or any(
        type(valor) not in (int, float) or not math.isfinite(valor) for valor in parametros
    ):
        raise ValueError("A campeã exige 34 pesos e vieses finitos.")
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "experimento": {
            "versao": VERSAO_EXPERIMENTO,
            "limite_segundos": limite,
            "semente_treino": semente,
        },
        "modelo": MODELO,
        "parametros": list(parametros),
        "tempo_segundos": tempo,
        "geracao": geracao,
    }
    # Registra o resultado anterior antes de substituir seu único arquivo de pesos.
    # Se o histórico falhar, a campeã antiga permanece intacta para uma nova tentativa.
    if caminho.exists():
        anterior = json.loads(caminho.read_text(encoding="utf-8"))
        experimento_anterior = anterior.get("experimento") if isinstance(anterior, dict) else None
        if (isinstance(experimento_anterior, dict)
                and experimento_anterior.get("versao") != VERSAO_EXPERIMENTO):
            registrar_resultado(caminho, anterior)
    # Substituir somente após escrever evita truncar o recorde anterior.
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho)
