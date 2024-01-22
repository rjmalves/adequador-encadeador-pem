import pandas as pd
from idecomp.decomp import Dadger, Caso, Arquivos
from idecomp.decomp.modelos.dadger import DP, PQ
from inewave.newave import Sistema
from os.path import join
from pathlib import Path
from datetime import datetime, timedelta
from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes


class ConversorCargasPECDECOMP:
    """
    Classe responsável por realizar o ajuste do arquivo dadger.rvX e
    de um deck do DECOMP, considerando dados de MMGD.

    Os registros DP são alterados para conter tanto o mercado líquido quanto
    o mercado base de MMGD, somados, por patamar.

    São criados novos registros PQ para as "fontes MMGD", por estágio e por
    submercado.

    """

    SUBSISTEMAS = {"SE/CO": 1, "S": 2, "NE": 3, "N": 4}
    SUBSISTEMAS_PQ = {"SECO": 1, "SUL": 2, "NE": 3, "N": 4}
    COLUNAS_FONTES_MMGD = ["Hidro", "Termelétrica", "Eólica", "Fotovoltaica"]
    ORDEM_PATAMARES = ["Pesada", "Média", "Leve"]

    def __init__(
        self,
        caminho_deck: str,
        caminho_arquivo_dp: str,
        caminho_planilha_semanal: str,
        caminho_planilha_mensal: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__caminho_arquivo_dp = caminho_arquivo_dp
        self.__caminho_planilha_semanal = caminho_planilha_semanal
        self.__caminho_planilha_mensal = caminho_planilha_mensal
        self.__arquivo_caso = arquivo_caso
        self.__le_nomes_arquivos()
        self.__le_planilhas()

    def __le_nomes_arquivos(self):
        caso = Caso.read(join(self.__caminho_deck, self.__arquivo_caso))
        self.__nome_arquivos = caso.arquivos
        arquivos = Arquivos.read(
            join(self.__caminho_deck, self.__nome_arquivos)
        )
        self.__nome_dadger = arquivos.dadger

    def __le_planilhas(self):
        self.df_planilha_semanal = pd.read_excel(
            self.__caminho_planilha_semanal, parse_dates=True
        )
        self.df_planilha_mensal = pd.read_excel(
            self.__caminho_planilha_mensal, parse_dates=True
        )
        caminho = Path(self.__caminho_arquivo_dp)
        self._arquivo_dp = Dadger.read(join(caminho.parent, caminho.parts[-1]))

    def processa_dadger_DP(self):
        dadger = Dadger.read(join(self.__caminho_deck, self.__nome_dadger))
        # Transfere todos os registros DP do arquivo lido
        # para o dadger do caso
        dps_arquivo = self._arquivo_dp.dp()
        if isinstance(dps_arquivo, list):
            for dp in dps_arquivo:
                dp_dadger = dadger.dp(
                    estagio=dp.estagio, codigo_submercado=dp.codigo_submercado
                )
                if isinstance(dp_dadger, DP):
                    dp_dadger.carga = dp.carga
                    dp_dadger.duracao = dp.duracao
        else:
            raise RuntimeError(f"registro não é DP: {dps_arquivo}")
        dadger.write(join(self.__caminho_deck, self.__nome_dadger))

    def processa_dadger_PQ(self):
        df_semanal = self.df_planilha_semanal
        df_mensal = self.df_planilha_mensal
        # Obtém as datas de fim de cada estágio
        dadger = Dadger.read(join(self.__caminho_deck, self.__nome_dadger))
        dt = dadger.dt
        data_base = datetime(year=dt.ano, month=dt.mes, day=dt.dia)
        n_estagios_semanais = (
            max([r.estagio for r in dadger.dp(codigo_submercado=1)]) - 1
        )
        estagios_semanais = list(range(1, n_estagios_semanais + 1))
        datas_fim = [
            data_base + timedelta(days=7 * i - 1) for i in estagios_semanais
        ]

        # Exclui os registros PQ pré existentes com carga MMGD, contidos em decks a
        # partir de jan/2023, para não contabilizar PQ/MMGD de forma duplicada. Os
        # registros já existentes são identificados pelo mnemônico "gd" no final da string
        for registro in dadger.pq():
            if "gd" in registro.nome or "MMGD" in registro.nome:
                dadger.data.remove(registro)

        # Constroi os registros PQ de MMGD, por mercado
        # e por estágio
        ultimo_pq = dadger.pq()[-1]
        for nome, indice in self.SUBSISTEMAS.items():
            mnemonico = next(
                k for k, v in self.SUBSISTEMAS_PQ.items() if v == indice
            )
            nome_pq = f"{mnemonico}_MMGD"
            # Adiciona estágios semanais
            for estagio, data in zip(estagios_semanais, datas_fim):
                geracao_patamares = []
                for patamar in self.ORDEM_PATAMARES:
                    filtro = (
                        (df_semanal["SO"] == data)
                        & (df_semanal["subsistema"] == nome)
                        & (df_semanal["Patamar"] == patamar)
                    )
                    geracao_patamares.append(
                        df_semanal.loc[filtro, self.COLUNAS_FONTES_MMGD]
                        .sum()
                        .sum()
                    )
                novo_pq = PQ()
                novo_pq.nome = nome_pq
                novo_pq.codigo_submercado = indice
                novo_pq.estagio = estagio
                novo_pq.geracao = geracao_patamares
                dadger.data.add_after(ultimo_pq, novo_pq)
                ultimo_pq = novo_pq
            # Adiciona estágio mensal
            geracao_patamares = []
            for patamar in self.ORDEM_PATAMARES:
                filtro = (df_mensal["subsistema"] == nome) & (
                    df_mensal["Patamar"] == patamar
                )
                geracao_patamares.append(
                    df_mensal.loc[filtro, self.COLUNAS_FONTES_MMGD].sum().sum()
                )
            novo_pq = PQ()
            novo_pq.nome = nome_pq
            novo_pq.codigo_submercado = indice
            novo_pq.estagio = estagio + 1
            novo_pq.geracao = geracao_patamares
            dadger.data.add_after(ultimo_pq, novo_pq)
            ultimo_pq = novo_pq

        dadger.write(join(self.__caminho_deck, self.__nome_dadger))


class DecompositorPequsiDECOMP:
    def __init__(self, caso_referencia: str, caso: str) -> None:
        self.__caso_referencia = caso_referencia
        self.__caso = caso
        self.__ano, self.__mes, self.__revisao = (
            Path(caso).parts[-2].split("_")
        )
        self.__data_base = datetime(int(self.__ano), int(self.__mes), 1)
        self.__rv = self.__revisao.split("rv")[1]

    def __quebra_registros_pq(self):
        sistema = Sistema.read(join(self.__caso_referencia, "sistema.dat"))
        dadger = Dadger.read(join(self.__caso, f"dadger.rv{self.__rv}"))
        estagios_decomp = len(dadger.dp(codigo_submercado=1))
        pqs_existentes = dadger.pq()
        # Adiciona os PQ copiando os valores por fonte
        # do sistema.dat do NEWAVE daquele mês
        df = sistema.geracao_usinas_nao_simuladas
        submercados = {1: "SECO", 2: "SUL", 3: "NE", 4: "N"}
        ultimo_registro = pqs_existentes[-1]
        for indice, submercado in submercados.items():
            for fonte in ["PCH", "PCT", "EOL", "UFV"]:
                pequsi_fonte = df.loc[
                    (df["codigo_submercado"] == indice)
                    & (df["fonte"] == fonte)
                    & (df["data"] >= self.__data_base),
                    "valor",
                ].dropna()
                geracao_1mes = float(pequsi_fonte.iloc[0])
                geracao_2mes = float(pequsi_fonte.iloc[1])
                pq_1mes = PQ()
                pq_1mes.estagio = 1
                pq_1mes.nome = f"{submercado}_{fonte}"
                pq_1mes.codigo_submercado = indice
                pq_1mes.geracao = [geracao_1mes, geracao_1mes, geracao_1mes]
                pq_2mes = PQ()
                pq_2mes.estagio = estagios_decomp
                pq_2mes.nome = f"{submercado}_{fonte}"
                pq_2mes.codigo_submercado = indice
                pq_2mes.geracao = [geracao_2mes, geracao_2mes, geracao_2mes]
                dadger.data.add_after(ultimo_registro, pq_1mes)
                dadger.data.add_after(pq_1mes, pq_2mes)
        # Deleta todos os registros PQ existentes anteriormente
        for r in pqs_existentes:
            dadger.data.remove(r)
        dadger.write(join(self.__caso, f"dadger.rv{self.__rv}"))

    def quebra_pequsi(self):
        self.__quebra_registros_pq()


def adequa_acl_mmgd_decomp(diretorio: str):
    Log.log().info(f"Adequando ACL e MMGD...")

    # Verifica se o DECOMP precisa ser adequado
    caso = Path(diretorio).parts[-2]
    ano, mes, revisao = caso.split("_")
    rv = revisao.split("rv")[1].zfill(2)

    # Se o caso for de antes de 2022, quebra o bloco
    # de pequenas usinas por fonte
    data_caso = datetime(year=int(ano), month=int(mes), day=1)
    data_referencia = datetime(2022, 1, 1)
    if data_caso < data_referencia:
        decompositor = DecompositorPequsiDECOMP(
            f"{ano}_{mes}_rv0/newave", diretorio
        )
        decompositor.quebra_pequsi()

    arquivo_dp = join(
        Configuracoes().diretorio_dados_mmgd_decomp,
        f"DP_REV{rv}PMO{ano}{mes}.txt",
    )
    arquivo_semanal = join(
        Configuracoes().diretorio_dados_mmgd_decomp,
        f"Semanal_DP_PREV_REV{rv}PMO{ano}{mes}.xlsx",
    )
    arquivo_mensal = join(
        Configuracoes().diretorio_dados_mmgd_decomp,
        f"Mensal_DP_PREV{rv}PMO{ano}{mes}.xlsx",
    )
    conversor_mmgd = ConversorCargasPECDECOMP(
        caminho_deck=diretorio,
        caminho_arquivo_dp=arquivo_dp,
        caminho_planilha_semanal=arquivo_semanal,
        caminho_planilha_mensal=arquivo_mensal,
    )
    conversor_mmgd.processa_dadger_DP()
    conversor_mmgd.processa_dadger_PQ()
