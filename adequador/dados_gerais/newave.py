from inewave.newave.dger import DGer
from inewave.newave.cvar import CVAR
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import nome_arquivo_cvar, nome_arquivo_dger

from adequador.utils.log import Log
import pandas as pd


def ajusta_dados_gerais_cvar(diretorio: str):

    Log.log().info(f"Adequando DADOSGERAIS...")

    df = pd.read_csv(Configuracoes().arquivo_dados_gerais_newave, sep=";")

    # Arquivo de dados gerais
    arquivo = nome_arquivo_dger()
    converte_utf8(diretorio, arquivo)
    dger = DGer.le_arquivo(diretorio, arquivo)

    # Modifica, caso desejado, geração de cenários e critério de parada
    dger.consideracao_media_anual_afluencias = int(df["vazao"])
    dger.reducao_automatica_ordem = 0
    dger.num_max_iteracoes = int(df["maxiter"])
    dger.delta_zinf = float(df["deltazinf"])
    dger.deltas_consecutivos = int(df["deltaconsecutivo"])
    dger.cvar = 1

    dger.escreve_arquivo(diretorio, arquivo)

    Log.log().info(f"Adequando CVAR...")

    df = pd.read_csv(Configuracoes().arquivo_dados_gerais_newave, sep=";")

    # Arquivo de CVAR
    arquivo = nome_arquivo_cvar()
    converte_utf8(diretorio, arquivo)
    arq_cvar = CVAR.le_arquivo(diretorio, arquivo)
    arq_cvar.valores_constantes = [int(df["alpha"]), int(df["lambda"])]
    arq_cvar.escreve_arquivo(diretorio, arquivo)
