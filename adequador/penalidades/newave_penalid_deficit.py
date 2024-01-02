from inewave.newave.sistema import Sistema
from inewave.newave.penalid import Penalid
from inewave.newave.clast import Clast
import pandas as pd
import numpy as np
from adequador.utils.backup import converte_utf8
from adequador.utils.nomes import (
    nome_arquivo_penalid,
    nome_arquivo_sistema,
    nome_arquivo_clast,
)
from adequador.utils.nomes import dados_caso
from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes
from os.path import join


def corrige_deficit_sistema(diretorio: str):
    Log.log().info(f"Adequando DEFICIT...")
    df_deficit = pd.read_csv(Configuracoes().arquivo_custos_deficit, sep=";")
    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()
    ano_caso, _, _ = dados_caso(diretorio)
    anodeck = int(ano_caso)

    arquivo = nome_arquivo_sistema()
    converte_utf8(diretorio, arquivo)
    sistema = Sistema.read(join(diretorio, arquivo))
    sistema.numero_patamares_deficit = 1
    df_sistema = sistema.custo_deficit

    if (
        anodeck in anos
    ):  # checa se faz parte dos anos com mais de 1 patamar de deficit
        ind = anos.index(anodeck)
        # se existir, corrige
        for s in [1, 2, 3, 4]:
            for i in [1, 2, 3, 4]:
                if i == 1:
                    corte = 1
                    custo_def = custo[ind]
                else:
                    corte = 0
                    custo_def = 0
                df_sistema.loc[
                    (df_sistema["codigo_submercado"] == s)
                    & (df_sistema["patamar_deficit"] == i),
                    "corte",
                ] = corte
                df_sistema.loc[
                    (df_sistema["codigo_submercado"] == s)
                    & (df_sistema["patamar_deficit"] == i),
                    "custo",
                ] = custo_def

    sistema.custo_deficit = df_sistema
    sistema.write(join(diretorio, arquivo))


def corrige_penalid(diretorio: str):
    Log.log().info(f"Ajustando PENALIDADES...")

    arquivo = nome_arquivo_penalid()

    # TODO - trocar penalidades de cdef para hibrido

    df_deficit = pd.read_csv(Configuracoes().arquivo_custos_deficit, sep=";")
    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()

    ano_caso, _, _ = dados_caso(diretorio)
    anodeck = int(ano_caso)

    penalid = Penalid.read(join(diretorio, arquivo))
    df_pen = penalid.penalidades

    if (
        anodeck in anos
    ):  # checa se faz parte dos anos com mais de 1 patamar de deficit
        ind = anos.index(anodeck)
        penalidade = custo[ind]

        rees_vazmin = list(range(1, 13))
        rees_ghmin = [4, 5]
        penalidade_desvio = np.ceil(penalidade * 1.01)

        df_pen.loc[
            df_pen["variavel"] == "DESVIO", "valor_R$_MWh"
        ] = penalidade_desvio

        for r in rees_vazmin:
            filtro_vazmin = df_pen.loc[
                (df_pen["codigo_ree_submercado"] == r)
                & (df_pen["variavel"] == "VAZMIN")
            ]
            if len(filtro_vazmin) == 0:
                # necessario criar linha
                linha_nova = {
                    "variavel": "VAZMIN",
                    "valor_R$_MWh": penalidade,
                    "valor_R$_hm3": np.nan,
                    "codigo_ree_submercado": r,
                }
                df_pen.loc[df_pen.shape[0]] = linha_nova
            else:
                df_pen.loc[
                    (df_pen["codigo_ree_submercado"] == r)
                    & (df_pen["variavel"] == "VAZMIN"),
                    "valor_R$_MWh",
                ] = penalidade

        for r in rees_ghmin:
            filtro_ghmin = df_pen.loc[
                (df_pen["codigo_ree_submercado"] == r)
                & (df_pen["variavel"] == "GHMIN")
            ]
            if len(filtro_ghmin) == 0:
                # necessario criar linha
                linha_nova = {
                    "variavel": "GHMIN",
                    "valor_R$_MWh": penalidade,
                    "valor_R$_hm3": np.nan,
                    "codigo_ree_submercado": r,
                }
                df_pen.loc[df_pen.shape[0]] = linha_nova
            else:
                df_pen.loc[
                    (df_pen["codigo_ree_submercado"] == r)
                    & (df_pen["variavel"] == "GHMIN"),
                    "valor_R$_MWh",
                ] = penalidade

    # Troca os valores de penalidades, calculando com base em cada
    # fonte informada

    df_valores = pd.read_csv(
        Configuracoes().arquivo_valores_penalidades_newave, sep=";"
    )
    sistema = Sistema.read(join(diretorio, nome_arquivo_sistema()))
    clast = Clast.read(join(diretorio, nome_arquivo_clast()))
    cdef = sistema.custo_deficit["custo"].max()
    maxcvu = clast.usinas["valor"].max()
    mapa_fontes = {
        "MAXCVU": maxcvu,
        "CDEF": cdef,
    }
    mapa_valores = {
        linha["violacao"]: mapa_fontes[linha["fonte"]] * linha["fator"]
        for _, linha in df_valores.iterrows()
    }
    rees = df_pen["codigo_ree_submercado"].dropna().unique().tolist()
    df_pen_novo = pd.DataFrame(
        columns=[
            "variavel",
            "codigo_ree_submercado",
            "patamar_penalidade",
            "patamar_carga",
            "valor_R$_MWh",
            "valor_R$_hm3",
        ]
    )
    for k, v in mapa_valores.items():
        for r in rees:
            df_pen_novo.loc[df_pen_novo.shape[0], :] = [
                k,
                r,
                1,
                None,
                v,
                None,
            ]
            df_pen_novo.loc[df_pen_novo.shape[0], :] = [
                k,
                r,
                2,
                None,
                None,
                None,
            ]

    penalid.penalidades = df_pen_novo
    penalid.write(join(diretorio, arquivo))
