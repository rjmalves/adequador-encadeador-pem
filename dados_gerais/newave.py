from inewave.newave.dger import DGer
from inewave.newave.cvar import CVAR
from os.path import join
from os import getenv
from dotenv import load_dotenv
import pathlib
import pandas as pd


DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = getenv("DIRETORIO_DADOS_ADEQUACAO")

ARQUIVO_DADOS_GERAIS_NEWAVE = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_DADOS_GERAIS_NEWAVE")
)


def ajusta_dados_gerais(diretorio: str, arquivo: str):

    df = pd.read_csv(ARQUIVO_DADOS_GERAIS_NEWAVE, sep=";")

    # Arquivo de dados gerais
    dger = DGer.le_arquivo(diretorio, arquivo)

    # Modifica, caso desejado, geração de cenários e critério de parada
    dger.consideracao_media_anual_afluencias = int(df["vazao"])
    dger.reducao_automatica_ordem = 0
    dger.num_max_iteracoes = int(df["maxiter"])
    dger.delta_zinf = float(df["deltazinf"])
    dger.deltas_consecutivos = int(df["deltaconsecutivo"])

    dger.escreve_arquivo(diretorio, arquivo)


def ajusta_cvar(diretorio: str, arquivo: str):

    df = pd.read_csv(ARQUIVO_DADOS_GERAIS_NEWAVE, sep=";")

    # Arquivo de CVAR
    arq_cvar = CVAR.le_arquivo(diretorio, arquivo)
    arq_cvar.valores_constantes = [int(df["alpha"]), int(df["lambda"])]
    arq_cvar.escreve_arquivo(diretorio, arquivo)
