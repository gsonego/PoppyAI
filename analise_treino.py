"""Agregação dos eventos e reprodução da campeã; sem alterar o aprendizado."""

from collections import Counter, deque
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path


def ler_eventos(caminho):
    eventos, ignoradas = [], 0
    caminho = Path(caminho)
    if not caminho.exists():
        return eventos, ignoradas
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        try:
            evento = json.loads(linha)
            if isinstance(evento, dict) and evento.get("schema") == 1:
                eventos.append(evento)
            else:
                ignoradas += 1
        except json.JSONDecodeError:
            # O relatório pode abrir enquanto a última linha está sendo gravada.
            ignoradas += 1
    return eventos, ignoradas


def resumir(eventos):
    geracoes, casos, colisoes, sessoes = {}, {}, [], []
    tentativas_vistas = set()
    for evento in eventos:
        tipo = evento.get("tipo")
        if tipo == "inicio_sessao":
            sessoes.append(evento)
        elif tipo == "geracao":
            chave = (evento["sessao"], evento["geracao"])
            geracoes[chave] = evento  # Último checkpoint/final desta tentativa de geração.
        elif tipo in ("encontro", "colisao"):
            obstaculo = evento["obstaculo"]
            chave = (evento["experimento"], evento["semente"], obstaculo["numero"],
                     obstaculo["tipo"], obstaculo["largura"], obstaculo["altura"], obstaculo["elevacao"])
            caso = casos.setdefault(chave, {"experimento": chave[0], "semente": chave[1],
                                           **obstaculo, "encontros": 0, "mortes": 0,
                                           "acoes": Counter(), "tempos": [], "conflitos": 0})
            tentativa = (evento["sessao"], evento["geracao"], evento["individuo"], chave, tipo)
            if tentativa in tentativas_vistas:
                continue
            tentativas_vistas.add(tentativa)
            if tipo == "encontro":
                caso["encontros"] += 1
            else:
                caso["mortes"] += 1
                caso["tempos"].append(evento["tempo"])
                acao = "abaixar" if evento["pediu_abaixar"] else "saltar" if evento["pediu_salto"] else "correr"
                caso["acoes"][acao] += 1
                caso["conflitos"] += bool(evento.get("conflito"))
                colisoes.append(evento)
    for caso in casos.values():
        caso["taxa"] = caso["mortes"] / caso["encontros"] if caso["encontros"] else None
    sem_recorde, anterior = 0, max((s.get("recorde_herdado") or 0 for s in sessoes[:1]), default=0)
    for geracao in geracoes.values():
        if geracao["concluida"]:
            sem_recorde = 0 if geracao["recorde"] > anterior + 1e-9 else sem_recorde + 1
            anterior = max(anterior, geracao["recorde"])
    return {"geracoes": list(geracoes.values()), "casos": list(casos.values()),
            "colisoes": colisoes, "sessoes": sessoes, "sem_recorde": sem_recorde}


def diagnosticar_campea(caminho, destino, limite=120):
    # Imports locais: a renderização dos gráficos pode usar outro Python com
    # Matplotlib instalado, sem precisar carregar Pygame nesse processo.
    from ambiente import Ambiente
    from campeao import VERSAO_EXPERIMENTO
    from config import CHAO_Y, PASSO
    from politica import MODELO, QUANTIDADE_PARAMETROS, aplicar_politica, calcular_saidas, observar

    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    pesos = dados.get("parametros", [])
    if (dados.get("experimento", {}).get("versao") != VERSAO_EXPERIMENTO
            or dados.get("modelo") != MODELO or len(pesos) != QUANTIDADE_PARAMETROS
            or any(type(p) not in (int, float) or not math.isfinite(p) for p in pesos)):
        raise ValueError("A campeã não corresponde ao modelo e às regras atuais.")
    semente = dados["experimento"]["semente_treino"]
    ambiente = Ambiente(semente, incluir_tuneis=True, incluir_passarinhos=True, incluir_pedras=True)
    trace, estados = deque(maxlen=180), deque(maxlen=61)
    while not ambiente.fim_de_jogo and ambiente.tempo_vivo < limite:
        estados.append(deepcopy(ambiente))
        z_salto, z_baixo = calcular_saidas(observar(ambiente), pesos)
        trace.append({"tempo": ambiente.tempo_vivo, "distancia": ambiente.distancia,
                      "numero": ambiente._alvo.numero, "tipo": ambiente.tipo_obstaculo,
                      "base_obstaculo": ambiente.elevacao_obstaculo,
                      "topo_obstaculo": ambiente.elevacao_obstaculo + ambiente.obstaculo.height,
                      "topo_poppy": CHAO_Y - ambiente.personagem.top,
                      "pes_poppy": CHAO_Y - ambiente.personagem.bottom,
                      "abaixada": ambiente.abaixada, "z_salto": z_salto, "z_abaixar": z_baixo})
        aplicar_politica(ambiente, pesos)
    atingido = ambiente.grupo_colisao
    alternativa = None
    if atingido is not None:
        # Busca física limitada de um salto a partir do mesmo estado anterior.
        # Não altera pesos, semente, pontuação ou arquivo da campeã.
        inicio = estados[0]
        for atraso in range(61):
            tentativa = deepcopy(inicio)
            alvo = next((g for g in tentativa.grupos if g.numero == atingido.numero), None)
            for passo in range(180):
                tentativa.definir_abaixada(False)
                tentativa.avancar(passo == atraso)
                if alvo is None:
                    alvo = next((g for g in tentativa.grupos if g.numero == atingido.numero), None)
                if tentativa.fim_de_jogo:
                    break
                if alvo is not None and alvo.retangulo.right <= tentativa.personagem.left:
                    alternativa = {"acao": "saltar", "instante": inicio.tempo_vivo + atraso * PASSO,
                                   "passou_em": tentativa.tempo_vivo}
                    break
            if alternativa:
                break
    resultado = {"experimento": VERSAO_EXPERIMENTO, "semente": semente,
                 "registrado_em": datetime.now(timezone.utc).isoformat(),
                 "geracao_salva": dados.get("geracao"), "recorde_salvo": dados["tempo_segundos"],
                 "politica": sha256(json.dumps(tuple(pesos)).encode()).hexdigest()[:16],
                 "tempo_reproduzido": ambiente.tempo_vivo, "limite_analise": limite,
                 "obstaculo": ambiente.descrever_grupo(atingido) if atingido else None,
                 "anterior": atingido.anterior if atingido else None,
                 "alternativa_encontrada": alternativa, "trace": list(trace)}
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(destino)
    return resultado
