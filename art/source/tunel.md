# Túnel integrado — experimento 9

`tunel.png`: arte final transparente, gerada e refinada com ImageGen a partir
de `art/previews/tunel-proposta-v2.png`, após a revisão do usuário que retirou
as paredes da entrada e saída. `tunel-rascunho.png` preserva a primeira variante
do sprite antes da correção da opacidade do metal.

Prompt: isolar o túnel aprovado sem Poppy ou cenário. Preservar bloco metálico
superior alto e sólido, rebites, travessa inferior do teto, corredor baixo com
fundo escuro e soleira fina. Entrada e saída inteiramente abertas, sem montantes
verticais ou lábios voltados para baixo. Pixel art de console clássico, contornos
escuros e paleta azul-cinza. Fundo transparente. Refinamento: metal e fundo do
corredor opacos e uniformes, sem manchas translúcidas ou textura nebulosa.

`art/tunel.py` remove as margens transparentes e monta os comprimentos de
120, 200 e 280 pixels. Bloco/teto com 118 pixels de altura, corredor de 42 pixels
e base decorativa de 2 pixels abaixo do nível de apoio. Escala sem suavização,
em uma grade de dois pixels. Os três sprites são preparados uma única vez.

O desenho começa a 160 pixels acima do chão. A colisão cobre somente o bloco
superior inteiro, até a borda inferior do teto. A base e o fundo escuro da
passagem são decorativos; não há paredes de colisão nas pontas. A arte aparece
atrás da Poppy, mostrando a personagem dentro do corredor. O topo excede a
altura máxima do salto. A prévia dos três comprimentos está em
`art/previews/tuneis-integrados.png`.
