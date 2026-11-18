"""Gera PNG, CSV e relatório HTML local a partir das métricas reais do treino."""

import argparse
from collections import Counter
import csv
from html import escape
import json
import os
from pathlib import Path
import subprocess
import sys

from analise_treino import diagnosticar_campea, ler_eventos, resumir
from campeao import VERSAO_EXPERIMENTO
from config import ARQUIVO_CAMPEAO, PASTA_TREINOS

CORES = {"simples": "#bd8b53", "lado_a_lado": "#94704a", "empilhadas": "#705640",
         "tunel": "#677588", "pedra": "#d4768a", "passarinho": "#4e9cbd"}


def nome_caso(caso):
    return f"#{caso['numero']} {caso['tipo']} ({caso['largura']}×{caso['altura']})"


def salvar_figura(figura, caminho, plt):
    temporario = caminho.with_suffix(".png.tmp")
    figura.savefig(temporario, format="png", dpi=150, facecolor="white")
    plt.close(figura)
    temporario.replace(caminho)


def gerar_relatorio(arquivo, pasta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    eventos, ignoradas = ler_eventos(arquivo)
    resumo = resumir(eventos)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    geracoes, casos = resumo["geracoes"], resumo["casos"]
    fig, eixos = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    fig.suptitle("PoppyAI · evolução e gargalos do treino", fontsize=19, weight="bold")
    ax = eixos[0, 0]
    if geracoes:
        x = list(range(len(geracoes)))
        for chave, nome, cor in (("melhor_tempo", "Melhor da geração", "#448c65"),
                                 ("mediana", "Mediana da população", "#519ab5"),
                                 ("recorde", "Recorde salvo", "#cc6983")):
            ax.plot(x, [g[chave] for g in geracoes], ".-", label=nome, color=cor)
        parciais = [i for i, g in enumerate(geracoes) if not g["concluida"]]
        if parciais:
            ax.scatter(parciais, [geracoes[i]["melhor_tempo"] for i in parciais], marker="x",
                       s=90, color="#493b45", label="Parcial / encerrada cedo", zorder=4)
        ticks = sorted({round(i * (len(x) - 1) / min(9, max(1, len(x) - 1)))
                        for i in range(min(10, len(x)))})
        ax.set_xticks(ticks, [str(geracoes[i]["geracao"]) for i in ticks])
        ax.legend(fontsize=8)
    else:
        ax.text(.5, .5, "Sem gerações registradas ainda.\nRetome o treino e pressione G.", ha="center", transform=ax.transAxes)
    ax.set(title="Progresso — gerações efetivamente registradas", xlabel="Geração (ordem de registro)", ylabel="Tempo vivo (s)")
    ax.grid(alpha=.15)

    ax = eixos[0, 1]
    frequentes = sorted((c for c in casos if c["mortes"]), key=lambda c: c["mortes"], reverse=True)[:10]
    if frequentes:
        ax.barh([nome_caso(c) for c in frequentes][::-1], [c["mortes"] for c in frequentes][::-1], color="#cc6983")
    else:
        ax.text(.5, .5, "Ainda não há colisões coletadas.", ha="center", transform=ax.transAxes)
    ax.set(title="Onde mais morrem", xlabel="Colisões (tentativas, incluindo elites repetidas)")

    ax = eixos[1, 0]
    indices = {(g["sessao"], g["geracao"]): i for i, g in enumerate(geracoes)}
    for tipo, cor in CORES.items():
        mortes = [c for c in resumo["colisoes"] if c["obstaculo"]["tipo"] == tipo]
        if mortes:
            # A geração atual pode ter colisões, mas ainda não ter checkpoint.
            for c in mortes:
                indices.setdefault((c["sessao"], c["geracao"]), len(indices))
            ax.scatter([indices[(c["sessao"], c["geracao"])] for c in mortes],
                       [c["tempo"] for c in mortes], s=13, alpha=.45, color=cor, label=tipo)
    ax.set(title="Tempo de cada colisão — faixas horizontais indicam gargalos", xlabel="Tentativa de geração registrada", ylabel="Tempo vivo (s)")
    if resumo["colisoes"]:
        ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=.15)

    ax = eixos[1, 1]
    dificeis = sorted((c for c in casos if c["encontros"] >= 5 and c["mortes"]),
                       key=lambda c: (c["taxa"], c["mortes"]), reverse=True)[:10]
    if dificeis:
        labels = [f"{nome_caso(c)} · {c['mortes']}/{c['encontros']}" for c in dificeis]
        ax.barh(labels[::-1], [c["taxa"] * 100 for c in dificeis][::-1], color="#677588")
        ax.set_xlim(0, 105)
    else:
        ax.text(.5, .5, "Aguarde ao menos 5 encontros\ncom o mesmo obstáculo.", ha="center", transform=ax.transAxes)
    ax.set(title="Falhas entre quem chegou ao obstáculo", xlabel="Colisões / encontros (%)")
    salvar_figura(fig, pasta / "treinamento.png", plt)

    diagnostico_path = pasta / "diagnostico_campea.json"
    diagnostico = json.loads(diagnostico_path.read_text(encoding="utf-8")) if diagnostico_path.exists() else {}
    if diagnostico.get("trace"):
        trace = diagnostico["trace"]
        fig, eixos = plt.subplots(3, 1, figsize=(12, 9), sharex=True, constrained_layout=True)
        obstaculo = diagnostico.get("obstaculo")
        titulo = (f"Colisão em {diagnostico['tempo_reproduzido']:.2f} s · {nome_caso(obstaculo)}"
                  if obstaculo else f"Sem colisão até {diagnostico['tempo_reproduzido']:.2f} s")
        fig.suptitle("Diagnóstico da campeã atual\n" + titulo, fontsize=16, weight="bold")
        t = [p["tempo"] for p in trace]
        eixos[0].plot(t, [p["z_salto"] for p in trace], color="#448c65", label="Saída salto (antes do degrau)")
        eixos[0].plot(t, [p["z_abaixar"] for p in trace], color="#cc6983", label="Saída abaixar (antes do degrau)")
        eixos[0].axhline(0, color="#493b45", lw=.8)
        eixos[0].set_ylabel("Valor da saída")
        eixos[0].legend(fontsize=9)
        eixos[1].fill_between(t, [p["base_obstaculo"] for p in trace], [p["topo_obstaculo"] for p in trace],
                              alpha=.25, color="#bd8b53", label="Faixa vertical do alvo")
        eixos[1].plot(t, [p["topo_poppy"] for p in trace], color="#519ab5", label="Topo da colisão da Poppy")
        eixos[1].plot(t, [p["pes_poppy"] for p in trace], color="#493b45", label="Pés da Poppy")
        eixos[1].set_ylabel("Altura acima do chão (px)")
        eixos[1].legend(fontsize=9)
        eixos[2].plot(t, [p["distancia"] for p in trace], color="#677588", label="Distância até a frente do alvo")
        eixos[2].axhline(0, color="#493b45", lw=.8)
        eixos[2].set(xlabel="Tempo de partida (s)", ylabel="Distância (px)")
        eixos[2].legend(fontsize=9)
        alternativa = diagnostico.get("alternativa_encontrada")
        if alternativa:
            for ax in eixos:
                ax.axvline(alternativa["instante"], color="#448c65", ls="--", alpha=.7)
            eixos[2].text(.02, .05, f"Busca física encontrou passagem saltando em {alternativa['instante']:.2f} s.",
                          transform=eixos[2].transAxes, color="#277047")
        for ax in eixos:
            ax.grid(alpha=.15)
        salvar_figura(fig, pasta / "diagnostico_campea.png", plt)

    colunas = ("experimento", "semente", "numero", "tipo", "largura", "altura", "elevacao", "encontros", "mortes", "taxa", "conflitos")
    with (pasta / "colisoes_por_obstaculo.csv").open("w", encoding="utf-8-sig", newline="") as arquivo_csv:
        escritor = csv.DictWriter(arquivo_csv, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(casos)
    with (pasta / "geracoes.csv").open("w", encoding="utf-8-sig", newline="") as arquivo_csv:
        colunas_g = ("sessao", "geracao", "concluida", "motivo", "total", "vivos", "mortos", "melhor_tempo", "mediana", "recorde")
        escritor = csv.DictWriter(arquivo_csv, fieldnames=colunas_g, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(geracoes)
    linhas = "".join(f"<tr><td>{escape(nome_caso(c))}</td><td>{c['semente']}</td><td>{c['mortes']}</td>"
                     f"<td>{c['encontros']}</td><td>{c['taxa']:.1%}</td><td>{c['conflitos']}</td><td>{escape(str(dict(c['acoes'])))}</td></tr>"
                     for c in sorted(casos, key=lambda c: c["mortes"], reverse=True) if c["taxa"] is not None)
    inicio = min((e["geracao"] for e in eventos if "geracao" in e), default=None)
    nota = (f"Coleta disponível a partir da geração {inicio}. As gerações anteriores não foram reconstruídas."
            if inicio is not None else "Ainda não há histórico de gerações. Retome o jogo e pressione G no treino.")
    texto_diag = escape(diagnostico.get("erro", ""))
    if diagnostico.get("obstaculo"):
        alternativa = diagnostico.get("alternativa_encontrada")
        texto_diag = (f"A campeã foi reproduzida até a colisão em {diagnostico['tempo_reproduzido']:.2f} s. "
                      + ("Uma busca física encontrou um salto que passa por esse obstáculo."
                         if alternativa else "A busca limitada não encontrou um salto alternativo; isso não prova impossibilidade."))
        ultimo = diagnostico["trace"][-1]
        if ultimo["z_salto"] > 0 and ultimo["z_abaixar"] > 0:
            texto_diag += " No quadro anterior ao impacto, as duas saídas estavam ativas; a prioridade de abaixar bloqueou o salto."
    img_diag = '<img src="diagnostico_campea.png" alt="Diagnóstico da campeã">' if diagnostico.get("trace") else ""
    html = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>PoppyAI · treino</title>
<style>body{{font:16px system-ui;color:#303c48;background:#f7f9fa;max-width:1400px;margin:40px auto;padding:0 24px}}
h1{{color:#37694e}}img{{width:100%;background:white;border-radius:8px;margin:12px 0 30px}}table{{border-collapse:collapse;width:100%;background:white}}
td,th{{padding:10px;border-bottom:1px solid #dde3e7;text-align:left}}.nota{{background:#fff3d9;padding:18px;border-radius:8px}}</style>
<h1>PoppyAI · evolução e gargalos</h1><p class="nota">{nota}</p>
<p>{len(resumo['colisoes'])} colisões · {len(casos)} obstáculos · {len(geracoes)} tentativas de geração registradas.
{resumo['sem_recorde']} gerações concluídas registradas sem novo recorde desde a última melhora observada.</p>
<p>Parciais e avanços com N incluem sobreviventes e são limites inferiores de tempo. Retomar uma geração cria outra tentativa.
Os encontros são contatos horizontais com o obstáculo; a taxa mede quem morreu entre quem chegou. Elites repetidas contam como novas tentativas.</p>
<img src="treinamento.png" alt="Evolução e frequência das colisões"><h2>Campeã atual</h2><p>{texto_diag}</p>{img_diag}
<h2>Obstáculos observados</h2><table><tr><th>Obstáculo</th><th>Semente</th><th>Mortes</th><th>Encontros</th><th>Taxa</th><th>Saídas em conflito</th><th>Comandos no impacto</th></tr>{linhas}</table>
<p>{ignoradas} linhas incompletas ou incompatíveis ignoradas. Dados: <a href="geracoes.csv">gerações CSV</a> ·
<a href="colisoes_por_obstaculo.csv">colisões CSV</a>. Gráficos de frequência não demonstram impossibilidade física.</p></html>'''
    destino = pasta / "relatorio.html"
    temporario = destino.with_suffix(".html.tmp")
    temporario.write_text(html, encoding="utf-8")
    temporario.replace(destino)
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, default=PASTA_TREINOS / f"experimento_{VERSAO_EXPERIMENTO}.jsonl")
    parser.add_argument("--campeao", type=Path, default=ARQUIVO_CAMPEAO)
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--abrir", action="store_true")
    parser.add_argument("--sem-diagnostico", action="store_true", help="Usa a reprodução já salva, sem executar a campeã novamente.")
    args = parser.parse_args()
    pasta = args.saida or args.arquivo.with_suffix("")
    pasta.mkdir(parents=True, exist_ok=True)
    if not args.sem_diagnostico:
        try:
            diagnosticar_campea(args.campeao, pasta / "diagnostico_campea.json")
        except (OSError, ValueError, KeyError, ImportError) as erro:
            (pasta / "diagnostico_campea.json").write_text(json.dumps({"erro": str(erro)}), encoding="utf-8")
    try:
        destino = gerar_relatorio(args.arquivo, pasta)
    except ModuleNotFoundError as erro:
        base = Path(getattr(sys, "_base_executable", sys.executable))
        if base.resolve() == Path(sys.executable).resolve():
            raise SystemExit("Instale as dependências opcionais: python -m pip install -r requirements-analise.txt") from erro
        # Aproveita o Matplotlib já instalado no Python-base sem adicionar
        # suas bibliotecas ao ambiente do jogo ou exigir acesso à rede.
        comando = [str(base), str(Path(__file__).resolve()), "--arquivo", str(args.arquivo.resolve()),
                   "--saida", str(pasta.resolve()), "--sem-diagnostico"]
        if args.abrir:
            comando.append("--abrir")
        resultado = subprocess.run(comando, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        raise SystemExit(resultado.returncode)
    print(destino.resolve())
    if args.abrir and os.name == "nt":
        os.startfile(str(destino.resolve()))


if __name__ == "__main__":
    main()
