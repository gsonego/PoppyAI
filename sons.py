"""Efeitos curtos carregados uma vez; falhas de áudio não interrompem o jogo."""

from pathlib import Path

import pygame

from diagnostico import registro


class Sons:
    def __init__(self, pasta=Path(__file__).resolve().parent / "audio"):
        self.silenciado = False
        self.efeitos = {}
        if pygame.mixer.get_init() is None:
            registro.warning("Audio indisponivel; continuando sem som")
            return
        try:
            self.efeitos = {nome: pygame.mixer.Sound(str(pasta / f"{nome}.wav"))
                            for nome in ("salto", "colisao", "menu_mover", "menu_confirmar", "recorde")}
            for efeito in self.efeitos.values():
                efeito.set_volume(0.45)
        except (pygame.error, OSError):
            registro.warning("Nao foi possivel carregar os efeitos; continuando sem som", exc_info=True)
            self.efeitos = {}

    @property
    def disponivel(self):
        return bool(self.efeitos)

    def alternar(self):
        self.silenciado = not self.silenciado
        if self.silenciado:
            for efeito in self.efeitos.values():
                efeito.stop()

    def tocar(self, nome):
        if not self.silenciado and nome in self.efeitos:
            return self.efeitos[nome].play()
        return None

    def fim_partida(self, novo_recorde=False):
        canal = self.tocar("colisao")
        if novo_recorde and not self.silenciado and self.disponivel:
            if canal is not None:
                canal.queue(self.efeitos["recorde"])
            else:
                self.tocar("recorde")
