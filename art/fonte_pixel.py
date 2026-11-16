"""Fonte bitmap 5×7 do jogo; não depende de fontes do sistema."""

from functools import lru_cache
import unicodedata

import pygame


# Cada par hexadecimal representa uma linha de cinco pixels.
GLIFOS = {
    "A": "0E11111F111111", "B": "1E11111E11111E", "C": "0E11101010110E",
    "D": "1E11111111111E", "E": "1F10101E10101F", "F": "1F10101E101010",
    "G": "0E11101711110F", "H": "1111111F111111", "I": "0E04040404040E",
    "J": "0702020202120C", "K": "11121418141211", "L": "1010101010101F",
    "M": "111B1515111111", "N": "11191513111111", "O": "0E11111111110E",
    "P": "1E11111E101010", "Q": "0E11111115120D", "R": "1E11111E141211",
    "S": "0F10100E01011E", "T": "1F040404040404", "U": "1111111111110E",
    "V": "11111111110A04", "W": "11111115151B11", "X": "11110A040A1111",
    "Y": "11110A04040404", "Z": "1F01020408101F",
    "0": "0E11131519110E", "1": "040C040404040E", "2": "0E11010204081F",
    "3": "1E01010E01011E", "4": "02060A121F0202", "5": "1F10101E01011E",
    "6": "0E10101E11110E", "7": "1F010204080808", "8": "0E11110E11110E",
    "9": "0E11110F01010E", ".": "00000000000C0C", ":": "000C0C000C0C00",
    "-": "0000001F000000", "/": "01020204080810", "+": "0004041F040400",
    "#": "0A0A1F0A1F0A0A", "!": "04040404040004", "?": "0E110204040004",
    "(": "02040808080402", ")": "08040202020408", " ": "00000000000000",
}


class FontePixel:
    @lru_cache(maxsize=256)
    def render(self, texto, cor, escala=2):
        texto = unicodedata.normalize("NFKD", texto.upper()).encode("ascii", "ignore").decode()
        superficie = pygame.Surface((max(1, len(texto) * 6 - 1) * escala, 7 * escala), pygame.SRCALPHA)
        for indice, letra in enumerate(texto):
            glifo = GLIFOS.get(letra, GLIFOS["?"])
            for y in range(7):
                bits = int(glifo[y * 2:y * 2 + 2], 16)
                for x in range(5):
                    if bits & (1 << (4 - x)):
                        pygame.draw.rect(superficie, cor, ((indice * 6 + x) * escala, y * escala, escala, escala))
        return superficie
