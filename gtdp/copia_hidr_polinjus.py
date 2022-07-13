from os.path import join
from os import getenv
from shutil import copyfile
from dotenv import load_dotenv
import pathlib

# Dados de entrada
DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQ_HIDR = join(DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_HIDR"))
ARQ_POLINJUS = join(DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_POLINJUS"))


def copia_hidr(diretorio: str, arquivo: str):
    arq_destino_hidr = join(diretorio, arquivo)
    copyfile(ARQ_HIDR, arq_destino_hidr)


def copia_polinjus(diretorio: str, arquivo: str):
    arq_destino_polinjus = join(diretorio, arquivo)
    copyfile(ARQ_POLINJUS, arq_destino_polinjus)
