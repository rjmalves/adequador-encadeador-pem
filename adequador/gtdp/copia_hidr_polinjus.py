from os.path import join
from shutil import copyfile
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import nome_arquivo_hidr, nome_arquivo_polinjus


def copia_hidr(diretorio: str):
    arquivo = nome_arquivo_hidr()
    arq_destino_hidr = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_hidr, arq_destino_hidr)


def copia_polinjus(diretorio: str):
    arquivo = nome_arquivo_polinjus()
    arq_destino_polinjus = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_polinjus, arq_destino_polinjus)
