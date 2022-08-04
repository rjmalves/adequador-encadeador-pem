import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from inewave.newave.modelos.modif import USINA, CMONT, CFUGA
from inewave.newave.modif import Modif
from inewave.newave.exph import Exph
from adequador.gtdp.copia_hidr_polinjus import copia_hidr
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import (
    dados_caso,
    nome_arquivo_exph,
    nome_arquivo_modif,
)
from adequador.utils.log import Log

NUM_ANOS_ESTUDO = 5


def adequa_usina(
    codigo: int, df_usina: pd.DataFrame, modif: Modif, anos_estudo: np.ndarray
):
    r_usina = modif.usina(codigo=codigo)
    if r_usina is None:
        r_usina = USINA()
        r_usina.codigo = codigo
        modif.append_registro(r_usina)

    df_ordenado = df_usina.sort_values("mes")
    for ano in anos_estudo:
        for _, linha in df_ordenado.iterrows():
            adequa_cfuga(modif, codigo, ano, int(linha["mes"]), linha["cfuga"])
    for ano in anos_estudo:
        for _, linha in df_ordenado.iterrows():
            adequa_cmont(modif, codigo, ano, int(linha["mes"]), linha["cmont"])


def adequa_cfuga(modif: Modif, codigo: int, ano: int, mes: int, valor: float):
    modificacoes_usina = modif.modificacoes_usina(codigo)
    mes_anterior = datetime(year=ano, month=mes, day=1) - relativedelta(
        months=1
    )
    anterior = modif.usina(codigo=codigo)
    for r in modificacoes_usina:
        if isinstance(r, CFUGA):
            if (r.ano == ano) and (r.mes == mes):
                modif.deleta_registro(r)
            elif (r.ano == mes_anterior.year) and (
                r.mes == mes_anterior.month
            ):
                anterior = r
    if not np.isnan(valor):
        r = CFUGA()
        r.ano = ano
        r.mes = mes
        r.nivel = valor
        modif.cria_registro(anterior, r)


def adequa_cmont(modif: Modif, codigo: int, ano: int, mes: int, valor: float):
    modificacoes_usina = modif.modificacoes_usina(codigo)
    mes_anterior = datetime(year=ano, month=mes, day=1) - relativedelta(
        months=1
    )
    anterior = modif.usina(codigo=codigo)
    for r in modificacoes_usina:
        if isinstance(r, CMONT):
            if (r.ano == ano) and (r.mes == mes):
                modif.deleta_registro(r)
            elif (r.ano == mes_anterior.year) and (
                r.mes == mes_anterior.month
            ):
                anterior = r
    if not np.isnan(valor):
        r = CMONT()
        r.ano = ano
        r.mes = mes
        r.nivel = valor
        modif.cria_registro(anterior, r)


def adequa_expansoes(exph: Exph):
    # Remove expansões repetidas
    exph.expansoes.drop_duplicates(inplace=True)


def adequa_cfuga_cmont_exph(diretorio: str):

    Log.log().info(f"Adequando GTDP...")

    copia_hidr(diretorio)

    df = pd.read_csv(Configuracoes().arquivo_cfuga_cmont, sep=";")
    ano_caso, _, _ = dados_caso(diretorio)
    ano = int(ano_caso)
    anos_estudo = np.arange(ano, ano + NUM_ANOS_ESTUDO)

    arquivo = nome_arquivo_modif()
    converte_utf8(diretorio, arquivo)

    modif = Modif.le_arquivo(diretorio, arquivo)
    # Apaga VOLMAX vazios
    volmax = modif.volmax()
    if isinstance(volmax, list):
        for v in volmax:
            if v.volume is None:
                modif.deleta_registro(v)

    usinas = df["usina"].unique().tolist()
    for u in usinas:
        df_usina = df.loc[df["usina"] == u, :]
        adequa_usina(u, df_usina, modif, anos_estudo)
    modif.escreve_arquivo(diretorio, arquivo)

    arquivo = nome_arquivo_exph()
    converte_utf8(diretorio, arquivo)

    exph = Exph.le_arquivo(diretorio, arquivo)
    adequa_expansoes(exph)
    exph.escreve_arquivo(diretorio, arquivo)
