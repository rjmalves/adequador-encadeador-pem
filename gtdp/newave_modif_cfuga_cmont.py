from os.path import join
from os import getenv, sep
from dotenv import load_dotenv
import pathlib
import pandas as pd
import numpy as np
from inewave.newave.modelos.modif import USINA, CMONT, CFUGA
from inewave.newave.modif import Modif


NUM_ANOS_ESTUDO = 5

DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQ_CFUGA_CMONT = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_CFUGA_CMONT")
)


def adequa_usina(
    codigo: int, df_usina: pd.DataFrame, modif: Modif, anos_estudo: np.ndarray
):
    print(f"Usina: {codigo}")
    r_usina = modif.usina(codigo=codigo)
    if r_usina is None:
        print("Criou registro USINA")
        r_usina = USINA()
        r_usina.codigo = codigo
        modif.append_registro(r_usina)

    df_ordenado = df_usina.sort_values("mes", ascending=False)
    for ano in anos_estudo:
        for _, linha in df_ordenado.iterrows():
            if linha["cfuga"] is not None:
                adequa_cfuga(modif, codigo, ano, linha["mes"], linha["cfuga"])
            if linha["cmont"] is not None:
                adequa_cmont(modif, codigo, ano, linha["mes"], linha["cmont"])


def adequa_cfuga(modif: Modif, codigo: int, ano: int, mes: int, valor: float):
    modificacoes_usina = modif.modificacoes_usina(codigo)
    for r in modificacoes_usina:
        if isinstance(r, CFUGA):
            if (r.ano == ano) and (r.mes == mes):
                print(f"Alterou nível CFUGA {mes}/{ano}: {valor}")
                r.nivel = valor
                return
    r = CFUGA()
    r.ano = ano
    r.mes = mes
    r.nivel = valor
    modif.cria_registro(modif.usina(codigo=codigo), r)
    print(f"Criou CFUGA {mes}/{ano}: {valor}")


def adequa_cmont(modif: Modif, codigo: int, ano: int, mes: int, valor: float):
    modificacoes_usina = modif.modificacoes_usina(codigo)
    for r in modificacoes_usina:
        if isinstance(r, CMONT):
            if (r.ano == ano) and (r.mes == mes):
                print(f"Alterou nível CMONT {mes}/{ano}: {valor}")
                r.nivel = valor
                return
    r = CMONT()
    r.ano = ano
    r.mes = mes
    r.nivel = valor
    modif.cria_registro(modif.usina(codigo=codigo), r)
    print(f"Criou CMONT {mes}/{ano}: {valor}")


def adequa_cfuga_cmont(diretorio: str, arquivo: str):

    df = pd.read_csv(ARQ_CFUGA_CMONT, sep=";")
    ano_caso = int(diretorio.split(sep)[-2].split("_")[0])
    anos_estudo = np.arange(ano_caso, ano_caso + NUM_ANOS_ESTUDO)
    modif = Modif.le_arquivo(diretorio, arquivo)
    usinas = df["usina"].unique().tolist()
    for u in usinas:
        df_usina = df.loc[df["usina"] == u, :]
        adequa_usina(u, df_usina, modif, anos_estudo)
    modif.escreve_arquivo(diretorio, arquivo)
