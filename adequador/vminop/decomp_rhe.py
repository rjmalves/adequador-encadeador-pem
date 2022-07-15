from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import CT, HE, CM, CQ
import datetime
import pandas as pd
from adequador.utils.backup import converte_utf8
from utils.log import Log
from utils.nomes import dados_caso, nome_arquivo_dadger
from utils.configuracoes import Configuracoes


def ajusta_rhe(diretorio: str):

    Log.log().info(f"Ajustando VMINOP (RHE)...")

    df = pd.read_csv(Configuracoes().arquivo_vminop, sep=";")

    v = df.loc[df["mes"] == 999, "vminop"].tolist()
    v_aux = []
    for i in range(len(v)):
        v_aux = v_aux + [[v[i]] * 12]

    vminop = dict(zip(df.loc[df["mes"] == 999, "ree"], v_aux))

    r = int(df.loc[df["mes"] != 999, "ree"].unique())
    vminop[r] = df.loc[df["ree"] == r, "vminop"].tolist()

    REEs_RHE = list(vminop.keys())

    tipo_penalidade = [0, 1]  # primeiro e segundo mês (hard e soft)

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # ======================== IDENTIFICA DADOS DO PMO
    # Pega o número total de estágios do deck
    n_est = len(dadger.dp(subsistema=1))

    # Coleta informações de datas do deck
    dataini = datetime.date(
        day=dadger.dt.dia, month=dadger.dt.mes, year=dadger.dt.ano
    )  # data de inicio do 1º estágio

    datasdeck = [dataini]
    for e in range(1, n_est, 1):
        datasdeck = datasdeck + [
            dataini + datetime.timedelta(days=7 * e)
        ]  # datas iniciais de todos os estágios
    pmo = datasdeck[(n_est - 1) - 1].month  # mês do PMO

    # Identifica a revisão é a RV0:
    rv0 = 0
    if datasdeck[0].month != datasdeck[1].month:
        rv0 = "sim"

    # ======================== CALCULA PENALIDADE RHE CONFORME REGRA ESTABELECIDA
    cts = dadger.lista_registros(CT)
    cvu_usinas = [r.cvus for r in cts]
    cvu_max = max(max(cvu_usinas))

    # Regra de cálculo da penalidade:
    penalidade = 1.005 * cvu_max
    penalidade = penalidade + (10 - penalidade) % 10

    # ======================== OBTEM VALORES PARA A RHE DEPENDENDO DO MÊS DO DECK

    # -------- calcula índices dos meses necessários (1º e 2º mês)
    indice_rhe_m2 = pmo % 12  # mês 2
    indice_rhe_m1 = pmo - 1  # mês 1 - corrente
    indice_rhe_m0 = (pmo - 2) % 12  # mês 0

    vminop_rhe = dict()
    for r in REEs_RHE:
        if pmo in [11, 12, 1]:  # se for PMO de nov, dez ou jan

            # Valor para o primeiro estágio/semana:
            if rv0 == "sim":  # é primeira semana
                estagio_1 = min(
                    vminop[r][indice_rhe_m0], vminop[r][indice_rhe_m1]
                )
            else:
                estagio_1 = vminop[r][indice_rhe_m1]

            # Valor para a ultima semana:
            estagio_n = min(vminop[r][indice_rhe_m1], vminop[r][indice_rhe_m2])

            # Concatena valores para todos os estágios do deck (em ordem):
            vminop_rhe[r] = (
                [estagio_1]
                + (n_est - 3) * [vminop[r][indice_rhe_m1]]
                + [estagio_n]
                + [vminop[r][indice_rhe_m2]]
            )
        else:
            vminop_rhe[r] = n_est * [vminop[r][indice_rhe_m1]]

    # ======================== CRIA OU ALTERA REGISTROS HE/CM
    # Verifica se existe registro HE. Se não existir, cria. Se existir, altera

    def cria_HE(
        dadger: Dadger,
        codigo,
        tipo_limite,
        limite,
        estagio,
        penalidade,
        tipo_penalidade,
        posicao_registro,
    ):
        he_novo = HE()
        he_novo.codigo = codigo
        he_novo.tipo_limite = tipo_limite
        he_novo.limite = limite
        he_novo.estagio = estagio
        he_novo.penalidade = penalidade
        he_novo.tipo_penalidade = tipo_penalidade
        dadger.cria_registro(posicao_registro, he_novo)

    def cria_CM(dadger: Dadger, codigo, ree, coeficiente, posicao_registro):
        cm_novo = CM()
        cm_novo.codigo = codigo
        cm_novo.ree = ree
        cm_novo.coeficiente = coeficiente
        dadger.cria_registro(posicao_registro, cm_novo)

    # Confere registros CM e HE existentes
    cms = dadger.lista_registros(CM)
    cms_ree = [r.ree for r in cms]
    cms_cod = [r.codigo for r in cms]

    hes = dadger.lista_registros(HE)
    hes_codigos = [r.codigo for r in hes]
    hes_estagios = [r.estagio for r in hes]

    rhes_existentes = []
    for i in range(len(hes_codigos)):
        ind = cms_cod.index(hes_codigos[i])
        rhes_existentes = rhes_existentes + [[cms_ree[ind], hes_estagios[i]]]

    rhes_necessarios = []
    for i in range(len(REEs_RHE)):
        for e in range(n_est):
            rhes_necessarios = rhes_necessarios + [[REEs_RHE[i], e + 1]]

    # Verifica se as RHEs necessárias no deck já existem. Caso sim, confere e ajusta valores.
    # Caso não, cria os registros necessários.
    for (r, e) in list(reversed(rhes_necessarios)):

        ind_REE = REEs_RHE.index(r)
        estagio = e
        if estagio == n_est:
            tipo = tipo_penalidade[1]  # se o estágio é do 2º mês
        else:
            tipo = tipo_penalidade[0]  # se o estágio é do 1º mês

        if [r, e] in rhes_existentes:  # Já existe RHE para o REE e estágio

            ind_cod = rhes_existentes.index([r, e])
            codigo = hes_codigos[ind_cod]

            dadger.he(codigo=codigo, estagio=estagio).tipo_limite = 2
            dadger.he(codigo=codigo, estagio=estagio).limite = vminop_rhe[r][
                estagio - 1
            ]
            dadger.he(codigo=codigo, estagio=estagio).penalidade = penalidade
            dadger.he(codigo=codigo, estagio=estagio).tipo_penalidade = tipo
        else:
            # Não existe RHE para o REE e estágio
            # Cria novos registros

            if estagio == n_est:
                id = (ind_REE + 1) + 100
            else:
                id = ind_REE + 1

            if len(dadger.lista_registros(CM)) > 0:
                posicao = dadger.lista_registros(CQ)[-1]
            else:
                posicao = dadger.lista_registros(CQ)[-1]

            if dadger.cm(codigo=id) is None:
                cria_CM(dadger, id, r, 1, posicao)

            cria_HE(
                dadger,
                id,
                2,
                vminop_rhe[r][estagio - 1],
                estagio,
                penalidade,
                tipo,
                posicao,
            )

            dadger.escreve_arquivo(diretorio, arquivo)
