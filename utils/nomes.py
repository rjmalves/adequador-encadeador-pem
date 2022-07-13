def nome_arquivo_dadger(caso: str):
    rv = caso.split("_rv")[1]
    arquivo = f"dadger.rv{rv}"
    return arquivo


def nome_arquivo_dger():
    return "dger.dat"


def nome_arquivo_cvar():
    return "cvar.dat"


def nome_arquivo_modif():
    return "modif.dat"
