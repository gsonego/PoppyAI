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
| 7 (atual) | Intervalos variáveis e progressivamente menores entre obstáculos, com uma distância mínima que permite completar o salto. |

Melhorias de interface, animação das patas, chão móvel, interpolação, VSync e
paralaxe não alteraram o modelo ou as regras e não abriram novos experimentos.
A unificação do arquivo e a persistência da geração também mantêm o experimento 7.

## Arquivo único e continuidade

Somente `dados/campeoes/campeao.json` armazena a campeã da IA. Ele contém
o experimento (versão, limite e semente), os quatro pesos, o viés, o recorde e
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
O recorde humano usa somente `dados/campeoes/recorde_humano.json`, separado da IA
e fora do Git. Guarda somente o tempo: é um recorde pessoal geral, independente
do experimento e da semente. Mudanças nas regras não zeram esse recorde.
A consolidação preservou o recorde atual
de 67,90 segundos e removeu os arquivos humanos separados por experimento.
