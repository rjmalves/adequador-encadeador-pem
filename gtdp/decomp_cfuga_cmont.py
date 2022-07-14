from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import ACCOTVOL, ACJUSMED, ACVAZMIN
import datetime
import pathlib
from dotenv import load_dotenv
from os import getenv
import pandas as pd
from os.path import join

# ======================== Dados GTDP - CFUGA e CMONT

# Pega dados do cfuga_cmont_historico com dados dos ciclos passados do GTDP para
# comparar com COTVOL existente no deck:


DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQUIVO_CFUGA_CMONT_HISTORICO = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_CFUGA_CMONT_HISTORICO")
)

ARQUIVO_CFUGA_CMONT = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_CFUGA_CMONT")
)


def adequa_cfuga_cmont(diretorio: str, arquivo: str):

    df_cmont_historico = pd.read_csv(ARQUIVO_CFUGA_CMONT_HISTORICO, sep=";")
    df_cmont_historico = df_cmont_historico.loc[
        ~df_cmont_historico["usina"].str.contains("&")
    ]
    usinas_cmont_historico = df_cmont_historico["usina"].unique().tolist()
    usinas_cmont_historico = [int(u) for u in usinas_cmont_historico]

    # Pega dados do cfuga_cmont.csv, dados do ciclo atual do GTDP, a serem considerados
    df_cmont_cfuga = pd.read_csv(ARQUIVO_CFUGA_CMONT, sep=";")
    usinas_cmont_cfuga = df_cmont_cfuga["usina"].unique().tolist()

    meses = [
        "JAN",
        "FEV",
        "MAR",
        "ABR",
        "MAI",
        "JUN",
        "JUL",
        "AGO",
        "SET",
        "OUT",
        "NOV",
        "DEZ",
    ]

    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # ======================== IDENTIFICA DADOS DO PMO
    # Pega o número total de estágios do deck
    n_est = len(dadger.dp(subsistema=1))

    # Coleta informações de datas do deck
    dataini = datetime.date(
        day=dadger.dt.dia, month=dadger.dt.mes, year=dadger.dt.ano
    )  # data de inicio do 1º estágio
    anodeck = (dataini + datetime.timedelta(days=7)).year  # ano do PMO

    datasdeck = [dataini]
    for e in range(1, n_est, 1):
        datasdeck = datasdeck + [
            dataini + datetime.timedelta(days=7 * e)
        ]  # datas iniciais de todos os estágios
    pmo = datasdeck[(n_est - 1) - 1].month  # mês do PMO

    if pmo == 12:
        anos = [anodeck, anodeck + 1]
    else:
        anos = [anodeck, anodeck]
    inds = [pmo - 1, pmo % 12]  # índice dos meses 1 e 2

    # ======================== FUNCOES CRIA REGISTRO ========================
    def cria_cotvol(dadger: Dadger, usina, mes, semana, ano, ordem, cmont):

        if ordem == 1:
            cotvol = cmont
        else:
            cotvol = 0

        posicao = dadger.lista_registros(ACVAZMIN)[
            -1
        ]  # Escolhe uma posicao para colocar os novos registros
        ac_novo = ACCOTVOL()
        ac_novo.uhe = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.ordem = ordem
        ac_novo.coeficiente = cotvol
        dadger.cria_registro(posicao, ac_novo)

    def cria_jusmed(dadger: Dadger, usina, mes, semana, ano, cjus):

        posicao = dadger.lista_registros(ACVAZMIN)[
            -1
        ]  # Escolhe uma posicao para colocar os novos registros
        ac_novo = ACJUSMED()
        ac_novo.uhe = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.cota = cjus
        dadger.cria_registro(posicao, ac_novo)

    # ======================== AJUSTE CFUGA (TUCURUI) ========================
    def altera_jusmed_usina(
        dadger: Dadger, usina, meses, anos, inds, cfuga_tucurui
    ):

        for m in [1, 0]:
            reg = dadger.ac(
                uhe=usina, modificacao=ACJUSMED, mes=meses[inds[m]]
            )
            cota = cfuga_tucurui[inds[m]]
            if reg is None:
                cria_jusmed(usina, meses[inds[m]], 1, anos[m], cota)
            else:
                reg.cota = cota

    # ======================== AJUSTE CFUGA E CMONT CONCOMITANTEMENTE ( JIRAU E STO ANTONIO)
    def altera_cotvol_jusmed_usina(
        dadger: Dadger,
        usina,
        n_est,
        meses,
        anos,
        inds,
        cmont_usina,
        cfuga_usina,
        cmont_antes,
    ):

        estagios = []
        for m in [1, 0]:
            for e in range(n_est - 1, 0, -1):
                if not (m == 1 and e > 1):  # se não é o 2º mês e estágio > 1
                    estagios.append(list([m, e]))

        for m, e in estagios:

            if m == 0:  # se 1º mês
                periodo = e
                reg_cotvol = dadger.ac(
                    uhe=usina,
                    modificacao=ACCOTVOL,
                    mes=meses[inds[m]],
                    semana=periodo,
                    ordem=1,
                )
                reg_jusmed = dadger.ac(
                    uhe=usina,
                    modificacao=ACJUSMED,
                    mes=meses[inds[m]],
                    semana=periodo,
                )
            else:  # se 2º mês
                print("DEBUG ",usina,meses[inds[m]])
                periodo = 1
                reg_cotvol = dadger.ac(
                    uhe=usina,
                    modificacao=ACCOTVOL,
                    mes=meses[inds[m]],
                    ordem=1,
                )
                reg_jusmed = dadger.ac(
                    uhe=usina, modificacao=ACJUSMED, mes=meses[inds[m]]
                )

            # confere se existe AC COTVOL e armazena valor
            if reg_cotvol.coeficiente is not None:
                cmont = reg_cotvol.coeficiente
            else:
                cmont = None

            if cmont is None:
                # se não existe AC COTVOL, cria com valor estipulado e armazena cfuga
                for o in [5, 4, 3, 2]:
                    cria_cotvol(
                        dadger,
                        usina,
                        meses[inds[m]],
                        periodo,
                        anos[m],
                        o,
                        0.00,
                    )
                cria_cotvol(
                    dadger,
                    usina,
                    meses[inds[m]],
                    periodo,
                    anos[m],
                    1,
                    cmont_usina[inds[m]],
                )
                cfuga_alterado = cfuga_usina[inds[m]]
            elif cmont is not None and cmont == round(cmont_antes[inds[m]], 2):
                # se existe AC COTVOL e é igual ao valor do gtdp ciclo 1 altera COTVOL para valor estipulado
                reg_cotvol.coeficiente = cmont_usina[inds[m]]
                cfuga_alterado = cfuga_usina[inds[m]]
            elif cmont is not None and cmont != round(cmont_antes[inds[m]], 2):
                # se existe AC COTVOL e NÃO é igual ao valor do gtdp ciclo 1 mantem e calcula cfuga para hqueda
                hqueda = cmont_usina[inds[m]] - cfuga_usina[inds[m]]
                cfuga_alterado = cmont - hqueda

            # confere se existe AC JUSMED e altera ou cria com valor calculado no passo anterior
            if reg_jusmed is not None:
                reg_jusmed.cota = cfuga_alterado
            else:
                cria_jusmed(
                    dadger,
                    usina,
                    meses[inds[m]],
                    periodo,
                    anos[m],
                    cfuga_alterado,
                )



    # ======================== REALIZA ALTERACOES POR USINA ====================
    for usina in usinas_cmont_cfuga:
        if usina not in usinas_cmont_historico:
            # ------ Tucurui:
            # Altera somente cfuga(jusmed)
            cfuga = df_cmont_cfuga.loc[
                df_cmont_cfuga["usina"] == usina, "cfuga"
            ].tolist()
            altera_jusmed_usina(
                dadger, usina, meses, anos, inds, cfuga
            )
        else:
            # ------ Jirau e Santo Antônio:
            # identifica dados do ciclo GTDP passado a serem utilizados para comparação
            # anos_gtdp = list(df_cmont_historico.keys())
            df_cmont_historico_uhe = df_cmont_historico.loc[
                df_cmont_historico["usina"] == str(usina), :
            ]

            anos_gtdp = df_cmont_historico_uhe["ano_inicio"].unique().tolist()
            anos_gtdp = [int(a) for a in anos_gtdp]

            dif = [i - anodeck for i in anos_gtdp]
            dif2 = [i > anodeck for i in anos_gtdp]
            if True in dif2:
                index = dif.index(min(dif))
            else:
                index = dif.index(max(dif))

            ano_referencia_comparacao = anos_gtdp[index]
            cmont_ciclopassado = df_cmont_historico_uhe.loc[
                df_cmont_historico_uhe["ano_inicio"]
                == ano_referencia_comparacao,
                "cmont_historico",
            ].tolist()
            cmont = df_cmont_cfuga.loc[
                df_cmont_cfuga["usina"] == usina, "cmont"
            ].tolist()
            cfuga = df_cmont_cfuga.loc[
                df_cmont_cfuga["usina"] == usina, "cfuga"
            ].tolist()
            altera_cotvol_jusmed_usina(
                dadger,
                usina,
                n_est,
                meses,
                anos,
                inds,
                cmont,
                cfuga,
                cmont_ciclopassado,
            )

    # ----- Escreve novo dadger
    dadger.escreve_arquivo(diretorio, arquivo)
