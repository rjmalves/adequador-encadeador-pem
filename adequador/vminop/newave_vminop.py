import pandas as pd
from adequador.utils.log import Log
from inewave.newave.dger import DGer
from inewave.newave.curva import Curva
from inewave.newave.clast import ClasT
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
    dger = DGer.le_arquivo(diretorio, arquivo)
    dger.curva_aversao = 1
    dger.escreve_arquivo(diretorio, arquivo)

    arquivo = nome_arquivo_curva()
    converte_utf8(diretorio, arquivo)
    curva = Curva.le_arquivo(diretorio, arquivo)
    curva.configuracoes_penalizacao = [1, 11, 1]

    # obtem maior CVU e calcula penalidade
    clast = ClasT.le_arquivo(diretorio, nome_arquivo_clast())
    df_clast = clast.usinas
    max_cvu = (
        df_clast[["Custo 1", "Custo 2", "Custo 3", "Custo 4", "Custo 5"]]
        .max()
        .max()
    )
    penalizacao = max_cvu * (1 + 0.12) ** (11 / 12)

    for _, linha in df.iterrows():
        adequa_penalizacao_curva(linha["ree"], penalizacao, curva)
        adequa_volumes_curva(
            linha["ree"], linha["mes"], linha["vminop"], curva
        )

    # Remove VMINP do MODIF
    arquivo = nome_arquivo_modif()
    converte_utf8(diretorio, arquivo)
    modif = Modif.le_arquivo(diretorio, arquivo)
    # Apaga VOLMAX vazios
    volmax = modif.volmax()
    if isinstance(volmax, list):
        for v in volmax:
            if v.volume is None:
                modif.deleta_registro(v)
    vminps = modif.vminp()
    if isinstance(vminps, list):
        for r in vminps:
            modif.deleta_registro(r)
    elif vminps is not None:
        modif.deleta_registro(vminps)
    modif.escreve_arquivo(diretorio, arquivo)

    # Remove VOLMIN do PENALID
    arquivo = nome_arquivo_penalid()
    converte_utf8(diretorio, arquivo)
    penalid = Penalid.le_arquivo(diretorio, arquivo)
    df_pen = penalid.penalidades
    indices_deletar = df_pen.loc[df_pen["Chave"] == "VOLMIN"].index.tolist()
    df_pen = df_pen.drop(indices_deletar)
    penalid.penalidades = df_pen
    penalid.escreve_arquivo(diretorio, arquivo)


def adequa_penalizacao_curva(ree: int, penalizacao: float, curva: Curva):
    if curva.custos_penalidades is None:
        return
    if curva.custos_penalidades.loc[
        curva.custos_penalidades["Sistema"] == ree, "Custo"
    ].empty:
        curva.custos_penalidades.loc[curva.custos_penalidades.shape[0]] = [
            ree,
            penalizacao,
        ]
        curva.custos_penalidades.sort_values("Sistema", inplace=True)
    curva.custos_penalidades.loc[
        curva.custos_penalidades["Sistema"] == ree, :
    ] = [
        ree,
        penalizacao,
    ]


def adequa_volumes_curva(
    ree: int, mes: int, volume_minimo: float, curva: Curva
):
    if curva.curva_seguranca is None:
        return

    anos = curva.curva_seguranca["Ano"].unique().tolist()
    num_linhas = curva.curva_seguranca.shape[0]
    for i, ano in enumerate(anos):
        if curva.curva_seguranca.loc[
            (curva.curva_seguranca["REE"] == ree)
            & (curva.curva_seguranca["Ano"] == ano),
            :,
        ].empty:
            curva.curva_seguranca.loc[num_linhas + i] = [ree, ano] + [
                volume_minimo
            ] * 12
        if mes == 999:
            curva.curva_seguranca.loc[
                (curva.curva_seguranca["REE"] == ree)
                & (curva.curva_seguranca["Ano"] == ano),
                :,
            ] = [ree, ano] + [volume_minimo] * 12
        else:
            curva.curva_seguranca.loc[
                (curva.curva_seguranca["REE"] == ree)
                & (curva.curva_seguranca["Ano"] == ano),
                MESES[int(mes - 1)],
            ] = volume_minimo
