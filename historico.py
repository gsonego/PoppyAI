"""Resumo dos resultados dos experimentos, sem guardar arquivos de pesos antigos."""

from datetime import datetime, timezone
import json
import math
from pathlib import Path


def registrar_resultado(caminho_campeao, campeao):
    experimento = campeao.get("experimento") if isinstance(campeao, dict) else None
    if not isinstance(experimento, dict) or type(experimento.get("versao")) is not int:
        raise ValueError("A campeã anterior não identifica um experimento válido.")
    tempo = campeao.get("tempo_segundos")
    if type(tempo) not in (int, float) or not math.isfinite(tempo) or tempo < 0:
        raise ValueError("O resultado do experimento anterior contém um tempo inválido.")
    geracao = campeao.get("geracao")
    if geracao is not None and (type(geracao) is not int or geracao < 1):
        raise ValueError("O resultado do experimento anterior contém uma geração inválida.")

    caminho = Path(caminho_campeao).with_name("historico_experimentos.json")
    historico = []
    if caminho.exists():
        historico = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(historico, list) or any(not isinstance(item, dict) for item in historico):
            raise ValueError("O histórico de experimentos contém dados inválidos.")
    resultado = {"experimento": experimento, "tempo_segundos": tempo, "geracao_final": geracao}
    for indice, anterior in enumerate(historico):
        if anterior.get("experimento") == experimento:
            # Se a gravação da nova campeã falhou, repetir não duplica o registro.
            if all(anterior.get(chave) == valor for chave, valor in resultado.items()):
                return
            historico[indice] = resultado
            break
    else:
        historico.append(resultado)
    resultado["encerrado_em"] = datetime.now(timezone.utc).isoformat()
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(historico, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                          encoding="utf-8")
    temporario.replace(caminho)
