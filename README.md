# PoppyAI

Experimento de aprendizado com um neurônio e busca evolutiva, sem bibliotecas de machine learning.

No PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Inicializar o Pygame e coordenar teclado, simulação, treino e desenho. |
| `config.py` | Dimensões, física, passo fixo, sementes, limite e caminho da campeã. |
| `ambiente.py` | Estado da partida, saltos, obstáculos e colisões. |
| `politica.py` | Converter a distância e os parâmetros em um pedido de salto. |
| `treino.py` | Pontuar partidas, preservar a melhor configuração e gerar candidatas. |
| `campeao.py` | Salvar e carregar a melhor configuração em JSON. |
| `interface.py` | Desenhar o estado atual, sem modificá-lo. |

O fluxo de cada passo é: observar a distância → a política pedir ou não um salto → o ambiente executar o passo → o treino verificar se a tentativa acabou → desenhar.

O ambiente não conhece pesos nem mutações. A política não conhece a física. O treino muda os parâmetros somente entre partidas. Essa divisão permite estudar cada conceito e, depois, usar o mesmo ambiente com parâmetros fixos para avaliação.

## Experimento atual

- Passo fixo de 1/60 s e limite de 30 s por tentativa.
- Treino sempre na sequência de obstáculos da semente 123.
- Campeã salva em `campeao.json`, ao lado dos arquivos; empates preservam a anterior.
- Ao reabrir, a primeira candidata usa os parâmetros salvos. O estado do gerador de mutações não é salvo, portanto a busca não continua exatamente de onde parou.
- Espaço permite salto manual e R reposiciona o jogo. Tentativas com intervenção manual não entram no recorde. R mantém o tamanho e a sequência atuais dos obstáculos, como na versão anterior.

A versão do experimento em `campeao.py` deve ser incrementada se mudar a física, a observação, a política ou a geração de obstáculos. O carregamento também verifica o limite e a semente para evitar comparar recordes de condições diferentes.

Os modos separados de treino e avaliação ainda serão implementados. Um recorde no treino não mede generalização para outras sequências. Se resultados de novas sequências orientarem ajustes, elas passam a servir como validação; a avaliação final precisa de outras sequências reservadas.
