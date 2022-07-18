from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes
from os import chdir
from adequador.utils.converte import executa_terminal


def ajusta_convertenomes_newave(diretorio: str):
    Log.log().info("Executando CONVERTENOMES...")
    chdir(diretorio)
    executa_terminal([Configuracoes().executavel_convertenomes_newave])
    chdir(Configuracoes().dir_base)
