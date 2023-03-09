from inewave.newave.arquivos import Arquivos
from inewave.newave.caso import Caso
from inewave.newave.dger import DGer
from inewave.newave.cvar import CVAR
from adequador.utils.backup import converte_utf8
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import (
    nome_arquivo_abertura,
    nome_arquivo_arquivos,
    nome_arquivo_clasgas,
    nome_arquivo_cvar,
    nome_arquivo_dger,
    nome_arquivo_adterm,
    nome_arquivo_gee,
    nome_arquivo_ghmin,
    nome_arquivo_ree,
    nome_arquivo_sar,
    nome_arquivo_re,
    nome_arquivo_tecno,
    nome_arquivo_simfinal,
    nome_arquivo_cortes_pos,
    nome_arquivo_cortesh_pos,
)

from os.path import join
from adequador.utils.log import Log
import pandas as pd


def garante_campos_arquivos(arquivos: Arquivos):
    arquivos.adterm = nome_arquivo_adterm()
    arquivos.ghmin = nome_arquivo_ghmin()
    arquivos.sar = nome_arquivo_sar()
    arquivos.cvar = nome_arquivo_cvar()
    arquivos.ree = nome_arquivo_ree()
    arquivos.re = nome_arquivo_re()
    arquivos.tecno = nome_arquivo_tecno()
    arquivos.abertura = nome_arquivo_abertura()
    arquivos.gee = nome_arquivo_gee()
    arquivos.clasgas = nome_arquivo_clasgas()
    arquivos.dados_simulacao_final = nome_arquivo_simfinal()
    arquivos.cortes_pos_estudo = nome_arquivo_cortes_pos()
    arquivos.cortesh_pos_estudo = nome_arquivo_cortesh_pos()


def garante_campos_dger(dger: DGer):
    dger.despacho_antecipado_gnl = 1
    dger.modif_automatica_adterm = 1
    dger.considera_ghmin = 1
    dger.simulacao_final_com_data = 0
    dger.utiliza_gerenciamento_pls = 0
    dger.comunicacao_dois_niveis = 0
    dger.armazenamento_local_arquivos_temporarios = 0
    dger.alocacao_memoria_ena = 0
    dger.alocacao_memoria_cortes = 0
    dger.sar = 0
    dger.cvar = 1
    dger.considera_zsup_min_convergencia = 0
    dger.desconsidera_vazao_minima = 0
    dger.restricoes_eletricas = 1
    dger.selecao_de_cortes_backward = 1
    dger.selecao_de_cortes_forward = 1
    dger.janela_de_cortes = 0
    dger.considera_reamostragem_cenarios = 1
    dger.tipo_reamostragem_cenarios = 1
    dger.passo_reamostragem_cenarios = 1
    dger.converge_no_zero = 0
    dger.consulta_fcf = 0
    dger.impressao_ena = 0
    dger.impressao_cortes_ativos_sim_final = 0
    dger.representacao_agregacao = 1
    dger.matriz_correlacao_espacial = 1
    dger.desconsidera_convergencia_estatistica = 1
    dger.momento_reamostragem = 1
    dger.mantem_arquivos_energias = 0
    dger.inicio_teste_convergencia = 1
    dger.sazonaliza_vmint = 0
    dger.sazonaliza_vmaxt = 0
    dger.sazonaliza_vminp = 0
    dger.sazonaliza_cfuga_cmont = 0
    dger.restricoes_emissao_gee = 0
    dger.consideracao_media_anual_afluencias = 3
    dger.reducao_automatica_ordem = 0
    dger.restricoes_fornecimento_gas = 0
    dger.memoria_calculo_cortes = 0
    dger.considera_geracao_eolica = 0
    dger.penalidade_corte_geracao_eolica = 0.0063
    dger.compensacao_correlacao_cruzada = 0
    dger.restricao_turbinamento = 0
    dger.restricao_defluencia = 0
    dger.aproveitamento_bases_backward = 1
    dger.impressao_estados_geracao_cortes = 1
    dger.semente_forward = 0
    dger.semente_backward = 0
    dger.restricao_lpp_turbinamento_maximo_ree = 0
    dger.restricao_lpp_turbinamento_maximo_uhe = 0
    dger.restricao_lpp_defluencia_maxima_ree = 0
    dger.restricao_lpp_defluencia_maxima_uhe = 0
    dger.restricoes_eletricas_especiais = 0
    dger.funcao_producao_uhe = 0
    dger.fcf_pos_estudo = 0


def garante_legendas_dger(caminho: str):

    LEGENDAS = [
        "TIPO DE EXECUCAO     ",
        "DURACAO DO PERIODO   ",
        "No. DE ANOS DO EST   ",
        "MES INICIO PRE-EST   ",
        "MES INICIO DO ESTUDO ",
        "ANO INICIO DO ESTUDO ",
        "No. DE ANOS PRE      ",
        "No. DE ANOS POS      ",
        "No. DE ANOS POS FINAL",
        "IMPRIME DADOS        ",
        "IMPRIME MERCADOS     ",
        "IMPRIME ENERGIAS     ",
        "IMPRIME M. ESTOCAS   ",
        "IMPRIME SUBSISTEMA   ",
        "No MAX. DE ITER.     ",
        "No DE SIM. FORWARD   ",
        "No DE ABERTURAS      ",
        "No DE SERIES SINT.   ",
        "ORDEM MAX. PAR(P)    ",
        "ANO INICIAL HIST.    ",
        "CALCULA VOL.INICIAL  ",
        "VOLUME INICIAL  -%   ",
        "POR SUBSISTEMA      ",
        "TOLERANCIA      -%   ",
        "TAXA DE DESCONTO-%   ",
        "TIPO SIMUL. FINAL    ",
        "IMPRESSAO DA OPER    ",
        "IMPRESSAO DA CONVERG.",
        "INTERVALO P/ GRAVAR  ",
        "No. MIN. ITER.       ",
        "RACIONAMENTO PREVENT.",
        "No. ANOS MANUT.UTE'S ",
        "TENDENCIA HIDROLOGICA",
        "RESTRICA0 DE ITAIPU  ",
        "BID                  ",
        "PERDAS P/ TRANSMISSAO",
        "EL NINO              ",
        "ENSO INDEX           ",
        "DURACAO POR PATAMAR  ",
        "OUTROS USOS DA AGUA  ",
        "CORRECAO DESVIO      ",
        "C.AVERSAO/PENAL.VMINP",
        "TIPO DE GERACAO ENAS ",
        "RISCO DE DEFICIT     ",
        "ITERACAO P/SIM.FINAL ",
        "AGRUPAMENTO LIVRE    ",
        "EQUALIZACAO PEN.INT. ",
        "REPRESENT.SUBMOT.    ",
        "ORDENACAO AUTOMATICA ",
        "CONS. CARGA ADICIONAL",
        "DELTA ZSUP           ",
        "DELTA ZINF           ",
        "DELTAS CONSECUT.     ",
        "DESP. ANTEC.  GNL    ",
        "MODIF.AUTOM.ADTERM   ",
        "CONSIDERA GHMIN      ",
        "S.F. COM DATA        ",
        "GER.PLs E NV1 E NV2  ",
        "SAR                  ",
        "CVAR                 ",
        "CONS. ZSUP MIN. CONV.",
        "DESCONSIDERA VAZMIN  ",
        "RESTRICOES ELETRICAS ",
        "SELECAO DE CORTES    ",
        "JANELA DE CORTES     ",
        "REAMOST. CENARIOS    ",
        "CONVERGE NO ZERO     ",
        "CONSULTA FCF         ",
        "IMPRESSAO AFL/VENTO  ",
        "IMP. CATIVO S.FINAL  ",
        "REP. AGREGACAO       ",
        "MATRIZ CORR.ESPACIAL ",
        "DESCONS. CONV. ESTAT ",
        "MOMENTO REAMOSTRAGEM ",
        "ARQUIVOS ENA         ",
        "INICIO TESTE CONVERG.",
        "SAZ. VMINT PER. EST. ",
        "SAZ. VMAXT PER. EST. ",
        "SAZ. VMINP PER. EST. ",
        "SAZ. CFUGA E CMONT   ",
        "REST. EMISSAO GEE    ",
        "AFLUENCIA ANUAL PARP ",
        "REST. FORNEC. GAS    ",
        "MEM. CALCULO CORTES  ",
        "GERACAO EOLICA       ",
        "COMP. COR. CRUZ.     ",
        "REST. TURBINAMENTO   ",
        "REST. DEFL. MAXIMA   ",
        "BASE PLS BACKWARD    ",
        "ESTADOS GER. CORTES  ",
        "SEMENTE FORWARD      ",
        "SEMENTE BACWARD      ",
        "REST.LPP TURB.MAX REE",
        "REST.LPP DEFL.MAX REE",
        "REST.LPP TURB.MAX UHE",
        "REST.LPP DEFL.MAX UHE",
        "REST.ELETRI ESPECIAIS",
        "FUNCAO DE PROD. UHE  ",
        "FCF POS ESTUDO       ",
    ]
    COL_LEGENDA = 21

    with open(caminho, "r") as arq_entrada:
        linhas = arq_entrada.readlines()
    with open(caminho, "w") as arq_saida:
        arq_saida.write(linhas[0])
        for legenda, linha in zip(LEGENDAS, linhas[1:]):
            arq_saida.write(legenda + linha[COL_LEGENDA:])


def ajusta_dados_gerais_cvar(diretorio: str):

    Log.log().info(f"Adequando DADOSGERAIS...")

    df = pd.read_csv(
        Configuracoes().arquivo_dados_gerais_newave, sep=";", index_col=0
    )

    # Arquivo de arquivos
    arquivo = nome_arquivo_arquivos()
    converte_utf8(diretorio, arquivo)
    arq = Arquivos.le_arquivo(diretorio, arquivo)
    # Garante que tem todos os blocos necessários
    garante_campos_arquivos(arq)
    arq.escreve_arquivo(diretorio, arquivo)

    # Arquivo de dados gerais
    arquivo = nome_arquivo_dger()
    converte_utf8(diretorio, arquivo)
    dger = DGer.le_arquivo(diretorio, arquivo)

    # Garante que tem todos os blocos necessários
    garante_campos_dger(dger)

    # Modifica, caso desejado, geração de cenários e critério de parada
    dger.consideracao_media_anual_afluencias = int(df.at["parp", "valor"])
    dger.num_minimo_iteracoes = int(df.at["miniter", "valor"])
    dger.num_max_iteracoes = int(df.at["maxiter", "valor"])
    dger.delta_zinf = float(df.at["deltazinf", "valor"])
    dger.deltas_consecutivos = int(df.at["deltaconsecutivo", "valor"])
    dger.restricao_defluencia = int(df.at["defluenciauhe", "valor"])
    dger.restricao_turbinamento = int(df.at["turbinamentouhe", "valor"])
    dger.restricao_lpp_defluencia_maxima_uhe = int(
        df.at["lppdefluenciauhe", "valor"]
    )
    dger.restricao_lpp_turbinamento_maximo_uhe = int(
        df.at["lppturbinamentouhe", "valor"]
    )
    dger.restricao_lpp_defluencia_maxima_ree = int(
        df.at["lppdefluenciaree", "valor"]
    )
    dger.restricao_lpp_turbinamento_maximo_ree = int(
        df.at["lppturbinamentoree", "valor"]
    )
    dger.restricoes_eletricas_especiais = int(
        df["restricoeseletricasespeciais"]
    )
    dger.funcao_producao_uhe = int(df.at["funcaoproducao", "valor"])
    dger.fcf_pos_estudo = int(df.at["fcfpos", "valor"])
    dger.cvar = int(df.at["cvar", "valor"])

    usa_gerenciador = int(df.at["usa_gerenciador_processos", "valor"])
    if usa_gerenciador:
        Log.log().info(f"Adequando gerenciador de PLs...")
        dger.utiliza_gerenciamento_pls = 1
        dger.comunicacao_dois_niveis = 1
        dger.armazenamento_local_arquivos_temporarios = 1
        caso = Caso.le_arquivo(diretorio, "caso.dat")
        caso.gerenciador_processos = df.at[
            "caminho_gerenciador_processos", "valor"
        ]
        caso.escreve_arquivo(diretorio, "caso.dat")

    imprime_arquivos = int(df.at["imprime_arquivos", "valor"])
    if imprime_arquivos:
        dger.mantem_arquivos_energias = 1
        dger.impressao_estados_geracao_cortes = 0

    dger.escreve_arquivo(diretorio, arquivo)

    # TODO - temporario (garante legendas)
    garante_legendas_dger(join(diretorio, arquivo))

    Log.log().info(f"Adequando CVAR...")

    df = pd.read_csv(Configuracoes().arquivo_dados_gerais_newave, sep=";")

    # Arquivo de CVAR
    arquivo = nome_arquivo_cvar()
    converte_utf8(diretorio, arquivo)
    arq_cvar = CVAR.le_arquivo(diretorio, arquivo)
    arq_cvar.valores_constantes = [
        int(df.at["alpha", "valor"]),
        int(df.at["lambda", "valor"]),
    ]
    arq_cvar.escreve_arquivo(diretorio, arquivo)
