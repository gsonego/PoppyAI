# PoppyAI

Experimento de aprendizado com dois nós de entrada (distância e altura do
obstáculo), um neurônio de saída e busca evolutiva, sem bibliotecas de machine
learning. A função de ativação é o degrau: pede salto quando `z > 0`.

No PowerShell, abra a tela inicial:

```powershell
.\.venv\Scripts\python.exe main.py
```

Escolha com as setas e Enter, ou clique em uma opção:

- **Jogar:** você controla os saltos da Poppy; mostra tempo e recorde pessoal.
- **Treinar IA:** a IA busca parâmetros; mostra tempo, recorde da IA e tentativa.
- **Ver a IA jogar:** usa a campeã salva com parâmetros fixos.

O visual usa a Poppy aprovada em pixel art, cenário claro e fonte bitmap incluída
no projeto. O cenário e os sprites são carregados uma vez; a física continua igual.
Orelhas e cauda são partes decorativas da arte; `Tab` também mostra o retângulo
de colisão nos modos da IA.

Durante a partida: `Espaço` salta (humano e treino), `R` reinicia, `Esc` volta
ao menu e `Tab` abre ou fecha os detalhes da IA (treino e avaliação).
No modo humano, a colisão mantém o resultado na tela; `R` repete a partida.
Seu recorde é salvo em `recorde_humano.json` ao morrer, reiniciar, voltar ao menu
ou fechar a janela. Ele é separado dos pesos e do recorde da IA.

Para entrar diretamente, use `--modo humano`, `--modo treino` ou
`--modo avaliacao`.

Para observar a campeã salva, com os dois pesos e o viés fixos:

```powershell
.\.venv\Scripts\python.exe main.py --modo avaliacao
```

Sem `--modo`, o programa abre o menu.
Na avaliação, a partida continua até a colisão, sem limite de tempo, e mantém
o resultado na tela. R repete a mesma sequência desde o início; o salto
manual fica desativado. Esse modo não gera mutações nem grava em `campeao_altura.json`.
Se não houver campeã salva, o programa informa que é preciso treinar primeiro.

Para avaliar em outra sequência de obstáculos:

```powershell
.\.venv\Scripts\python.exe main.py --modo avaliacao --semente 456
```

A mesma semente repete a mesma sequência; sementes diferentes geram outras
sequências. O primeiro obstáculo continua igual. A semente aparece nos detalhes da IA e
no terminal, e R reinicia com a semente escolhida. Sem `--semente`, a avaliação
usa 123. Essa opção é exclusiva da avaliação; o treino continua usando 123.

Nos modos da IA, pressione `Tab` para mostrar os dois pesos, o viés, a distância,
a altura e o pedido atual da política. As entradas são normalizadas pelas dimensões da janela:

```python
z = peso_distancia * (distancia / LARGURA) + peso_altura * (altura / ALTURA) + vies
```

A marca rosa nos detalhes indica a distância em que a decisão muda, para a altura
do obstáculo atual:
`limite = -(peso_altura * (altura / ALTURA) + vies) / peso_distancia * LARGURA`.
Com peso da distância negativo, pede salto abaixo do limite; com positivo,
acima. No limite exato, não pede salto (`z > 0`, sujeito à precisão numérica).
Peso da distância zero produz uma decisão que depende apenas da altura e do
viés, sem marca de distância. Limites negativos ou fora da tela continuam
descritos no texto, sem uma marca visível no chão. O pedido só vira um salto
quando o personagem está no chão e a distância é não negativa.

O modelo anterior, com apenas distância, permanece salvo em `campeao.json`.
O modelo com altura usa a versão 2 do experimento e salva em
`campeao_altura.json`. É necessário treiná-lo antes de avaliá-lo; o recorde
antigo não é transferido. Adicionar uma entrada permite novas regras, mas
não garante melhora do desempenho.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Inicializar o Pygame e coordenar menu, controles e os três modos. |
| `config.py` | Dimensões, física, passo fixo, sementes, limite e caminho da campeã. |
| `ambiente.py` | Estado da partida, saltos, obstáculos e colisões. |
| `politica.py` | Converter distância, altura e parâmetros em um pedido de salto. |
| `treino.py` | Pontuar partidas, preservar a melhor configuração e gerar candidatas. |
| `avaliacao.py` | Carregar a campeã e acompanhar uma partida com parâmetros fixos. |
| `humano.py` | Acompanhar a partida humana e salvar o recorde pessoal separado. |
| `campeao.py` | Salvar e carregar a melhor configuração em JSON. |
| `interface.py` | Desenhar menu, partida e painel opcional, sem alterar a simulação. |
| `art/cenario.py` | Desenhar o cenário estático em pixel art. |
| `art/fonte_pixel.py` | Renderizar a fonte bitmap sem fontes externas. |

O fluxo de cada passo é: observar distância e altura → a política pedir ou não um salto → o ambiente executar o passo → o treino verificar se a tentativa acabou → desenhar.

O ambiente não conhece pesos nem mutações. A política não conhece a física. O treino muda os parâmetros somente entre partidas. Essa divisão permite estudar cada conceito e, depois, usar o mesmo ambiente com parâmetros fixos para avaliação.

## Experimento atual

- Passo fixo de 1/60 s e tentativas sem limite de tempo: terminam na colisão.
- No treino, os parâmetros mudam após a colisão. Novos recordes são salvos durante a partida, a cada avanço de aproximadamente um segundo sobre o recorde salvo, e também na colisão, antes de reiniciar, ao voltar ao menu ou ao fechar a janela. Tentativas com intervenção manual não substituem a campeã. Se uma candidata sobreviver indefinidamente, a mesma tentativa continuará rodando e sendo salva enquanto melhora o recorde.
- Treino sempre na sequência de obstáculos da semente 123.
- Campeã salva em `campeao_altura.json`, ao lado dos arquivos; empates preservam a anterior.
- Durante o jogo, as gravações ocorrem em uma thread separada para não bloquear os quadros. Se o disco estiver ocupado, a fila mantém apenas o pedido mais recente. Ao fechar a janela, o programa espera a última gravação terminar. Erros de gravação são informados.
- Ao reabrir, a primeira candidata usa os parâmetros salvos. O estado do gerador de mutações não é salvo, portanto a busca não continua exatamente de onde parou.
- No treino, Espaço permite salto manual e R reposiciona o jogo. Tentativas com intervenção manual não entram no recorde. R mantém o tamanho e a sequência atuais dos obstáculos, como na versão anterior.

A versão do experimento em `campeao.py` deve ser incrementada se mudar a física, a observação, a política ou a geração de obstáculos. O carregamento também verifica o limite e a semente. O limite atual é `null` no JSON (sem teto). Campeãs da versão 2 com o antigo limite de 30 segundos continuam válidas: seus tempos são os já alcançados, e um recorde de 30 segundos não significa que houve colisão nesse instante. As próximas gravações usam o formato sem teto.

A avaliação usa a semente 123 por padrão para reproduzir o desempenho da campeã; `--semente` permite observar o desempenho em outras sequências. Se resultados dessas sequências orientarem ajustes, elas passam a servir como validação; a avaliação final precisa de outras sequências reservadas.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
