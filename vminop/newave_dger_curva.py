from os.path import join, isdir
from os import listdir, getenv
import pandas as pd
from inewave.newave.dger import DGer
from inewave.newave.curva import Curva

DIR_CASOS = "/home/exemplo/backtest"
ARQ_VMINOP = getenv("ARQUIVO_VMINOP_NEWAVE")
ARQ_DGER = "dger.dat"
ARQ_CURVA = "curva.dat"


def adequa_dger(diretorio: str, arq_dger: str):
    print(f"Adequando {arq_dger} ...")
    dger = DGer.le_arquivo(diretorio, arq_dger)
    dger.curva_aversao = 1
    dger.escreve_arquivo(diretorio, arq_dger)


def adequa_curva(df: pd.DataFrame, diretorio: str, arq_curva: str):
    print(f"Adequando {arq_curva} ...")
    curva = Curva.le_arquivo(diretorio, arq_curva)
    curva.configuracoes_penalizacao = [1, 11, 1]
    for _, linha in df.iterrows():
        adequa_penalizacao_curva(linha["ree"], linha["penalizacao"], curva)
        adequa_volumes_curva(linha["ree"], linha["vminop"], curva)


def adequa_penalizacao_curva(ree: int, penalizacao: float, curva: Curva):
    df_penal = curva.custos_penalidades
    if df_penal is None:
        return
    if df_penal.loc[df_penal["Sistema"] == ree, "Custo"].empty:
        print(f"Adicionando penalização de {penalizacao} para REE {ree}")
        curva.custos_penalidades.loc[df_penal.shape[0]] = [ree, penalizacao]
        curva.custos_penalidades.sort_values("Sistema", inplace=True)


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


def adequa_dger_curva(
    df: pd.DataFrame, diretorio: str, arq_dger: str, arq_curva: str
):
    adequa_dger(diretorio, arq_dger)
    adequa_curva(df, diretorio, arq_curva)


pastas_rv0 = [
    d for d in listdir(DIR_CASOS) if isdir(join(DIR_CASOS, d)) and "_rv0" in d
]

df = pd.read_csv("cfuga_cmont.csv", sep=";")

for p in pastas_rv0:
    print(f"Adequando: {p} ...")
    diretorio = join(DIR_CASOS, p, "newave")
    adequa_dger_curva(df, diretorio, ARQ_DGER, ARQ_CURVA)
