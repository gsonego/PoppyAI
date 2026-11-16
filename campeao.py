"""Persistência da melhor política, sem salvar o estado da busca aleatória."""

import json
import math
from pathlib import Path


# Incremente se mudar a física, observação, política ou geração de obstáculos.
VERSAO_EXPERIMENTO = 2


def carregar_campeao(caminho, limite, semente):
    caminho = Path(caminho)
    if not caminho.exists():
        return None

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict) or dados.get("experimento") != {
        "versao": VERSAO_EXPERIMENTO,
        "limite_segundos": limite,
        "semente_treino": semente,
    }:
        raise ValueError("A campeã salva pertence a outro experimento.")

    valores = [dados.get(chave) for chave in (
        "peso_distancia", "peso_altura", "vies", "tempo_segundos",
    )]
    if any(
        type(valor) not in (int, float) or not math.isfinite(valor)
        for valor in valores
    ):
        raise ValueError("A campeã salva contém parâmetros ou tempo inválidos.")
    peso_distancia, peso_altura, vies, tempo = valores
    if not 0 <= tempo <= limite:
        raise ValueError("O tempo salvo está fora do limite do experimento.")
    return (peso_distancia, peso_altura, vies), tempo


def salvar_campeao(caminho, parametros, tempo, limite, semente):
    caminho = Path(caminho)
    dados = {
        "experimento": {
            "versao": VERSAO_EXPERIMENTO,
            "limite_segundos": limite,
            "semente_treino": semente,
        },
        "peso_distancia": parametros[0],
        "peso_altura": parametros[1],
        "vies": parametros[2],
        "tempo_segundos": tempo,
    }
    # Substituir somente após escrever evita truncar o recorde anterior.
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporario.replace(caminho)
