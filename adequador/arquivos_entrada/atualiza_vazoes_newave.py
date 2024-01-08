from os.path import join
from shutil import copyfile
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log


def atualiza_vazoes(diretorio: str):
    Log.log().info(f"Adequando VAZOES...")
    arquivo = "vazoes.dat"
    copyfile(
        join(Configuracoes().diretorio_dados_adequacao, arquivo),
        join(diretorio, arquivo),
    )
