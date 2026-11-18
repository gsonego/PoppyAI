# Histórico dos experimentos

Ordem baseada nas mudanças registradas no projeto. O número corresponde a
`VERSAO_EXPERIMENTO`, salvo dentro de `dados/campeoes/campeao.json`.

| Experimento | Mudança principal |
| --- | --- |
| 1 | Política com distância como entrada e um viés; salto decidido por degrau. Inicialmente havia um teto de 30 segundos. |
| 2 | Altura do obstáculo como segunda entrada. Depois, remoção do teto de 30 segundos: a tentativa passou a terminar na colisão. |
| 3 | Caixas duplas lado a lado e empilhadas, nos três modos. |
| 4 | Largura total do obstáculo como terceira entrada, para ajustar o momento do salto. |
| 5 | Área de colisão da Poppy ampliada para 48 × 56 pixels. Durante esta etapa entrou o treino coletivo de 50 Poppys por geração. |
| 6 | Velocidade como quarta entrada; aceleração gradual de 350 até 650 px/s. |
| 7 | Intervalos variáveis e progressivamente menores entre obstáculos, com uma distância mínima que permite completar o salto. |
| 8 | Rede com cinco entradas (incluindo elevação), quatro neurônios intermediários com tanh e duas saídas de degrau: salto e abaixar. São 34 pesos e vieses. Os voadores passam a participar do treino e da avaliação. |
| 9 | Bumerangue substituído por túnel de 120, 200 ou 280 pixels, com passagem fixa de 42 pixels e bloqueio superior intransponível por salto. Mesma rede 5/4/2; o alvo continua sendo o túnel até a traseira da Poppy sair. |
| 10 | Pedras baixas e pássaros separados logo depois entram também no treino e na avaliação. A pedra permite correr em pé, mas atinge o focinho abaixado; saltar perto dela pode encontrar o pássaro. Mesma rede 5/4/2, novos pesos e geração 1. |
| 11 | Pássaro chega mais perto da pedra: atraso de 0,10 s e distância mínima de 32 px (antes 0,30 s e 90 px). Todo túnel passa a ser seguido por pedra, com o intervalo normal contado da saída, e depois pelo pássaro. Sem dois túneis consecutivos. Mesma rede 5/4/2, novos pesos e geração 1. |
| 12 (atual) | Sorteio por famílias com menor chance de repetição e bloqueio temporário após duas escolhas iguais. Depois de túnel, pode vir caixa, pedra ou pássaro; sem pedra obrigatória e sem dois túneis seguidos. Mantém pedra + pássaro próximo, margens normais, rede 5/4/2 e semente de treino fixa. Novos pesos e geração 1. |

Melhorias de interface, animação das patas, chão móvel, interpolação, VSync e
paralaxe não alteraram o modelo ou as regras e não abriram novos experimentos.
A unificação do arquivo e a persistência da geração mantiveram o experimento 7.
A adaptação da IA para os voadores abriu o experimento 8. A troca do bumerangue
pelo túnel abre o experimento 9 com pesos novos e geração 1, mantendo a arquitetura.

## Arquivo único e continuidade

Somente `dados/campeoes/campeao.json` armazena a campeã da IA. Ele contém
o experimento (versão, limite e semente), a arquitetura da rede, os 34 pesos e vieses, o recorde e
`geracao`: o número da geração atual do treino, independentemente da geração
em que o recorde foi conquistado. Continua fora do Git.

A geração é salva nos novos recordes, nas trocas de geração e ao sair do treino,
mesmo sem melhora do recorde. Ao reabrir, a contagem é retomada e a corrida dessa
geração recomeça com uma população criada a partir da campeã. A população completa,
o estado do sorteio e o andamento da corrida não são restaurados.

Arquivos antigos sem `geracao` começam em 1: a contagem anterior não foi registrada
e não pode ser recuperada. Na consolidação, os pesos e o recorde do experimento 7
foram preservados; os arquivos separados dos experimentos anteriores foram removidos.

Ao mudar as regras ou entradas, incremente `VERSAO_EXPERIMENTO` e acrescente uma
linha ao histórico. O treino começa uma busca com geração 1 e substitui a campeã
do experimento anterior no primeiro salvamento. A avaliação recusa campeãs de
outro experimento. Pontuações de desafios diferentes não são comparadas.

## Resultados dos experimentos encerrados

Antes de substituir a campeã por uma de outro experimento, o programa salva um
resumo em `dados/campeoes/historico_experimentos.json`: identificação completa
do experimento, melhor tempo, geração final registrada e data de encerramento
em UTC. As entradas seguem a ordem em que foram registradas. Uma nova execução
do mesmo experimento atualiza seu resumo, sem duplicar a entrada.

Esse arquivo contém somente resultados, sem pesos nem populações. Permanece
fora do Git junto dos dados locais; `campeao.json` continua sendo o único
arquivo de campeã. A geração final é a contagem alcançada pelo treino, não a
geração em que a campeã surgiu. Se um arquivo antigo não tiver essa contagem,
o histórico registra `null`, pois não é possível recuperá-la.

O resumo é criado no primeiro salvamento do novo experimento. Só abrir o treino
ou avaliar não encerra o anterior. Se a gravação do histórico falhar, a campeã
anterior não é substituída. Salvar recordes no mesmo experimento não cria
entradas no histórico. Apagar manualmente a campeã antes da troca impede que
seu resultado seja recuperado automaticamente.

## Recorde humano

O recorde humano usa somente `dados/campeoes/recorde_humano.json`, separado da IA
e fora do Git. Guarda somente o tempo: é um recorde pessoal geral, independente
do experimento e da semente. Mudanças nas regras não zeram esse recorde.
A consolidação preservou o recorde atual
de 67,90 segundos e removeu os arquivos humanos separados por experimento.
