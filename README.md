# PoppyAI

Experimento de aprendizado com quatro nós de entrada (distância, altura, largura e velocidade do
obstáculo), um neurônio de saída e busca evolutiva, sem bibliotecas de machine
learning. A função de ativação é o degrau: pede salto quando `z > 0`.

No PowerShell, abra a tela inicial:

```powershell
.\.venv\Scripts\python.exe main.py
```

Escolha com as setas e Enter, ou clique em uma opção:

- **Jogar:** você controla os saltos da Poppy; mostra tempo e recorde pessoal.
- **Treinar IA:** 50 Poppys treinam juntas; mostra geração, sobreviventes, tempo e recorde da IA.
- **Ver a IA jogar:** usa a campeã salva com parâmetros fixos.

O visual usa a Poppy aprovada em pixel art, cenário claro e fonte bitmap incluída
no projeto. O cenário e os sprites são carregados uma vez; a interface não altera a física.
O jogo abre em tela cheia, na resolução do monitor. `F11` alterna entre tela cheia
e janela; no modo janela, você pode redimensionar ou maximizar. A imagem mantém a proporção, com faixas
nas sobras, e usa ampliação sem suavização para preservar os pixels. As coordenadas
do mouse são convertidas para que os botões continuem funcionando em qualquer tamanho.
A área de colisão da Poppy tem 48 × 56 pixels lógicos e cobre corpo e cabeça.
As pontas das orelhas, a cauda e as extremidades das patas ficam fora para dar
uma pequena tolerância. O retângulo é fixo entre as poses; não muda a cada passo.
`Tab` mostra essa área nos modos da IA. A distância do sensor parte da frente
desse retângulo. A arte mantém a posição visual anterior, com um deslocamento
horizontal de -5 pixels em relação ao centro da área de colisão.

A corrida usa quatro poses alinhadas, alternadas a cada 32 pixels percorridos
pelo mundo. Ela acompanha o deslocamento da partida, sem depender do relógio real.
No salto, as patas ficam recolhidas; na colisão, a corrida para. No humano e na
avaliação, a Poppy fica vermelha; no treino coletivo, ela desaparece. No menu
ela permanece parada. Quadros e tamanhos são carregados e
guardados em memória, sem leitura de imagem a cada quadro. A animação por si só não altera a física nem a política.

Durante a partida: `Espaço` salta no humano, `R` reinicia no humano e na avaliação, `Esc` volta
ao menu e `Tab` abre ou fecha os detalhes da IA (treino e avaliação).
No modo humano, a colisão mantém o resultado na tela; `R` repete a partida.
A Poppy fica vermelha ao colidir no humano e na avaliação e permanece assim
até reiniciar. No treino, cada Poppy que colide é removida junto com sua linha.
Seu recorde é salvo em `recorde_humano_intervalos.json` ao morrer, reiniciar, voltar ao menu
ou fechar a janela. Ele é separado dos pesos e do recorde da IA.

Para entrar diretamente, use `--modo humano`, `--modo treino` ou
`--modo avaliacao`.

Para observar a campeã salva, com os quatro pesos e o viés fixos:

```powershell
.\.venv\Scripts\python.exe main.py --modo avaliacao
```

Sem `--modo`, o programa abre o menu.
Na avaliação, a partida continua até a colisão, sem limite de tempo, e mantém
o resultado na tela. R repete a mesma sequência desde o início; o salto
manual fica desativado. Esse modo não gera mutações nem grava em `dados/campeoes/campeao_intervalos.json`.
Se não houver campeã salva, o programa informa que é preciso treinar primeiro.

Para avaliar em outra sequência de obstáculos:

```powershell
.\.venv\Scripts\python.exe main.py --modo avaliacao --semente 456
```

A mesma semente repete a mesma sequência; sementes diferentes geram outras
sequências. O primeiro obstáculo continua igual. A semente aparece nos detalhes da IA e
no terminal, e R reinicia com a semente escolhida. Sem `--semente`, a avaliação
usa 123. Essa opção é exclusiva da avaliação; o treino continua usando 123.

Nos modos da IA, pressione `Tab` para mostrar os quatro pesos, o viés, a distância,
a altura, a largura total do conjunto, a velocidade e o pedido atual da política.
Distância e largura são divididas pela largura lógica da janela, altura pela
altura lógica e velocidade por `VELOCIDADE_MAXIMA`:

```python
z = (peso_distancia * (distancia / LARGURA)
     + peso_altura * (altura / ALTURA)
     + peso_largura * (largura / LARGURA)
     + peso_velocidade * (velocidade / VELOCIDADE_MAXIMA)
     + vies)
```

A marca rosa nos detalhes indica a distância em que a decisão muda, para a altura
a largura e a velocidade do conjunto atual:
`limite = -(peso_altura * (altura / ALTURA) + peso_largura * (largura / LARGURA) + peso_velocidade * (velocidade / VELOCIDADE_MAXIMA) + vies) / peso_distancia * LARGURA`.
Com peso da distância negativo, pede salto abaixo do limite; com positivo,
acima. No limite exato, não pede salto (`z > 0`, sujeito à precisão numérica).
Peso da distância zero produz uma decisão que depende apenas da altura, da largura, da velocidade e do
viés, sem marca de distância. Limites negativos ou fora da tela continuam
descritos no texto, sem uma marca visível no chão. O pedido só vira um salto
quando o personagem está no chão e a distância é não negativa.

O modelo da IA é a versão 7, com quatro pesos e um viés, salvo em
`dados/campeoes/campeao_intervalos.json`. As regras da partida são a versão 6,
com o recorde pessoal em `recorde_humano_intervalos.json`. Os intervalos menores mudam o
desafio: é necessário novo treino e novos recordes. As campeãs anteriores foram
preservadas em `dados/campeoes/`, sem reaproveitar suas pontuações no novo modelo.
As forças do salto e a aceleração continuam iguais. Os pesos anteriores permanecem
em seus arquivos, incluindo `dados/campeoes/campeao_velocidade.json`.

A pasta `dados/campeoes/` é criada automaticamente no primeiro salvamento e é
ignorada pelo Git. Os arquivos das campeãs que eram versionados foram retirados
do índice; o próximo commit remove-os da versão atual do repositório. Isso não
apaga os arquivos publicados em commits antigos.
A largura permite aprender um momento de salto diferente para caixas largas.
A força e a duração do salto continuam fixas: a IA só decide quando pedir o
salto. Um obstáculo mais largo pode exigir saltar mais perto para não pousar
antes de ultrapassá-lo. O treino busca os pesos; não há uma regra manual que
obrigue o peso da largura a ter um sinal específico.

## Caixas duplas

Humano, treino e avaliação usam a mesma geração. O primeiro obstáculo continua
sendo uma caixa simples de 30 × 50. Nos seguintes sorteios, a distribuição é:

- 50%: caixa simples, nas dimensões que já existiam.
- 25%: duas caixas iguais lado a lado, sem vão; largura total de 40 a 80 px.
- 25%: duas caixas iguais empilhadas; altura total de 60 a 84 px.

A força do salto continua igual. As dimensões máximas dos
pares foram verificadas com a física atual para que exista um momento de salto
capaz de ultrapassá-los. A colisão e o sensor usam o retângulo total, preenchido
pelas duas caixas. No humano e na avaliação, R recomeça a sequência pela caixa
simples inicial; cada geração do treino também começa nessa mesma sequência.

## Intervalos menores e variáveis

A pista mantém vários conjuntos de caixas ao mesmo tempo. Os novos conjuntos
entram pela borda direita; os antigos continuam visíveis até saírem pela esquerda.
A colisão considera todos eles, e a observação da IA aponta para o próximo conjunto
que ainda não passou completamente pela personagem.

O intervalo é o vão entre a traseira de um conjunto e a frente do seguinte.
Sorteamos uma duração entre 1,8 e 2,3 segundos no início e reduzimos essa faixa
continuamente até 0,85 a 1,15 segundos aos 90 segundos de partida. A duração
sorteada é convertida em pixels usando a velocidade no momento de gerar o conjunto.
O vão nunca fica abaixo de 567 pixels: esse piso considera um salto completo,
mais 0,15 segundo de margem, na velocidade máxima. Por isso, o tempo efetivo
entre conjuntos pode ser maior que a faixa sorteada, especialmente em velocidades
mais baixas. A largura dos conjuntos também entra no tempo entre suas frentes.

A mesma semente reproduz tipos, dimensões e intervalos para todas as Poppys.
Reiniciar restaura a progressão inicial. Testes de saltos consecutivos alternam
os pares máximos no menor intervalo e verificam a passagem em 350, 500 e 650 px/s,
com a aceleração ativa.

## Chão em movimento

A grama, a terra e as flores deslizam para a esquerda na mesma velocidade dos
obstáculos, guiadas pela distância já percorrida. O padrão de chão é carregado
uma vez e repetido sem emendas. No menu ele fica parado; na colisão ele para;
reiniciar a partida ou a geração restaura sua posição. Essa mudança é visual
e não invalida pesos ou recordes. Paisagem e nuvens ainda permanecem estáticas.

## Velocidade progressiva

Nos três modos, começa em 350 px/s e aumenta continuamente 2,5 px/s a cada
segundo sobrevivido (25 px/s a cada 10 segundos), até 650 px/s aos 120 segundos.
A velocidade aparece no cabeçalho. Reiniciar ou começar uma geração restaura
350 px/s. As 50 Poppys sobreviventes têm a mesma aceleração, definida pelo tempo
simulado, independentemente da velocidade de renderização. As patinhas já
acompanham o deslocamento mais rápido. Não há limite de duração da partida.

A IA recebe a velocidade como quarta entrada para ajustar o momento do salto.
Os maiores conjuntos de caixas foram testados de 350 a 650 px/s, a cada 25 px/s,
incluindo a aceleração durante o salto, com a mesma física e colisão do jogo.

## Treino visual por gerações

São 50 Poppys com pesos próprios, simuladas no mesmo passo fixo e na mesma
sequência de obstáculos. Cada uma tem uma cor fixa para a linha até a frente
do obstáculo; as Poppys mantêm a pelagem original. As linhas aparecem sempre
no treino. As demais Poppys são desenhadas com transparência e uma representante
com melhor tempo fica destacada. Sobreviventes empatadas são equivalentes pelo
critério de pontuação atual; o destaque não prevê qual sobreviverá mais.

Quando todas morrem, a próxima geração começa automaticamente. As cinco melhores
são preservadas (incluindo a campeã histórica); as outras 45 vêm de mutações
dos melhores pais, com 20% de chance por vaga de sortear pesos novos. Uma campeã
já salva entra na primeira geração. Os pesos não mudam durante a partida de
uma Poppy. O arquivo e o formato da campeã continuam compatíveis com a avaliação.

`N` salva a melhor pontuação alcançada e avança a geração, mesmo com Poppys vivas.
Não há limite de duração; use essa tecla se alguma continuar sobrevivendo.
`Tab` abre os pesos e a marca de salto da representante; `Esc` volta ao menu
salvando o melhor progresso. `Espaço` e `R` ficam desativados no treino coletivo.
Poppys que fazem os mesmos movimentos podem se sobrepor, embora sejam simuladas
e pontuadas separadamente. O estado completo da população e o número da geração
não são persistidos: ao reabrir, começa uma geração nova com a campeã salva.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Inicializar o Pygame e coordenar menu, controles e os três modos. |
| `config.py` | Dimensões, física, passo fixo, sementes, limite e caminho da campeã. |
| `ambiente.py` | Estado da partida, saltos, obstáculos e colisões. |
| `politica.py` | Converter distância, altura, largura e parâmetros em um pedido de salto. |
| `treino.py` | Pontuar partidas, preservar a melhor configuração e gerar candidatas. |
| `geracoes.py` | Simular 50 candidatas, eliminar colisões e selecionar a próxima geração. |
| `avaliacao.py` | Carregar a campeã e acompanhar uma partida com parâmetros fixos. |
| `humano.py` | Acompanhar a partida humana e salvar o recorde pessoal separado. |
| `campeao.py` | Salvar e carregar a melhor configuração em JSON. |
| `interface.py` | Desenhar menu, partida e painel opcional, sem alterar a simulação. |
| `janela.py` | Ampliar a apresentação e converter cliques sem alterar a física. |
| `art/cenario.py` | Desenhar a paisagem em pixel art e o chão que acompanha o deslocamento. |
| `art/fonte_pixel.py` | Renderizar a fonte bitmap sem fontes externas. |

O fluxo de cada passo é: observar distância, altura, largura e velocidade → a política pedir ou não um salto → o ambiente executar o passo → o treino verificar se a tentativa acabou → desenhar.

O ambiente não conhece pesos nem mutações. A política não conhece a física. O treino muda os parâmetros somente entre partidas. Essa divisão permite estudar cada conceito e, depois, usar o mesmo ambiente com parâmetros fixos para avaliação.

## Experimento atual

- Passo fixo de 1/60 s e tentativas sem limite de tempo: terminam na colisão.
- No treino coletivo, os parâmetros mudam entre gerações. Novos recordes são salvos durante a partida, a cada avanço de aproximadamente um segundo sobre o recorde salvo, e também ao encerrar uma geração, voltar ao menu ou fechar a janela.
- Treino sempre na sequência de obstáculos da semente 123.
- Campeã salva em `dados/campeoes/campeao_intervalos.json`, fora do versionamento; empates preservam a anterior.
- Durante o jogo, as gravações ocorrem em uma thread separada para não bloquear os quadros. Se o disco estiver ocupado, a fila mantém apenas o pedido mais recente. Ao fechar a janela, o programa espera a última gravação terminar. Erros de gravação são informados.
- Ao reabrir, a primeira candidata usa os parâmetros salvos. O estado do gerador de mutações não é salvo, portanto a busca não continua exatamente de onde parou.
- No treino, N avança para a próxima geração; não há intervenção manual nos saltos.

A versão do experimento em `campeao.py` deve ser incrementada se mudar a física, a observação, a política ou a geração de obstáculos. O carregamento também verifica o limite e a semente. O limite atual é `null` no JSON (sem teto). Recordes de versões anteriores não são comparados com os do desafio atual.

A avaliação usa a semente 123 por padrão para reproduzir o desempenho da campeã; `--semente` permite observar o desempenho em outras sequências. Se resultados dessas sequências orientarem ajustes, elas passam a servir como validação; a avaliação final precisa de outras sequências reservadas.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
