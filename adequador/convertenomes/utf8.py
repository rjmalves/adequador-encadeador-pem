from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes
from os import chdir
from os import listdir
from adequador.utils.backup import converte_utf8


def ajusta_utf8(diretorio: str):
    Log.log().info("Executando UTF8...")
    chdir(diretorio)
    for a in listdir("."):
        converte_utf8(".", a)
    chdir(Configuracoes().dir_base)
