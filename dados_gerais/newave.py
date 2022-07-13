from inewave.newave.dger import DGer
from inewave.newave.cvar import CVAR
from os.path import join
import pandas as pd


ARQ_ALTERACOES = "dadosgeraisnewave.csv"
df = pd.read_csv(join(".\dados_gerais", ARQ_ALTERACOES), sep=";")

# Dados de entrada
alteracoes = {
    "Cenário": int(df["vazao"]),  # 3: PAR(p)-A; 1: PAR(p)
    "Max iterações": int(df["maxiter"]),
    "Delta zinf": float(df["deltazinf"]),
    "Deltas consecutivos": int(df["deltaconsecutivo"]),
    "Alpha": int(df["alpha"]),
    "Lambda": int(df["lambda"]),
}


def ajusta_dados_gerais(diretorio: str, arquivo: str):

    # Arquivo de dados gerais
    dger = DGer.le_arquivo(diretorio, arquivo)

    # Modifica, caso desejado, geração de cenários e critério de parada
    dger.consideracao_media_anual_afluencias = alteracoes["Cenário"]
    dger.reducao_automatica_ordem = 0

    dger.num_max_iteracoes = alteracoes["Max iterações"]
    dger.delta_zinf = alteracoes["Delta zinf"]
    dger.deltas_consecutivos = alteracoes["Deltas consecutivos"]

    dger.escreve_arquivo(diretorio, arquivo)


def ajusta_cvar(diretorio: str, arquivo: str):

    # Arquivo de CVAR
    arq_cvar = CVAR.le_arquivo(diretorio, arquivo)
    arq_cvar.valores_constantes = [alteracoes["Alpha"], alteracoes["Lambda"]]
    arq_cvar.escreve_arquivo(diretorio, arquivo)
