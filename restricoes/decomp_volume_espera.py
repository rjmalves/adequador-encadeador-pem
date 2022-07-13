from idecomp.decomp.dadger import Dadger
import pandas as pd
from os import listdir, curdir, sep
from os.path import isfile, isdir, join, normpath
import datetime, time

# Dados de entrada:
arquivo_ve = "/home/pem/estudos/CPAMP/Ciclo_2021-2022/Backtest/casos/novos_volumes_espera.csv"


def ajusta_volume_espera(diretorio: str, arquivo: str, arquivo_ve):
    
    dadger = Dadger.le_arquivo(diretorio, arquivo)

    df_ve = pd.read_csv(arquivo_ve, index_col="data")

    caso = normpath(diretorio).split(sep)[-2]
    ano, mes, _ = caso.split("_")
    ano = int(ano)
    mes = int(mes)
    mes_seguinte = mes % 12 + 1
    ano_seguinte = ano if mes != 12 else ano + 1

    # Acessa o VE de CAMARGOS para saber quantas semanas a frente  
    num_casos_a_frente = len(dadger.ve(codigo=1).volumes)-1

    # Extrai somente as informações que serão utilizadas para atualizar os VE
    indices = list(df_ve.index)
    idx = indices.index(caso)
    idx_linhas = list(range(idx, idx + num_casos_a_frente))
    linhas_ve = df_ve.iloc[idx_linhas, :]
    s = f"{ano_seguinte}_{str(mes_seguinte).zfill(2)}"
    ve_mes = df_ve.loc[df_ve.index.str.contains(s), :]

    # Atualiza os registros VE com os respectivos valores de volume de espera

    usinas = [int(i) for i in list(df_ve)]

    for c in usinas:
        co = str(c)
        dados_ve = linhas_ve[co].tolist() + [ve_mes[co].tolist()[-1]]
        if dadger.ve(codigo = c) is not None:
            dadger.ve(codigo = c).volumes = dados_ve

    dadger.escreve_arquivo(diretorio, arquivo)

  

