# Passarinho alto

Arte original em pixel art desenhada por código em `art/passarinho.py`.
Perfil para a esquerda, contorno azul escuro, corpo azul, barriga clara e bico
laranja. Quatro poses de asas em um quadro fixo de 40 × 32 pixels, sem suavização.
`passarinho.png` exporta a mesma arte usada no jogo em uma folha horizontal.

A animação avança a cada 24 pixels percorridos pelo mundo e congela na colisão.
A área de colisão de 40 × 24 cobre o corpo; pontas das asas têm tolerância.
O centro fica 104 pixels acima do chão, com espaço acima das orelhas da Poppy
correndo. Não altera a altura ao bater asas.

Para regenerar a folha:

```powershell
.\.venv\Scripts\python.exe -c "from art.passarinho import salvar_folha; salvar_folha('art/source/passarinho.png')"
```
