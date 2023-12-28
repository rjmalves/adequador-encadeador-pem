import pandas as pd
from adequador.utils.log import Log
from inewave.newave.dger import Dger
from inewave.newave.curva import Curva
from inewave.newave.clast import Clast
from inewave.newave.modif import Modif
from inewave.newave.penalid import Penalid
from adequador.utils.nomes import (
    nome_arquivo_clast,
    nome_arquivo_curva,
    nome_arquivo_dger,
    nome_arquivo_modif,
    nome_arquivo_penalid,
)
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from os.path import join
from datetime import datetime

MESES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def adequa_vminop(diretorio: str):
    Log.log().info(f"Adequando VMINOP...")

    df = pd.read_csv(Configuracoes().arquivo_vminop, sep=";")

    arquivo = nome_arquivo_dger()
    converte_utf8(diretorio, arquivo)
    dger = Dger.read(join(diretorio, arquivo))
    dger.curva_aversao = 1
    dger.write(join(diretorio, arquivo))

    arquivo = nome_arquivo_curva()
    converte_utf8(diretorio, arquivo)
    curva = Curva.read(join(diretorio, arquivo))
    curva.configuracoes_penalizacao = [1, 11, 1]

    # obtem maior CVU e calcula penalidade
    clast = Clast.read(join(diretorio, nome_arquivo_clast()))
    df_clast = clast.usinas
    max_cvu = df_clast["valor"].max()
    penalizacao = max_cvu * (1 + 0.12) ** (11 / 12)

    for _, linha in df.iterrows():
        adequa_penalizacao_curva(linha["ree"], penalizacao, curva)
        adequa_volumes_curva(
            linha["ree"], linha["mes"], linha["vminop"], curva
        )

    curva.write(join(diretorio, arquivo))

    # Remove VMINP do MODIF
    arquivo = nome_arquivo_modif()
    converte_utf8(diretorio, arquivo)
    modif = Modif.read(join(diretorio, arquivo))
    vminps = modif.vminp()
    if isinstance(vminps, list):
        for r in vminps:
            modif.data.remove(r)
    elif vminps is not None:
        modif.data.remove(vminps)
    modif.write(join(diretorio, arquivo))

    # Remove VOLMIN do PENALID
    arquivo = nome_arquivo_penalid()
    converte_utf8(diretorio, arquivo)
    penalid = Penalid.read(join(diretorio, arquivo))
    df_pen = penalid.penalidades
    indices_deletar = df_pen.loc[df_pen["variavel"] == "VOLMIN"].index.tolist()
    df_pen = df_pen.drop(indices_deletar)
    penalid.penalidades = df_pen
    penalid.write(join(diretorio, arquivo))


def adequa_penalizacao_curva(ree: int, penalizacao: float, curva: Curva):
    if curva.custos_penalidades is None:
        return
    if curva.custos_penalidades.loc[
        curva.custos_penalidades["codigo_ree"] == ree, "penalidade"
    ].empty:
        curva.custos_penalidades.loc[curva.custos_penalidades.shape[0]] = [
            ree,
            penalizacao,
        ]
        curva.custos_penalidades.sort_values("codigo_ree", inplace=True)
    curva.custos_penalidades.loc[
        curva.custos_penalidades["codigo_ree"] == ree, :
    ] = [
        ree,
        penalizacao,
    ]


def adequa_volumes_curva(
    ree: int, mes: int, volume_minimo: float, curva: Curva
):
    if curva.curva_seguranca is None:
        return

    # TODO - caso excepcional de VMINOP para o NORTE quando o
    # PMO é de Novembro ou Dezembro ser 18% só nesses meses.
    anos = curva.curva_seguranca["data"].dt.year.unique().tolist()

    for ano in anos:
        if curva.curva_seguranca.loc[
            (curva.curva_seguranca["codigo_ree"] == ree)
            & (curva.curva_seguranca["data"].dt.year == ano),
            :,
        ].empty:
            for m in range(1, 13):
                dic_curva = dict(
                    {
                        "codigo_ree": [ree],
                        "data": [datetime(year=ano, month=m, day=1)],
                        "valor": [volume_minimo],
                    }
                )
                curva.curva_seguranca = pd.concat(
                    [curva.curva_seguranca, pd.DataFrame(dic_curva)]
                )
        if mes == 999:
            curva.curva_seguranca.loc[
                (curva.curva_seguranca["codigo_ree"] == ree)
                & (curva.curva_seguranca["data"].dt.year == ano),
                "valor",
            ] = volume_minimo
        else:
            curva.curva_seguranca.loc[
                (curva.curva_seguranca["codigo_ree"] == ree)
                & (
                    curva.curva_seguranca["data"]
                    == datetime(year=ano, month=mes, day=1)
                ),
                "valor",
            ] = volume_minimo
