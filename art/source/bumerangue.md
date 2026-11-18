# Bumerangue baixo

Arte original em pixel art desenhada por código em `art/bumerangue.py`:
contorno escuro, madeira laranja, faixa clara e detalhes rosa. Não usa imagens
ou serviços externos. A folha `bumerangue.png` exporta os mesmos 16 quadros
do jogo em uma grade 4 × 4 transparente, para revisão no repositório.

Cada quadro ocupa 32 × 32 pixels. A rotação acontece em passos de 22,5 graus,
sem suavização, a cada 12 pixels de deslocamento do mundo. As poses são criadas
uma única vez e congelam junto com a partida na colisão.

Para regenerar a folha, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -c "from art.bumerangue import salvar_folha; salvar_folha('art/source/bumerangue.png')"
```
