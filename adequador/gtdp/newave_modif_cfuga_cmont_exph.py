import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from inewave.newave.modelos.modif import USINA, CMONT, CFUGA
from inewave.newave.modif import Modif
from inewave.newave.exph import Exph
from inewave.newave import Dger
from inewave.libs.modelos.usinas_hidreletricas import (
    VolumeReferencialPeriodo,
    VolumeReferencialTipoPadrao,
)
from adequador.gtdp.copia_hidr_polinjus import (
    copia_hidr,
    copia_polinjus,
    copia_indices_newave,
    copia_volrefsaz,
)
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import (
    dados_caso,
    nome_arquivo_exph,
    nome_arquivo_modif,
)
from adequador.utils.log import Log
from os.path import join

NUM_ANOS_ESTUDO = 5


def adequa_usina(
    data_inicio_estudo: datetime,
    codigo: int,
    df_usina: pd.DataFrame,
    modif: Modif,
    anos_estudo: np.ndarray,
):
    r_usina = modif.usina(codigo=codigo)
    if r_usina is None:
        r_usina = USINA()
        r_usina.codigo = codigo
        modif.data.append(r_usina)

    df_ordenado = df_usina.sort_values("mes")
    for ano in anos_estudo:
        for _, linha in df_ordenado.iterrows():
            adequa_cfuga(
                data_inicio_estudo,
                modif,
                codigo,
                ano,
                int(linha["mes"]),
                linha["cfuga"],
            )
    for ano in anos_estudo:
        for _, linha in df_ordenado.iterrows():
            adequa_cmont(modif, codigo, ano, int(linha["mes"]), linha["cmont"])


def adequa_cfuga(
    data_inicio_estudo: datetime,
    modif: Modif,
    codigo: int,
    ano: int,
    mes: int,
    valor: float,
):
    # Premissa:
    # Não altera CFUGA para UHE 275 nos dois primeiro meses de estudo
    mes_estagio = datetime(year=ano, month=mes, day=1)
    delta_1mes = relativedelta(months=1)
    if codigo == 275 and (
        data_inicio_estudo <= mes_estagio <= data_inicio_estudo + delta_1mes
    ):
        return
    modificacoes_usina = modif.modificacoes_usina(codigo)
    mes_anterior = mes_estagio - delta_1mes
    anterior = modif.usina(codigo=codigo)
    for r in modificacoes_usina:
        if isinstance(r, CFUGA):
            if r.data_inicio == mes_estagio:
                modif.data.remove(r)
            elif r.data_inicio == mes_anterior:
                anterior = r
    if not np.isnan(valor):
        r = CFUGA()
        r.data_inicio = mes_estagio
        r.nivel = valor
        modif.data.add_after(anterior, r)


def adequa_cmont(modif: Modif, codigo: int, ano: int, mes: int, valor: float):
    modificacoes_usina = modif.modificacoes_usina(codigo)
    mes_anterior = datetime(year=ano, month=mes, day=1) - relativedelta(
        months=1
    )
    anterior = modif.usina(codigo=codigo)
    for r in modificacoes_usina:
        if isinstance(r, CMONT):
            if r.data_inicio == datetime(year=ano, month=mes, day=1):
                modif.data.remove(r)
            elif r.data_inicio == mes_anterior:
                anterior = r
    if not np.isnan(valor):
        r = CMONT()
        r.data_inicio = datetime(year=ano, month=mes, day=1)
        r.nivel = valor
        modif.data.add_after(anterior, r)


def adequa_expansoes(exph: Exph) -> bool:
    # Remove expansões repetidas
    if exph.expansoes is not None:
        exph.expansoes.drop_duplicates(inplace=True)
        return True
    return False


def gera_volumes_referencia_libs(diretorio: str):
    dger = Dger.read(join(diretorio, "dger.dat"))
    df = pd.read_csv(Configuracoes().arquivo_volumes_referencia_libs)

    data_inicio_estudo = datetime(
        dger.ano_inicio_estudo, dger.mes_inicio_estudo, 1
    )
    num_anos_estudo = dger.num_anos_estudo + dger.num_anos_pos_estudo

    data_fim_estudo = datetime(
        data_inicio_estudo.year + num_anos_estudo - 1, 12, 1
    )
    meses = pd.date_range(data_inicio_estudo, data_fim_estudo, freq="MS")

    with open(join(diretorio, "volumes-referencia.csv"), "w") as arq:
        # Escreve o tipo de volume de referência
        ri = VolumeReferencialTipoPadrao()
        ri.tipo_referencia = 1
        ri.write(arq)

        for indice_mes in range(len(meses)):
            for u in df["codigo_usina"].unique():
                mes_inicio = meses[indice_mes]
                mes_fim = meses[indice_mes]
                r = VolumeReferencialPeriodo()
                r.codigo_usina = u
                r.data_inicio = mes_inicio
                r.data_fim = mes_fim
                r.volume_referencia = df.loc[
                    (df["codigo_usina"] == u)
                    & (df["mes"] == mes_inicio.month),
                    "volume_referencia",
                ].iloc[0]

                r.write(arq)


def adequa_cfuga_cmont_exph(diretorio: str):
    Log.log().info(f"Adequando GTDP...")

    copia_hidr(diretorio)
    copia_polinjus(diretorio)
    copia_indices_newave(diretorio)
    copia_volrefsaz(diretorio)
    gera_volumes_referencia_libs(diretorio)

    df = pd.read_csv(Configuracoes().arquivo_cfuga_cmont, sep=";")
    ano_caso, mes_caso, _ = dados_caso(diretorio)
    ano = int(ano_caso)
    mes = int(mes_caso)
    data_inicio_estudo = datetime(ano, mes, 1)
    anos_estudo = np.arange(ano, ano + NUM_ANOS_ESTUDO)

    arquivo = nome_arquivo_modif()
    converte_utf8(diretorio, arquivo)

    modif = Modif.read(join(diretorio, arquivo))
    # Apaga VOLMAX vazios
    volmax = modif.volmax()
    if isinstance(volmax, list):
        for v in volmax:
            if v.volume is None:
                modif.data.remove(v)
    elif volmax is not None:
        if volmax.volume is None:
            modif.data.remove(volmax)

    usinas = df["usina"].unique().tolist()
    for u in usinas:
        df_usina = df.loc[df["usina"] == u, :]
        adequa_usina(data_inicio_estudo, u, df_usina, modif, anos_estudo)
    modif.write(join(diretorio, arquivo))

    arquivo = nome_arquivo_exph()
    converte_utf8(diretorio, arquivo)

    exph = Exph.read(join(diretorio, arquivo))
    if adequa_expansoes(exph):
        exph.write(join(diretorio, arquivo))
