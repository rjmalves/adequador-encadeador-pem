import pathlib
from typing import Tuple


def nome_arquivo_dger():
    return "dger.dat"


def nome_arquivo_cvar():
    return "cvar.dat"


def nome_arquivo_curva():
    return "curva.dat"


def nome_arquivo_sistema():
    return "sistema.dat"


def nome_arquivo_penalid():
    return "penalid.dat"


def nome_arquivo_clast():
    return "clast.dat"


def nome_arquivo_modif():
    return "modif.dat"


def nome_arquivo_hidr():
    return "hidr.dat"


def nome_arquivo_polinjus():
    return "polinjus.dat"


def dados_caso(caminho: str) -> Tuple[str, str, str]:
    p = pathlib.Path(caminho)
    return p.parts[-2].split("_")


def nome_arquivo_dadger(revisao: str):
    arquivo = f"dadger.{revisao}"
    return arquivo


def nome_arquivo_vazoes(caso: str):
    rv = caso.split("_")[-1]
    arquivo = f"vazoes.{rv}"
    return arquivo
