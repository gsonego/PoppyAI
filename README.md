# PoppyAI

Experimento de aprendizado com um neurônio e busca evolutiva, sem bibliotecas de machine learning.

No PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

Para observar a campeã salva, com peso e viés fixos:

```powershell
.\.venv\Scripts\python.exe main.py --modo avaliacao
```

O modo padrão continua sendo treino (também pode usar `--modo treino`).
Na avaliação, a partida para na colisão ou no limite de 30 segundos e mantém
o resultado na tela. R repete a mesma sequência desde o início; o salto
manual fica desativado. Esse modo não gera mutações nem grava em `campeao.json`.
Se não houver campeã salva, o programa informa que é preciso treinar primeiro.

Para avaliar em outra sequência de obstáculos:

```powershell
.\.venv\Scripts\python.exe main.py --modo avaliacao --semente 456
```

A mesma semente repete a mesma sequência; sementes diferentes geram outras
sequências. O primeiro obstáculo continua igual. A semente aparece na tela e
no terminal, e R reinicia com a semente escolhida. Sem `--semente`, a avaliação
usa 123. Essa opção é exclusiva da avaliação; o treino continua usando 123.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Inicializar o Pygame e coordenar teclado, simulação, treino e desenho. |
| `config.py` | Dimensões, física, passo fixo, sementes, limite e caminho da campeã. |
| `ambiente.py` | Estado da partida, saltos, obstáculos e colisões. |
| `politica.py` | Converter a distância e os parâmetros em um pedido de salto. |
| `treino.py` | Pontuar partidas, preservar a melhor configuração e gerar candidatas. |
| `avaliacao.py` | Carregar a campeã e acompanhar uma partida com parâmetros fixos. |
| `campeao.py` | Salvar e carregar a melhor configuração em JSON. |
| `interface.py` | Desenhar o estado atual, sem modificá-lo. |

O fluxo de cada passo é: observar a distância → a política pedir ou não um salto → o ambiente executar o passo → o treino verificar se a tentativa acabou → desenhar.

O ambiente não conhece pesos nem mutações. A política não conhece a física. O treino muda os parâmetros somente entre partidas. Essa divisão permite estudar cada conceito e, depois, usar o mesmo ambiente com parâmetros fixos para avaliação.

## Experimento atual

- Passo fixo de 1/60 s e limite de 30 s por tentativa.
- Treino sempre na sequência de obstáculos da semente 123.
- Campeã salva em `campeao.json`, ao lado dos arquivos; empates preservam a anterior.
- Ao reabrir, a primeira candidata usa os parâmetros salvos. O estado do gerador de mutações não é salvo, portanto a busca não continua exatamente de onde parou.
- No treino, Espaço permite salto manual e R reposiciona o jogo. Tentativas com intervenção manual não entram no recorde. R mantém o tamanho e a sequência atuais dos obstáculos, como na versão anterior.

A versão do experimento em `campeao.py` deve ser incrementada se mudar a física, a observação, a política ou a geração de obstáculos. O carregamento também verifica o limite e a semente para evitar comparar recordes de condições diferentes.

A avaliação usa a semente 123 por padrão para reproduzir o desempenho da campeã; `--semente` permite observar o desempenho em outras sequências. Se resultados dessas sequências orientarem ajustes, elas passam a servir como validação; a avaliação final precisa de outras sequências reservadas.
