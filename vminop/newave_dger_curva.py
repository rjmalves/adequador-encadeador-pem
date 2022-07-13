from os.path import join, isdir
from os import listdir, getenv
import pandas as pd
from inewave.newave.dger import DGer
from inewave.newave.curva import Curva
from inewave.newave.clast import ClasT

DIR_CASOS = "/home/exemplo/backtest"
ARQ_VMINOP = getenv("ARQUIVO_VMINOP_NEWAVE")
ARQ_DGER = "dger.dat"
ARQ_CURVA = "curva.dat"
ARQ_CLAST = "clast.dat"


def adequa_dger(diretorio: str, arq_dger: str):
    print(f"Adequando {arq_dger} ...")
    dger = DGer.le_arquivo(diretorio, arq_dger)
    dger.curva_aversao = 1
    dger.escreve_arquivo(diretorio, arq_dger)


def adequa_curva(df: pd.DataFrame, diretorio: str, arq_curva: str, arq_clast: str):
    print(f"Adequando {arq_curva} ...")
    curva = Curva.le_arquivo(diretorio, arq_curva)
    curva.configuracoes_penalizacao = [1, 11, 1]

    # obtem maior CVU e calcula penalidade
    clast = ClasT.le_arquivo(diretorio, arq_clast)
    df_clast = clast.usinas
    max_cvu = df_clast[["Custo 1","Custo 2","Custo 3","Custo 4","Custo 5"]].max().max()
    penalizacao = max_cvu * (1+0.12)**(11/12)

    for _, linha in df.iterrows():
        adequa_penalizacao_curva(linha["ree"], penalizacao, curva)
        adequa_volumes_curva(linha["ree"], linha["vminop"], curva)


def adequa_penalizacao_curva(ree: int, penalizacao: float, curva: Curva):
    df_penal = curva.custos_penalidades
    if df_penal is None:
        return
    if df_penal.loc[df_penal["Sistema"] == ree, "Custo"].empty:
        print(f"Adicionando penalização de {penalizacao} para REE {ree}")
        curva.custos_penalidades.loc[df_penal.shape[0]] = [ree, penalizacao]
        curva.custos_penalidades.sort_values("Sistema", inplace=True)
    # adicionar aqui caso não seja empty, temos que garantir que esta o valor novo


def adequa_volumes_curva(ree: int, volume_minimo: float, curva: Curva):
    df_curva = curva.curva_seguranca
    if df_curva is None:
        return
    anos = df_curva["Ano"].unique().tolist()
    num_linhas = df_curva.shape[0]
    for i, ano in enumerate(anos):
        if df_curva.loc[
            (df_curva["REE"] == ree) & (df_curva["Ano"] == ano), :
        ].empty:
            print(f"Adicionando curva para REE {ree}/{ano}: {volume_minimo}")
            curva.custos_penalidades.loc[num_linhas + i] = [ree, ano] + [
                volume_minimo
            ] * 12
    # adicionar aqui, conferir o mês, se é 999 ou se tem variação por mês, para pegar o caso de dezembro do Norte
    # tem que em algum lugar excluir os VMINPs do modif também


def adequa_dger_curva(
    df: pd.DataFrame, diretorio: str, arq_dger: str, arq_curva: str, arq_clast: str
):
    adequa_dger(diretorio, arq_dger)
    adequa_curva(df, diretorio, arq_curva, arq_clast)


pastas_rv0 = [
    d for d in listdir(DIR_CASOS) if isdir(join(DIR_CASOS, d)) and "_rv0" in d
]

df = pd.read_csv("vminop.csv", sep=";")

for p in pastas_rv0:
    print(f"Adequando: {p} ...")
    diretorio = join(DIR_CASOS, p, "newave")
    adequa_dger_curva(df, diretorio, ARQ_DGER, ARQ_CURVA, ARQ_CLAST)
