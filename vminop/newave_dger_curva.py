import pathlib
from dotenv import load_dotenv
from os import getenv
from os.path import join
import pandas as pd
from inewave.newave.dger import DGer
from inewave.newave.curva import Curva
from inewave.newave.clast import ClasT
from inewave.newave.modif import Modif

DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQ_VMINOP = join(DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_VMINOP"))

ARQUIVO_CLAST = "clast.dat"
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


def adequa_dger(diretorio: str, arq_dger: str):
    print(f"Adequando {arq_dger} ...")
    dger = DGer.le_arquivo(diretorio, arq_dger)
    dger.curva_aversao = 1
    dger.escreve_arquivo(diretorio, arq_dger)


def adequa_curva(diretorio: str, arq_curva: str):
    print(f"Adequando {arq_curva} ...")
    df = pd.read_csv(ARQ_VMINOP, sep=";")
    curva = Curva.le_arquivo(diretorio, arq_curva)
    curva.configuracoes_penalizacao = [1, 11, 1]

    # obtem maior CVU e calcula penalidade
    clast = ClasT.le_arquivo(diretorio, ARQUIVO_CLAST)
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


def adequa_penalizacao_curva(ree: int, penalizacao: float, curva: Curva):
    if curva.custos_penalidades is None:
        return
    if curva.custos_penalidades.loc[
        curva.custos_penalidades["Sistema"] == ree, "Custo"
    ].empty:
        print(f"Adicionando penalização de {penalizacao} para REE {ree}")
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
            print(f"Adicionando curva para REE {ree}/{ano}: {volume_minimo}")
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


def remove_vminp_modif(diretorio: str, arquivo: str):
    modif = Modif.le_arquivo(diretorio, arquivo)
    vminps = modif.vminp()
    if isinstance(vminps, list):
        for r in vminps:
            modif.deleta_registro(r)
    elif vminps is not None:
        modif.deleta_registro(vminps)
    modif.escreve_arquivo(diretorio, arquivo)
