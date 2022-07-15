from os.path import isfile, join
from shutil import copyfile
from adequador.utils.converte import converte_codificacao
from adequador.utils.configuracoes import Configuracoes


def realiza_backup(diretorio: str, arquivo: str):
    arquivo_backup = f"backup_{arquivo}"
    if not isfile(join(diretorio, arquivo_backup)) and isfile(
        join(diretorio, arquivo)
    ):
        copyfile(join(diretorio, arquivo), join(diretorio, arquivo_backup))


def converte_utf8(diretorio: str, arquivo: str):
    if isfile(join(diretorio, arquivo)):
        converte_codificacao(
            join(diretorio, arquivo),
            Configuracoes().script_converte_codificacao,
        )
