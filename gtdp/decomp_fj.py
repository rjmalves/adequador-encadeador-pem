from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import CQ, FJ
import pathlib
from os.path import join
from os import getenv
from dotenv import load_dotenv

# Dados de entrada:
DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQUIVO_POLINJUS = getenv("ARQUIVO_POLINJUS")


def ajusta_fj(diretorio: str, arquivo: str):

    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # Consideração dos polinômios de jusante
    if dadger.fj is None:
        fj_novo = FJ()
        fj_novo.arquivo = ARQUIVO_POLINJUS
        reg_anterior = dadger.lista_registros(CQ)[-1]
        dadger.cria_registro(reg_anterior, fj_novo)
    else:
        dadger.fj.arquivo = ARQUIVO_POLINJUS

    dadger.escreve_arquivo(diretorio, arquivo)
