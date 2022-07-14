from inewave.newave.sistema import Sistema
from inewave.newave.penalid import Penalid
import pandas as pd
import numpy as np
import pathlib
from dotenv import load_dotenv
from os import getenv, sep
from os.path import join
from utils.log import Log

# Dados de entrada:
DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQUIVO_CUSTOS_DEFICIT = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_CUSTOS_DEFICIT")
)


def corrige_deficit_sistema(diretorio: str, arquivo: str):

    Log.log().info(f"Ajustando déficit...")

    df_deficit = pd.read_csv(ARQUIVO_CUSTOS_DEFICIT, sep=";")
    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()

    anodeck = int(diretorio.split(sep)[-2].split("_")[0])
    sistema = Sistema.le_arquivo(diretorio, arquivo)
    sistema.numero_patamares_deficit = 1
    df_sistema = sistema.custo_deficit

    if (
        anodeck in anos
    ):  # checa se faz parte dos anos com mais de 1 patamar de deficit
        ind = anos.index(anodeck)
        # se existir, corrige
        for s in [1, 2, 3, 4]:
            for i in [2, 3, 4]:
                df_sistema.loc[
                    df_sistema["Num. Subsistema"] == s, "Corte Pat. " + str(i)
                ] = 0.00
                df_sistema.loc[
                    df_sistema["Num. Subsistema"] == s, "Custo Pat. " + str(i)
                ] = 0.00
            i = 1
            df_sistema.loc[
                df_sistema["Num. Subsistema"] == s, "Corte Pat. " + str(i)
            ] = 1.00
            df_sistema.loc[
                df_sistema["Num. Subsistema"] == s, "Custo Pat. " + str(i)
            ] = custo[ind]

    sistema.custo_deficit = df_sistema
    sistema.escreve_arquivo(diretorio, arquivo)


def corrige_penalid(diretorio: str, arquivo: str):

    Log.log().info(f"Ajustando penalidades...")

    df_deficit = pd.read_csv(ARQUIVO_CUSTOS_DEFICIT, sep=";")
    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()

    anodeck = int(diretorio.split(sep)[-2].split("_")[0])

    penalid = Penalid.le_arquivo(diretorio, arquivo)
    df_pen = penalid.penalidades

    if (
        anodeck in anos
    ):  # checa se faz parte dos anos com mais de 1 patamar de deficit
        ind = anos.index(anodeck)
        penalidade = custo[ind]

        rees_vazmin = list(range(1, 13))
        rees_ghmin = [4, 5]
        penalidade_desvio = np.ceil(penalidade * 1.001)

        indices_deletar = df_pen.loc[
            df_pen["Chave"] == "VOLMIN"
        ].index.tolist()
        df_pen = df_pen.drop(indices_deletar)

        df_pen.loc[
            df_pen["Chave"] == "DESVIO", "Penalidade 1"
        ] = penalidade_desvio

        for r in rees_vazmin:
            filtro_vazmin = df_pen.loc[
                (df_pen["Subsistema"] == r) & (df_pen["Chave"] == "VAZMIN")
            ]
            if len(filtro_vazmin) == 0:
                # necessario criar linha
                linha_nova = {
                    "Chave": "VAZMIN",
                    "Penalidade 1": penalidade,
                    "Penalidade 2": np.nan,
                    "Subsistema": r,
                }
                df_pen.loc[df_pen.shape[0]] = linha_nova
            else:
                df_pen.loc[
                    (df_pen["Subsistema"] == r)
                    & (df_pen["Chave"] == "VAZMIN"),
                    "Penalidade 1",
                ] = penalidade

        for r in rees_ghmin:
            filtro_ghmin = df_pen.loc[
                (df_pen["Subsistema"] == r) & (df_pen["Chave"] == "GHMIN")
            ]
            if len(filtro_ghmin) == 0:
                # necessario criar linha
                linha_nova = {
                    "Chave": "GHMIN",
                    "Penalidade 1": penalidade,
                    "Penalidade 2": np.nan,
                    "Subsistema": r,
                }
                df_pen.loc[df_pen.shape[0]] = linha_nova
            else:
                df_pen.loc[
                    (df_pen["Subsistema"] == r) & (df_pen["Chave"] == "GHMIN"),
                    "Penalidade 1",
                ] = penalidade
    penalid.penalidades = df_pen
    penalid.escreve_arquivo(diretorio, arquivo)
