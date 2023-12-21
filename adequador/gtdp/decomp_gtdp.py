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
    ACVOLMIN,
    ACVOLMAX,
)
from idecomp.decomp.modelos.dadger import UH, FJ, CQ
import datetime
import pandas as pd
from adequador.gtdp.copia_hidr_polinjus import copia_hidr, copia_polinjus
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.nomes import (
    dados_caso,
    nome_arquivo_dadger,
    nome_arquivo_polinjus,
)
from os.path import join


def ajusta_acs(diretorio: str):
    def deleta_ac(dadger: Dadger, u: int, tipo: classmethod):
        reg = dadger.ac(codigo_usina=u, modificacao=tipo)
        if reg is not None:
            dadger.data.remove(reg)

    def adiciona_ac_nposnw(dadger: Dadger, u: int, p: int):
        usina = dadger.uh(codigo_usina=u)
        if usina is not None:
            reg = dadger.ac(codigo_usina=u, modificacao=ACNPOSNW)
            if reg is None:
                # se não existir AC NPOSNW para esta usina, cria
                posicao = dadger.data.get_registers_of_type(ACVAZMIN)[
                    -1
                ]  # Escolhe  posicao para colocar os novos registros
                ac_novo = ACNPOSNW()
                ac_novo.codigo_usina = u
                ac_novo.codigo_posto = p
                dadger.data.add_after(posicao, ac_novo)
            else:
                # se ja existe AC NPOSNW para esta usina, coloca valor correto
                dadger.ac(
                    codigo_usina=u, modificacao=ACNPOSNW
                ).codigo_posto = p

    def adiciona_ac_vertju(dadger: Dadger, u: int):
        usina = dadger.uh(codigo_usina=u)
        if usina is not None:
            reg = dadger.ac(codigo_usina=u, modificacao=ACVERTJU)
            if reg is None:
                # se não existir AC VERTJU para esta usina, cria
                posicao = dadger.data.get_registers_of_type(ACVAZMIN)[
                    -1
                ]  # Escolhe posicao para colocar os novos registros
                ac_novo = ACVERTJU()
                ac_novo.codigo_usina = u
                ac_novo.considera_influencia = 1
                dadger.data.add_after(posicao, ac_novo)
            elif isinstance(reg, list):
                # se ja existe AC VERTJU para esta usina, coloca valor correto - habilitar para 1
                for r in reg:
                    r.considera_influencia = 1
            else:
                # se ja existe AC VERTJU para esta usina, coloca valor correto - habilitar para 1
                reg.considera_influencia = 1

    df_usinas_cmont_cfuga = pd.read_csv(
        Configuracoes().arquivo_cfuga_cmont, sep=";"
    )
    df_nposnw = pd.read_csv(Configuracoes().arquivo_ac_nposnw, sep=";")
    df_nposnw = df_nposnw.loc[~df_nposnw["usinas_nposnw"].str.contains("&")]
    df_vertju = pd.read_csv(Configuracoes().arquivo_ac_vertju, sep=";")

    usinas_cmont_cfuga = df_usinas_cmont_cfuga["usina"].unique().tolist()
    usinas_nposnw = df_nposnw["usinas_nposnw"].tolist()
    postos_nposnw = df_nposnw["postos_nposnw"].tolist()
    usinas_vertju = df_vertju["usinas_vertju"].tolist()

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.read(join(diretorio, arquivo))

    # Lista as usinas consideradas no deck (registros existentes no bloco UH)
    uhs = dadger.data.get_registers_of_type(UH)
    cod_usinas = [r.codigo_usina for r in uhs]

    # Compatabilidade com decks antigos
    deleta_ac(dadger, 46, ACVOLMIN)
    deleta_ac(dadger, 46, ACVOLMAX)

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
            adiciona_ac_nposnw(dadger, int(u), int(p))

    # Depois de ter feito as alterações, escreve arquivo dadger
    dadger.write(join(diretorio, arquivo))


# ======================== Dados GTDP - CFUGA e CMONT

# Pega dados do cfuga_cmont_historico com dados dos ciclos passados do GTDP para
# comparar com COTVOL existente no deck:


def adequa_cfuga_cmont(diretorio: str):
    df_cmont_historico = pd.read_csv(
        Configuracoes().arquivo_cfuga_cmont_historico, sep=";"
    )
    df_cmont_historico = df_cmont_historico.loc[
        ~df_cmont_historico["usina"].str.contains("&")
    ]
    usinas_cmont_historico = df_cmont_historico["usina"].unique().tolist()
    usinas_cmont_historico = [int(u) for u in usinas_cmont_historico]

    # Pega dados do cfuga_cmont.csv, dados do ciclo atual do GTDP, a serem considerados
    df_cmont_cfuga = pd.read_csv(Configuracoes().arquivo_cfuga_cmont, sep=";")
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

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.read(join(diretorio, arquivo))

    # ======================== IDENTIFICA DADOS DO PMO
    # Pega o número total de estágios do deck
    n_est = len(dadger.dp(codigo_submercado=1))

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

        posicao = dadger.data.get_registers_of_type(ACVAZMIN)[
            -1
        ]  # Escolhe uma posicao para colocar os novos registros
        ac_novo = ACCOTVOL()
        ac_novo.codigo_usina = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.ordem = ordem
        ac_novo.coeficiente = cotvol
        dadger.data.add_after(posicao, ac_novo)

    def cria_jusmed(dadger: Dadger, usina, mes, semana, ano, cjus):
        posicao = dadger.data.get_registers_of_type(ACVAZMIN)[
            -1
        ]  # Escolhe uma posicao para colocar os novos registros
        ac_novo = ACJUSMED()
        ac_novo.codigo_usina = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.cota = cjus
        dadger.data.add_after(posicao, ac_novo)

    # ======================== AJUSTE CFUGA (TUCURUI) ========================
    def altera_jusmed_usina(
        dadger: Dadger, usina, meses, anos, inds, cfuga_tucurui
    ):
        for m in [1, 0]:
            reg = dadger.ac(
                codigo_usina=usina, modificacao=ACJUSMED, mes=meses[inds[m]]
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
                    codigo_usina=usina,
                    modificacao=ACCOTVOL,
                    mes=meses[inds[m]],
                    semana=periodo,
                    ordem=1,
                )
                reg_jusmed = dadger.ac(
                    codigo_usina=usina,
                    modificacao=ACJUSMED,
                    mes=meses[inds[m]],
                    semana=periodo,
                )
            else:  # se 2º mês
                periodo = 1
                reg_cotvol = dadger.ac(
                    codigo_usina=usina,
                    modificacao=ACCOTVOL,
                    mes=meses[inds[m]],
                    ordem=1,
                )
                reg_jusmed = dadger.ac(
                    codigo_usina=usina,
                    modificacao=ACJUSMED,
                    mes=meses[inds[m]],
                )

            # confere se existe AC COTVOL e armazena valor
            if reg_cotvol is not None:
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
            altera_jusmed_usina(dadger, usina, meses, anos, inds, cfuga)
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
    dadger.write(join(diretorio, arquivo))


def ajusta_fj(diretorio: str):
    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    converte_utf8(diretorio, arquivo)
    dadger = Dadger.read(join(diretorio, arquivo))

    # Consideração dos polinômios de jusante
    if dadger.fj is None:
        fj_novo = FJ()
        fj_novo.arquivo = nome_arquivo_polinjus()
        dadger.data.append(fj_novo)
    else:
        dadger.fj.arquivo = nome_arquivo_polinjus()

    dadger.write(join(diretorio, arquivo))


def ajusta_gtdp(diretorio: str):
    Log.log().info(f"Adequando GTDP...")

    ajusta_acs(diretorio)
    adequa_cfuga_cmont(diretorio)
    ajusta_fj(diretorio)
    copia_hidr(diretorio)
    copia_polinjus(diretorio)
