# Pedra baixa

Arte original desenhada por código em `art/pedra.py`, com contorno escuro,
cinza médio e realce claro. A forma de 16 × 5 pixels é ampliada sem suavização
para 32 × 10. O arquivo `pedra.png` exporta a mesma imagem usada no jogo.

Em pé, a Poppy passa com a corrida normal e sem alterar a altura. A pedra
colide apenas com a faixa frontal de 12 pixels da área de colisão quando ela
está abaixada. Não há novas poses nem mecânica de subir/descer um degrau.
O salto também permite passar pela pedra isolada. Desde o experimento 10, nos três modos, cada pedra
é seguida por um pássaro separado, com intervalo próximo de 0,1 segundo e no
mínimo 32 pixels a partir da sua saída. A arte da pedra continua independente,
sem nenhuma ligação visual com o pássaro. A sequência penaliza saltos feitos
perto da pedra; caminhar em pé permite atravessar os dois. Desde o experimento
11, todo túnel é seguido de uma pedra com intervalo normal, e depois do pássaro.
O intervalo curto atual é de 0,10 s, reduzido dos 0,30 s do experimento 10.

Para regenerar a arte:

```powershell
.\.venv\Scripts\python.exe -c "from art.pedra import salvar_sprite; salvar_sprite('art/source/pedra.png')"
```
