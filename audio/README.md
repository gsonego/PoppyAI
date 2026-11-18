# Efeitos do jogo

Efeitos originais sintetizados para o projeto, em estilo de console clássico,
sem gravações, samples ou serviços externos. Os WAVs e o gerador ficam no Git.

| Arquivo | Uso | Duração |
| --- | --- | --- |
| `salto.wav` | Salto iniciado no humano ou na avaliação | 0,13 s |
| `colisao.wav` | Fim de partida no humano ou na avaliação | 0,20 s |
| `menu_mover.wav` | Trocar a opção selecionada | 0,045 s |
| `menu_confirmar.wav` | Confirmar uma opção | 0,145 s |
| `recorde.wav` | Após a colisão, ao conquistar recorde pessoal | 0,47 s |

Formato PCM mono, 16 bits, 44.100 Hz. Onda quadrada, ruído determinístico na
colisão e envelopes de entrada/saída para reduzir estalos. Volume moderado
definido em `sons.py`; sem música. Para regenerar os mesmos arquivos:

```powershell
.\.venv\Scripts\python.exe audio/gerar_efeitos.py
```
