from os.path import join, isfile
from os import remove
from shutil import copyfile
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import (
    nome_arquivo_hidr,
    nome_arquivo_polinjus,
)


def copia_hidr(diretorio: str):
    arquivo = nome_arquivo_hidr()
    arq_destino_hidr = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_hidr, arq_destino_hidr)


def copia_polinjus(diretorio: str):
    arquivo = nome_arquivo_polinjus()
    # Se existir polinjus.dat no caso, deleta
    arq_polinjus_dat = join(diretorio, "polinjus.dat")
    if isfile(arq_polinjus_dat):
        remove(arq_polinjus_dat)
    arq_destino_polinjus = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_polinjus, arq_destino_polinjus)


def copia_indices_newave(diretorio: str):
    arquivo = "indices.csv"
    arq_destino = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_indices_newave, arq_destino)


def copia_indices_decomp(diretorio: str):
    arquivo = "indices.csv"
    arq_destino = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_indices_decomp, arq_destino)


def copia_volrefsaz(diretorio: str):
    arquivo = "volref_saz.dat"
    arq_destino = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_volrefsaz, arq_destino)


def copia_volumes_referencia_libs(diretorio: str):
    arquivo = "volumes-referencia.csv"
    arq_destino = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_volumes_referencia_libs, arq_destino)
