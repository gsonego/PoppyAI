# Poppy abaixada

Pose de perfil para a direita, gerada com ImageGen a partir de
`poppy-aprovada.png`, com fundo transparente. Integrada no modo humano.

Prompt: preservar identidade, paleta, contornos em pixel art, pelagem creme,
marca marrom no olho e coleira rosa de coração. Alterar somente a pose para
um agachamento canino natural: quatro patas dobradas sob o corpo, cabeça baixa,
orelhas para trás e cauda baixa; aproximadamente 55% da altura em pé, sem
simplesmente achatar a imagem. Um sprite isolado, sem texto, cenário ou sombra.

O jogo recorta a margem transparente, reduz para 38 pixels de altura sem
suavização e mantém o apoio no chão. A colisão é de 48 × 32 pixels. A versão
vermelha usa uma multiplicação de cor em memória e ambas ficam em cache.

## Corrida abaixada

`poppy-corrida-abaixada.png`: folha 2 × 2 gerada com ImageGen a partir da pose
abaixada, na ordem superior esquerda, superior direita, inferior esquerda,
inferior direita. Mantida no projeto junto com a pose de referência.

Prompt: mesma Poppy, de perfil para a direita, correndo abaixada. Preservar
cabeça, tronco, cauda, escala, paleta, coleira e orelhas baixas. Quatro poses
distintas das patas curtas dobradas: extensão dianteira, passagem sob o corpo,
extensão oposta e segunda passagem. Cabeça e corpo estáveis, mesma linha do
chão e células iguais; fundo transparente, sem rótulos ou cenário.

O ciclo acompanha o deslocamento do mundo, como a corrida em pé, e congela
na colisão. Os quatro quadros têm tamanho fixo e são guardados em memória.
