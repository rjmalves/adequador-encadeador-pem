from inewave.newave.arquivos import Arquivos
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
)

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
    dger.selecao_de_cortes = 1
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


def ajusta_dados_gerais_cvar(diretorio: str):

    Log.log().info(f"Adequando DADOSGERAIS...")

    df = pd.read_csv(Configuracoes().arquivo_dados_gerais_newave, sep=";")

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
    dger.consideracao_media_anual_afluencias = int(df["vazao"])
    dger.reducao_automatica_ordem = 0
    dger.num_minimo_iteracoes = int(df["miniter"])
    dger.num_max_iteracoes = int(df["maxiter"])
    dger.delta_zinf = float(df["deltazinf"])
    dger.deltas_consecutivos = int(df["deltaconsecutivo"])
    dger.cvar = 1

    dger.escreve_arquivo(diretorio, arquivo)

    Log.log().info(f"Adequando CVAR...")

    df = pd.read_csv(Configuracoes().arquivo_dados_gerais_newave, sep=";")

    # Arquivo de CVAR
    arquivo = nome_arquivo_cvar()
    converte_utf8(diretorio, arquivo)
    arq_cvar = CVAR.le_arquivo(diretorio, arquivo)
    arq_cvar.valores_constantes = [int(df["alpha"]), int(df["lambda"])]
    arq_cvar.escreve_arquivo(diretorio, arquivo)
