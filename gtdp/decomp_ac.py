from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import (
    ACCOTVOL,
    ACJUSMED,
    ACCOTVAZ,
    ACPROESP,
    ACPERHID,
    ACNCHAVE,
    ACTIPERH,
    ACVERTJU,
    ACNPOSNW,
    ACVAZMIN,
)
from idecomp.decomp.modelos.dadger import UH
from os.path import join
from os import getenv
import pathlib
from dotenv import load_dotenv
import datetime
import pandas as pd

# Dados de entrada:

DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQUIVO_DADOS_GERAIS_NEWAVE = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_DADOS_GERAIS_NEWAVE")
)

ARQUIVO_USINAS_CMONT_CFUGA = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_CFUGA_CMONT")
)

ARQUIVO_AC_NPOSNW = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_AC_NPOSNW")
)

ARQUIVO_AC_VERTJU = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_AC_VERTJU")
)


def ajusta_acs(diretorio: str, arquivo: str):
    def deleta_ac(dadger: Dadger, u: int, tipo: classmethod):
        reg = dadger.ac(uhe=u, modificacao=tipo)
        if reg is not None:
            dadger.deleta_registro(reg)

    def adiciona_ac_nposnw(dadger: Dadger, u: int, p: int):
        usina = dadger.uh(codigo=u)
        if usina is not None:
            reg = dadger.ac(uhe=u, modificacao=ACNPOSNW)
            if reg is None:
                # se não existir AC NPOSNW para esta usina, cria
                posicao = dadger.lista_registros(ACVAZMIN)[
                    -1
                ]  # Escolhe  posicao para colocar os novos registros
                ac_novo = ACNPOSNW()
                ac_novo.uhe = u
                ac_novo.posto = p
                dadger.cria_registro(posicao, ac_novo)
            else:
                # se ja existe AC NPOSNW para esta usina, coloca valor correto
                dadger.ac(uhe=u, modificacao=ACNPOSNW).posto = p

    def adiciona_ac_vertju(dadger: Dadger, u: int):

        usina = dadger.uh(codigo=u)
        if usina is not None:
            reg = dadger.ac(uhe=u, modificacao=ACVERTJU)
            if reg is None:
                # se não existir AC VERTJU para esta usina, cria
                posicao = dadger.lista_registros(ACVAZMIN)[
                    -1
                ]  # Escolhe posicao para colocar os novos registros
                ac_novo = ACVERTJU()
                ac_novo.uhe = u
                ac_novo.influi = 1
                dadger.cria_registro(posicao, ac_novo)
            else:
                # se ja existe AC VERTJU para esta usina, coloca valor correto - habilitar para 1
                dadger.ac(uhe=u, modificacao=ACVERTJU).influi = 1

    df_usinas_cmont_cfuga = pd.read_csv(ARQUIVO_USINAS_CMONT_CFUGA, sep=";")
    df_nposnw = pd.read_csv(ARQUIVO_AC_NPOSNW, sep=";")
    df_nposnw = df_nposnw.loc[~df_nposnw["usinas_nposnw"].str.contains("&")]
    df_vertju = pd.read_csv(ARQUIVO_AC_VERTJU, sep=";")

    usinas_cmont_cfuga = df_usinas_cmont_cfuga["usina"].unique().tolist()
    usinas_nposnw = df_nposnw["usinas_nposnw"].tolist()
    postos_nposnw = df_nposnw["postos_nposnw"].tolist()
    usinas_vertju = df_vertju["usinas_vertju"].tolist()

    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # Lista as usinas consideradas no deck (registros existentes no bloco UH)
    uhs = dadger.lista_registros(UH)
    cod_usinas = [r.codigo for r in uhs]

    for u in cod_usinas:

        # Deleta registros AC PROESP, PERHID, NCHAVE, COTVAZ, TIPERH para todas as usinas que possuem.
        # O objetivo é que os dados considerados passem a ser os revisados pelo GTDP.
        deleta_ac(dadger, u, ACPROESP)
        deleta_ac(dadger, u, ACPERHID)
        deleta_ac(dadger, u, ACNCHAVE)
        deleta_ac(dadger, u, ACCOTVAZ)
        deleta_ac(dadger, u, ACTIPERH)

        # Deleta AC COTVOL e JUSMED para todas as usinas, menos uhs definidas acima, tipicamente 275, 285 e 287
        # (Tucuruí, Santo Antônio e Jirau) visto que essas possuem cota de montante e de jusante variáveis
        # sazonais conforme o GTDP
        if u not in usinas_cmont_cfuga:

            deleta_ac(dadger, u, ACCOTVOL)
            deleta_ac(dadger, u, ACJUSMED)

    for u in usinas_vertju:
        adiciona_ac_vertju(dadger, u)

    # Adiciona, em casos antes de 2017, registros AC NPOSNW conforme usinas_nposnw e postos_nposnw informados.
    # Em decks de 2015 e 2016, o número do posto de acoplamento não era alterado através de alteração de cadastro
    # via mnemônico NPOSNW (visto que a funcionalidade não existia na época). Então, para estes anos, serão inseridos
    # os postos via NPOSNW com base nos decks mais próximos, no caso, 2017. Esta informação é utilizada pelo Gevazp.

    # Coleta informações de datas do deck
    dataini = datetime.date(
        day=dadger.dt.dia, month=dadger.dt.mes, year=dadger.dt.ano
    )  # data de inicio do 1º estágio
    ano_caso = (dataini + datetime.timedelta(days=7)).year  # ano do PMO

    if ano_caso < 2017:
        for u, p in zip(usinas_nposnw, postos_nposnw):
            adiciona_ac_nposnw(dadger, u, p)

    # Depois de ter feito as alterações, escreve arquivo dadger
    dadger.escreve_arquivo(diretorio, arquivo)
