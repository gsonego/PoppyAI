"""Registro local de encerramentos e falhas, inclusive falhas nativas do SDL."""

from contextlib import contextmanager
import faulthandler
import logging
from pathlib import Path


ARQUIVO_LOG = Path(__file__).resolve().parent / "dados" / "logs" / "jogo.log"
registro = logging.getLogger("poppy.execucao")
registro.addHandler(logging.NullHandler())
registro.setLevel(logging.INFO)
registro.propagate = False


@contextmanager
def registrar_execucao(caminho=ARQUIVO_LOG):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as arquivo:
        handler = logging.StreamHandler(arquivo)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        registro.addHandler(handler)
        habilitar = not faulthandler.is_enabled()
        try:
            if habilitar:
                faulthandler.enable(file=arquivo, all_threads=True)
            registro.info("Iniciando jogo")
            try:
                yield
            except BaseException:
                registro.exception("Jogo interrompido por erro ou interrupcao")
                raise
            else:
                registro.info("Jogo encerrado normalmente")
        finally:
            if habilitar:
                faulthandler.disable()
            registro.removeHandler(handler)
            handler.close()
