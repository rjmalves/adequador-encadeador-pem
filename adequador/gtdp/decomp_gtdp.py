from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import (
    ACCOTVOL,
    ACJUSMED,
    ACNUMPOS,
    ACNUMJUS,
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
    ACVSVERT,
    ACVMDESV,
)
from idecomp.decomp.modelos.dadger import TI, FA, VL, VA, VU
from shutil import copyfile
import datetime
import pandas as pd
import numpy as np
from adequador.gtdp.copia_hidr_polinjus import copia_hidr, copia_polinjus
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.nomes import (
    dados_caso,
    nome_arquivo_dadger,
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

    # def adiciona_ac_vertju(dadger: Dadger, u: int):
    #     usina = dadger.uh(codigo_usina=u)
    #     if usina is not None:
    #         reg = dadger.ac(codigo_usina=u, modificacao=ACVERTJU)
    #         if reg is None:
    #             # se não existir AC VERTJU para esta usina, cria
    #             posicao = dadger.data.get_registers_of_type(ACVAZMIN)[
    #                 -1
    #             ]  # Escolhe posicao para colocar os novos registros
    #             ac_novo = ACVERTJU()
    #             ac_novo.codigo_usina = u
    #             ac_novo.considera_influencia = 1
    #             dadger.data.add_after(posicao, ac_novo)
    #         elif isinstance(reg, list):
    #             # se ja existe AC VERTJU para esta usina, coloca valor correto - habilitar para 1
    #             for r in reg:
    #                 r.considera_influencia = 1
    #         else:
    #             # se ja existe AC VERTJU para esta usina, coloca valor correto - habilitar para 1
    #             reg.considera_influencia = 1

    def remove_acs_vertju(dadger: Dadger):
        usina = dadger.uh(codigo_usina=u)
        if usina is not None:
            reg = dadger.ac(codigo_usina=u, modificacao=ACVERTJU)
            if reg is not None:
                dadger.data.remove(reg)

    df_usinas_cmont_cfuga = pd.read_csv(
        Configuracoes().arquivo_cfuga_cmont, sep=";"
    )
    df_nposnw = pd.read_csv(Configuracoes().arquivo_ac_nposnw, sep=";")
    df_nposnw = df_nposnw.loc[~df_nposnw["usinas_nposnw"].str.contains("&")]
    # df_vertju = pd.read_csv(Configuracoes().arquivo_ac_vertju, sep=";")

    usinas_cmont_cfuga = df_usinas_cmont_cfuga["usina"].unique().tolist()
    usinas_nposnw = df_nposnw["usinas_nposnw"].tolist()
    postos_nposnw = df_nposnw["postos_nposnw"].tolist()
    # usinas_vertju = df_vertju["usinas_vertju"].tolist()

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.read(join(diretorio, arquivo))

    # Lista as usinas consideradas no deck (registros existentes no bloco UH)
    uhs = dadger.uh()
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

    # Não é mais necessário usar AC VERTJU, visto que o hidr deve ser editado com esse flag, agora
    # que os três modelos já usam adequadamente esta informação.
    # for u in usinas_vertju:
    #     adiciona_ac_vertju(dadger, u)
    remove_acs_vertju(dadger)

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

    # ======================== AJUSTE CMONT (BELO MONTE) ========================
    def altera_cotvol_usina(
        dadger: Dadger, usina, meses, anos, inds, cmont_bm
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
            else:  # se 2º mês
                periodo = 1
                reg_cotvol = dadger.ac(
                    codigo_usina=usina,
                    modificacao=ACCOTVOL,
                    mes=meses[inds[m]],
                    ordem=1,
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
                    cmont_bm[inds[m]],
                )
            else:
                # se existe AC COTVOL, garante que é o valor estipulado
                reg_cotvol.coeficiente = cmont_bm[inds[m]]

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
                cria_jusmed(dadger, usina, meses[inds[m]], 1, anos[m], cota)
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
            # ------ Belo Monte>
            # Altera somente cmont(cotvol)
            # ------ Tucurui:
            # Altera somente cfuga(jusmed)
            cmont = df_cmont_cfuga.loc[
                df_cmont_cfuga["usina"] == usina, "cmont"
            ].tolist()
            if any([not np.isnan(c) for c in cmont]):
                altera_cotvol_usina(dadger, usina, meses, anos, inds, cmont)
            cfuga = df_cmont_cfuga.loc[
                df_cmont_cfuga["usina"] == usina, "cfuga"
            ].tolist()
            if any([not np.isnan(c) for c in cfuga]):
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
    fj = dadger.fj
    if fj is not None:
        dadger.data.remove(fj)
    fa = dadger.fa
    if fa is None:
        r = FA()
        r.arquivo = "indices.csv"
        dadger.data.add_after(dadger.ev, r)

    dadger.write(join(diretorio, arquivo))


def copia_indices(diretorio: str):
    arquivo = "indices.csv"
    arq_destino = join(diretorio, arquivo)
    copyfile(Configuracoes().arquivo_indices, arq_destino)


def ajusta_representacao_fontes(diretorio: str):
    def ajusta_codigos_uh_fontes(dadger: Dadger):
        for k, v in mapa_fontes:
            uh_fontes = dadger.uh(codigo_usina=k)
            uh_fontes.codigo_usina = v

    def ajusta_codigos_mp_fontes(dadger: Dadger):
        for k, v in mapa_fontes:
            mp_fontes = dadger.mp(codigo_usina=k)
            mp_fontes.codigo_usina = v

    def ajusta_codigos_fd_fontes(dadger: Dadger):
        for k, v in mapa_fontes:
            fd_fontes = dadger.fd(codigo_usina=k)
            fd_fontes.codigo_usina = v

    def ajusta_acs_vl_va_vu_fontes(dadger: Dadger):
        ### Alterações de Fontes A -> C
        # AC 183 NUMPOS 300 -> AC 146 NUMPOS 300
        ac_numpos = dadger.ac(codigo_usina=183, modificacao=ACNUMPOS)
        if ac_numpos is not None:
            ac_numpos.codigo_usina = 146
        # AC 183 NPOSNW 303 -> AC 146 NPOSNW 303
        ac_nposnw = dadger.ac(codigo_usina=183, modificacao=ACNPOSNW)
        if ac_nposnw is not None:
            ac_nposnw.codigo_usina = 146
        # AC 183 VAZMIN 0 -> AC 146 VAZMIN 0
        ac_vazmin = dadger.ac(codigo_usina=183, modificacao=ACVAZMIN)
        if ac_vazmin is not None:
            ac_vazmin.codigo_usina = 146
            ac_vazmin.limite_vazao = 0.0
        # Retira AC 124 NUMJUS 183
        ac_numjus = dadger.ac(codigo_usina=124, modificacao=ACNUMJUS)
        if ac_numjus is not None:
            dadger.data.remove(ac_numjus)
        # TI 183 -> TI 146
        ti_antigo = dadger.ti(codigo_usina=183)
        ti_novo = TI()
        ti_novo.codigo_usina = 146
        ti_novo.taxa = ti_antigo.taxa
        dadger.data.add_after(ti_antigo, ti_novo)
        dadger.data.remove(ti_antigo)

        ultimo_registro_adicionado_vazao_lateral = dadger.cq()[-1]
        # Insere VL 146 1
        vl_fontesC = dadger.vl(codigo_usina_influenciada=146)
        if vl_fontesC is None:
            vl_fontesC = VL()
            vl_fontesC.codigo_usina_influenciada = 146
            vl_fontesC.fator_impacto_defluencia = 1
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, vl_fontesC
            )
        ultimo_registro_adicionado_vazao_lateral = vl_fontesC
        # Insere VU 146 147 1
        vu_fontesC = dadger.vu(
            codigo_usina_influenciada=146, codigo_usina_influenciadora=147
        )
        if vu_fontesC is None:
            vu_fontesC = VU()
            vu_fontesC.codigo_usina_influenciada = 146
            vu_fontesC.codigo_usina_influenciadora = 147
            vu_fontesC.fator_impacto_defluencia = 1
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, vu_fontesC
            )
        ultimo_registro_adicionado_vazao_lateral = vu_fontesC
        # Troca CQ 166 1 184 para CQ 166 1 146
        cq_fontesC = dadger.cq(
            codigo_restricao=166, estagio=1, codigo_usina=184
        )
        if cq_fontesC is not None:
            cq_fontesC.codigo_usina = 146

        ### Alterações de Fontes BC -> AB
        # AC 184 NUMPOS 300 -> AC 147 NUMPOS 300
        ac_numpos = dadger.ac(codigo_usina=184, modificacao=ACNUMPOS)
        if ac_numpos is not None:
            ac_numpos.codigo_usina = 147
        # Remove AC 182 DESVIO e AC 124 DESVIO
        # AC 184 VAZMIN 0 -> AC 147 VAZMIN 0
        ac_vazmin = dadger.ac(codigo_usina=184, modificacao=ACVAZMIN)
        if ac_vazmin is not None:
            ac_vazmin.codigo_usina = 147
            ac_vazmin.limite_vazao = 0.0
        # Insere VL 147 1
        vl_fontesAB = dadger.vl(codigo_usina_influenciada=147)
        if vl_fontesAB is None:
            vl_fontesAB = VL()
            vl_fontesAB.codigo_usina_influenciada = 147
            vl_fontesAB.fator_impacto_defluencia = 1
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, vl_fontesAB
            )
        ultimo_registro_adicionado_vazao_lateral = vl_fontesAB
        # Insere VU 147 146 1
        vu_fontesAB = dadger.vu(
            codigo_usina_influenciada=147, codigo_usina_influenciadora=146
        )
        if vu_fontesAB is None:
            vu_fontesAB = VU()
            vu_fontesAB.codigo_usina_influenciada = 147
            vu_fontesAB.codigo_usina_influenciadora = 146
            vu_fontesAB.fator_impacto_defluencia = 1
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, vu_fontesAB
            )
        ultimo_registro_adicionado_vazao_lateral = vu_fontesAB

    mapa_fontes = {
        183: 146,
        184: 147,
    }

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    dadger = Dadger.read(join(diretorio, arquivo))

    # Se o deck possui UH 146 e UH 147, então o deck já
    # possui a representação nova de fontes. Não faz nada
    if (
        dadger.uh(codigo_usina=146) is not None
        and dadger.uh(codigo_usina=147) is not None
    ):
        return

    # Se o deck possui UH 183 e UH 184, então o deck
    # possui representação antiga de fontes, e precisa ajustar
    ajusta_codigos_uh_fontes(dadger)
    ajusta_codigos_mp_fontes(dadger)
    ajusta_codigos_fd_fontes(dadger)
    ajusta_acs_vl_va_vu_fontes(dadger)

    # ----- Escreve novo dadger
    dadger.write(join(diretorio, arquivo))


def ajusta_representacao_belo_monte_pimental(diretorio: str):
    def cria_volmin(
        dadger: Dadger,
        usina,
        mes,
        semana,
        ano,
        volume,
        reg_anterior,
    ):
        ac_novo = ACVOLMIN()
        ac_novo.codigo_usina = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.volume = volume
        dadger.data.add_after(reg_anterior, ac_novo)
        return ac_novo

    def cria_volmax(
        dadger: Dadger,
        usina,
        mes,
        semana,
        ano,
        volume,
        reg_anterior,
    ):
        ac_novo = ACVOLMAX()
        ac_novo.codigo_usina = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.volume = volume
        dadger.data.add_after(reg_anterior, ac_novo)
        return ac_novo

    def cria_vsvert(
        dadger: Dadger,
        usina,
        mes,
        semana,
        ano,
        volume,
        reg_anterior,
    ):
        ac_novo = ACVSVERT()
        ac_novo.codigo_usina = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.volume = volume
        dadger.data.add_after(reg_anterior, ac_novo)
        return ac_novo

    def cria_vmdesv(
        dadger: Dadger,
        usina,
        mes,
        semana,
        ano,
        volume,
        reg_anterior,
    ):
        ac_novo = ACVMDESV()
        ac_novo.codigo_usina = usina
        ac_novo.mes = mes
        ac_novo.semana = semana
        ac_novo.ano = ano
        ac_novo.volume = volume
        dadger.data.add_after(reg_anterior, ac_novo)
        return ac_novo

    def ajusta_acs_volumes_belo_monte_pimental(dadger: Dadger):
        # ACS VOLMIN, VOLMAX, VSVERT e VMDESV para o valor sazonal
        ultimo_registro_adicionado_volume = dadger.ac(
            codigo_usina=314, modificacao=ACCOTVOL
        )
        df = pd.read_csv(Configuracoes().arquivo_volumes_sazonais, sep=";")
        usinas_volumes = [288, 314]
        for u in usinas_volumes:
            estagios = []
            for m in [1, 0]:
                for e in range(n_est - 1, 0, -1):
                    if not (
                        m == 1 and e > 1
                    ):  # se não é o 2º mês e estágio > 1
                        estagios.append(list([m, e]))

            for m, e in estagios:
                if m == 0:  # se 1º mês
                    periodo = e
                    reg_volmin = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACVOLMIN,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                    reg_volmax = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACJUSMED,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                    reg_vsvert = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACVSVERT,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                    reg_vmdesv = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACVMDESV,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                else:  # se 2º mês
                    periodo = 1
                    reg_volmin = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACVOLMIN,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                    reg_volmax = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACJUSMED,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                    reg_vsvert = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACVSVERT,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )
                    reg_vmdesv = dadger.ac(
                        codigo_usina=u,
                        modificacao=ACVMDESV,
                        mes=meses[inds[m]],
                        semana=periodo,
                    )

                volume = df.loc[
                    (df["usina"] == u) & (df["mes"] == meses[inds[m]]),
                    "volume",
                ].iloc[0]

                # confere se existe cada um dos registros e o valor
                if reg_volmin is not None:
                    volmin = reg_volmin.volume
                else:
                    volmin = None

                if volmin is None:
                    # se não existe AC VOLMIN, cria com valor estipulado
                    ultimo_registro_adicionado_volume = cria_volmin(
                        dadger,
                        u,
                        meses[inds[m]],
                        periodo,
                        anos[m],
                        volume,
                        ultimo_registro_adicionado_volume,
                    )

                if reg_volmax is not None:
                    volmax = reg_volmax.volume
                else:
                    volmax = None

                if volmax is None:
                    # se não existe AC VOLMAX, cria com valor estipulado
                    ultimo_registro_adicionado_volume = cria_volmax(
                        dadger,
                        u,
                        meses[inds[m]],
                        periodo,
                        anos[m],
                        volume,
                        ultimo_registro_adicionado_volume,
                    )

                if reg_vsvert is not None:
                    vsvert = reg_vsvert.volume
                else:
                    vsvert = None

                if vsvert is None:
                    # se não existe AC VSVERT, cria com valor estipulado
                    ultimo_registro_adicionado_volume = cria_vsvert(
                        dadger,
                        u,
                        meses[inds[m]],
                        periodo,
                        anos[m],
                        volume,
                        ultimo_registro_adicionado_volume,
                    )

                if reg_vmdesv is not None:
                    vmdesv = reg_vmdesv.volume
                else:
                    vmdesv = None

                if vmdesv is None:
                    # se não existe AC VMDESV, cria com valor estipulado
                    ultimo_registro_adicionado_volume = cria_vmdesv(
                        dadger,
                        u,
                        meses[inds[m]],
                        periodo,
                        anos[m],
                        volume,
                        ultimo_registro_adicionado_volume,
                    )

    def ajusta_vl_vu_va_belo_monte(dadger: Dadger):
        ultimo_registro_adicionado_vazao_lateral = dadger.vu()[-1]
        # Insere VL 288 1
        vl_bm = dadger.vl(codigo_usina_influenciada=288)
        if vl_bm is None:
            vl_bm = VL()
            vl_bm.codigo_usina_influenciada = 288
            vl_bm.fator_impacto_defluencia = 1
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, vl_bm
            )
        ultimo_registro_adicionado_vazao_lateral = vl_bm
        # Insere VU 288 314 1.00
        vu_bm = dadger.vu(
            codigo_usina_influenciada=288, codigo_usina_influenciadora=314
        )
        if vu_bm is None:
            vu_bm = VU()
            vu_bm.codigo_usina_influenciada = 288
            vu_bm.codigo_usina_influenciadora = 314
            vu_bm.fator_impacto_defluencia = 1
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, vu_bm
            )
        ultimo_registro_adicionado_vazao_lateral = vu_bm
        # Insere VA 288 288 0.07
        if va_bm is None:
            va_bm = VA()
            va_bm.codigo_usina_influenciada = 288
            va_bm.codigo_posto_influenciador = 288
            va_bm.fator_impacto_incremental = 0.07
            dadger.data.add_after(
                ultimo_registro_adicionado_vazao_lateral, va_bm
            )
        ultimo_registro_adicionado_vazao_lateral = va_bm

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    dadger = Dadger.read(join(diretorio, arquivo))

    # Se o deck possui VL, VU e VA para BM, então o deck já
    # possui a representação. Não faz nada
    if (
        dadger.vl(codigo_usina_influenciada=288) is not None
        and dadger.vu(
            codigo_usina_influenciada=288, codigo_usina_influenciadora=314
        )
        is not None
        and dadger.va(
            codigo_usina_influenciada=288,
            codigo_posto_influenciador=288,
        )
        is not None
    ):
        return

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

    # Se o deck possui UH 183 e UH 184, então o deck
    # possui representação antiga de fontes, e precisa ajustar
    ajusta_acs_volumes_belo_monte_pimental(dadger)
    ajusta_vl_vu_va_belo_monte(dadger)

    # ----- Escreve novo dadger
    dadger.write(join(diretorio, arquivo))


def ajusta_gtdp(diretorio: str):
    Log.log().info(f"Adequando GTDP...")

    ajusta_acs(diretorio)
    adequa_cfuga_cmont(diretorio)
    ajusta_representacao_fontes(diretorio)
    ajusta_representacao_belo_monte_pimental(diretorio)
    ajusta_fj(diretorio)
    copia_hidr(diretorio)
    copia_polinjus(diretorio)
    copia_indices(diretorio)
