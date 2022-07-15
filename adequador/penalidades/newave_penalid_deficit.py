from inewave.newave.sistema import Sistema
from inewave.newave.penalid import Penalid
import pandas as pd
import numpy as np
from adequador.utils.backup import converte_utf8
from adequador.utils.nomes import nome_arquivo_penalid, nome_arquivo_sistema
from adequador.utils.nomes import dados_caso
from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes


def corrige_deficit_sistema(diretorio: str):

    Log.log().info(f"Ajustando déficit...")
    df_deficit = pd.read_csv(Configuracoes().arquivo_custos_deficit, sep=";")
    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()
    ano_caso, _, _ = dados_caso(diretorio)
    anodeck = int(ano_caso)

    arquivo = nome_arquivo_sistema()
    converte_utf8(diretorio, arquivo)
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


def corrige_penalid(diretorio: str):

    Log.log().info(f"Ajustando penalidades...")

    arquivo = nome_arquivo_penalid()

    df_deficit = pd.read_csv(Configuracoes().arquivo_custos_deficit, sep=";")
    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()

    ano_caso, _, _ = dados_caso(diretorio)
    anodeck = int(ano_caso)

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
