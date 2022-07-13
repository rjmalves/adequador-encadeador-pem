def nome_arquivo_dadger(caso: str):
    rv = caso.split("_rv")[1]
    arquivo = f"dadger.rv{rv}"
    return arquivo


def nome_arquivo_dger(caso: str):
    return "dger.dat"


def nome_arquivo_cvar(caso: str):
    return "cvar.dat"


def nome_arquivo_curva(caso: str):
    return "curva.dat"


def nome_arquivo_sistema(caso: str):
    return "sistema.dat"


def nome_arquivo_penalid(caso: str):
    return "penalid.dat"


def nome_arquivo_modif(caso: str):
    return "modif.dat"


def nome_arquivo_hidr(caso: str):
    return "hidr.dat"


def nome_arquivo_polinjus(caso: str):
    return "polinjus.dat"


def nome_arquivo_vazoes(caso: str):
    rv = caso.split("_rv")[1]
    arquivo = f"vazoes.rv{rv}"
    return arquivo
