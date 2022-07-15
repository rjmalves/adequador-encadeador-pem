from idecomp.decomp.dadger import Dadger
import pandas as pd
import pathlib
from adequador.utils.backup import converte_utf8
from utils.log import Log
from utils.nomes import dados_caso, nome_arquivo_dadger
from utils.configuracoes import Configuracoes


def ajusta_volume_espera(diretorio: str):

    Log.log().info(f"Ajustando VEs...")

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    converte_utf8(diretorio, arquivo)
    dadger = Dadger.le_arquivo(diretorio, arquivo)

    df_ve = pd.read_csv(
        Configuracoes().arquivo_volumes_espera, index_col="data"
    )

    caso = pathlib.Path(diretorio).parts[-2]
    ano, mes, _ = caso.split("_")
    ano = int(ano)
    mes = int(mes)
    mes_seguinte = mes % 12 + 1
    ano_seguinte = ano if mes != 12 else ano + 1

    # Acessa o VE de CAMARGOS para saber quantas semanas a frente
    num_casos_a_frente = len(dadger.ve(codigo=1).volumes) - 1

    # Extrai somente as informações que serão utilizadas para atualizar os VE
    indices = list(df_ve.index)
    idx = indices.index(caso)
    idx_linhas = list(range(idx, idx + num_casos_a_frente))
    linhas_ve = df_ve.iloc[idx_linhas, :]
    linhas_ve = linhas_ve.loc[:].astype(float)
    s = f"{ano_seguinte}_{str(mes_seguinte).zfill(2)}"
    ve_mes = df_ve.loc[df_ve.index.str.contains(s), :]
    ve_mes = ve_mes.loc[:].astype(float)

    # Atualiza os registros VE com os respectivos valores de volume de espera
    usinas = [int(i) for i in list(df_ve)]

    for c in usinas:
        co = str(c)
        dados_ve = linhas_ve[co].tolist() + [ve_mes[co].tolist()[-1]]

        if dadger.ve(codigo=c) is not None:
            dadger.ve(codigo=c).volumes = dados_ve

    dadger.escreve_arquivo(diretorio, arquivo)
