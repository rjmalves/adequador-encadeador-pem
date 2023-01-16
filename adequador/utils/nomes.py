import pathlib
from typing import Tuple


def nome_arquivo_arquivos():
    return "arquivos.dat"


def nome_arquivo_dger():
    return "dger.dat"


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


def nome_arquivo_exph():
    return "exph.dat"


def nome_arquivo_adterm():
    return "adterm.dat"


def nome_arquivo_ghmin():
    return "ghmin.dat"


def nome_arquivo_sar():
    return "sar.dat"


def nome_arquivo_cvar():
    return "cvar.dat"


def nome_arquivo_ree():
    return "ree.dat"


def nome_arquivo_re():
    return "re.dat"


def nome_arquivo_tecno():
    return "tecno.dat"


def nome_arquivo_abertura():
    return "abertura.dat"


def nome_arquivo_gee():
    return "gee.dat"


def nome_arquivo_clasgas():
    return "clasgas.dat"


def nome_arquivo_simfinal():
    return "simfinal.dat"


def nome_arquivo_cortes_pos():
    return "cortes-pos.dat"


def nome_arquivo_cortesh_pos():
    return "cortesh-pos.dat"


def nome_arquivo_hidr():
    return "hidr.dat"


def nome_arquivo_polinjus():
    return "polinjus.csv"


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


def nome_arquivo_velocidades(caso: str):
    rv = caso.split("_")[-1]
    arquivo = f"velocidades.{rv}"
    return arquivo
