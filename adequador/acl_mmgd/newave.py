import pandas as pd
import numpy as np
from pathlib import Path
from os.path import join
from inewave.newave import Arquivos, Caso, Dger, Sistema, Patamar, Cadic
from datetime import datetime
from dateutil.relativedelta import relativedelta
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log


class MontadorBaseACLNEWAVE:
    """
    Classe responsável por extrair dados de dois decks de NEWAVE,
    um composto com os blocos de pequenas usinas atualizados com
    ACL e outro com o bloco segundo o processo anterior.

    PREMISSA: Assume que os decks são relativos ao mesmo PMO.
    """

    def __init__(
        self,
        caminho_deck_atual: str,
        caminho_deck_acl: str,
        arquivo_caso: str = "caso.dat",
        arquivo_base: str = "base_acl.csv",
    ) -> None:
        self.__caminho_deck_atual = caminho_deck_atual
        self.__caminho_deck_acl = caminho_deck_acl
        self.__arquivo_caso = arquivo_caso
        self.__le_nomes_arquivos()
        self.__arquivo_base = arquivo_base

    def __le_nomes_arquivos(self):
        caso_atual = Caso.read(
            join(self.__caminho_deck_atual, self.__arquivo_caso)
        )
        self.__nome_arquivos_atual = caso_atual.arquivos
        arquivos_atual = Arquivos.read(
            join(self.__caminho_deck_atual, self.__nome_arquivos_atual)
        )
        caso_acl = Caso.read(
            join(self.__caminho_deck_acl, self.__arquivo_caso)
        )
        self.__nome_arquivos_acl = caso_acl.arquivos
        self.__nome_sistema_atual = arquivos_atual.sistema
        self.__nome_patamar_atual = arquivos_atual.patamar
        arquivos_acl = Arquivos.read(
            join(self.__caminho_deck_acl, self.__nome_arquivos_acl)
        )
        self.__nome_sistema_acl = arquivos_acl.sistema
        self.__nome_patamar_acl = arquivos_acl.patamar
        dger_atual = Dger.read(
            join(self.__caminho_deck_atual, arquivos_atual.dger)
        )
        self.__numero_anos_estudo = dger_atual.num_anos_estudo
        self.__ano_inicio_estudo = dger_atual.ano_inicio_estudo

    def __le_arquivos_decks(self):
        self.__sistema_atual = Sistema.read(
            join(self.__caminho_deck_atual, self.__nome_sistema_atual)
        )
        self.__sistema_acl = Sistema.read(
            join(self.__caminho_deck_acl, self.__nome_sistema_acl)
        )
        self.__patamar_atual = Patamar.read(
            join(self.__caminho_deck_atual, self.__nome_patamar_atual)
        )
        self.__patamar_acl = Patamar.read(
            join(self.__caminho_deck_acl, self.__nome_patamar_acl)
        )

    def __monta_vetor_datas(self) -> pd.DatetimeIndex:
        ano_inicio = self.__ano_inicio_estudo
        ano_final = ano_inicio + self.__numero_anos_estudo - 1
        inicio = datetime(year=ano_inicio, month=1, day=1)
        fim = datetime(year=ano_final, month=12, day=1)
        return pd.date_range(inicio, fim, freq="MS")

    def __monta_base(
        self,
        pequsi_atual: pd.DataFrame,
        pequsi_acl: pd.DataFrame,
        patamar_atual: pd.DataFrame,
        patamar_acl: pd.DataFrame,
    ):
        # O df deve ter as colunas:
        # submercado | patamar | bloco | data | delta_acl
        submercados = pequsi_atual["codigo_submercado"].unique().tolist()
        patamares = patamar_atual["patamar"].unique().tolist()
        blocos = patamar_atual["indice_bloco"].unique().tolist()
        datas = self.__monta_vetor_datas()
        df_acl = pd.DataFrame()
        for s in submercados:
            for p in patamares:
                for b in blocos:
                    geracao_oficial = (
                        pequsi_atual.loc[
                            (pequsi_atual["codigo_submercado"] == s)
                            & (pequsi_atual["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    prof_oficial = (
                        patamar_atual.loc[
                            (patamar_atual["codigo_submercado"] == s)
                            & (patamar_atual["patamar"] == p)
                            & (patamar_atual["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    geracao_acl = (
                        pequsi_acl.loc[
                            (pequsi_acl["codigo_submercado"] == s)
                            & (pequsi_acl["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    prof_acl = (
                        patamar_acl.loc[
                            (patamar_acl["codigo_submercado"] == s)
                            & (patamar_acl["patamar"] == p)
                            & (patamar_acl["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    df_t = pd.DataFrame(
                        data={
                            "data": datas,
                            "delta_acl": geracao_acl * prof_acl
                            - geracao_oficial * prof_oficial,
                        }
                    )
                    df_t["indice_bloco"] = b
                    df_t["patamar"] = p
                    df_t["codigo_submercado"] = s
                    df_acl = pd.concat([df_acl, df_t], ignore_index=True)
        return df_acl[
            [
                "codigo_submercado",
                "patamar",
                "indice_bloco",
                "data",
                "delta_acl",
            ]
        ]

    def processa_base_acl(self):
        self.__le_arquivos_decks()

        pequsi_atual = self.__sistema_atual.geracao_usinas_nao_simuladas
        pequsi_acl = self.__sistema_acl.geracao_usinas_nao_simuladas
        patamar_atual = self.__patamar_atual.usinas_nao_simuladas
        patamar_acl = self.__patamar_acl.usinas_nao_simuladas
        df_base = self.__monta_base(
            pequsi_atual, pequsi_acl, patamar_atual, patamar_acl
        )
        # PREMISSA: Fixa em 0.0 os meses faltantes do deck
        df_base.loc[pd.isna(df_base["delta_acl"]), "delta_acl"] = 0.0
        df_base.to_csv(self.__arquivo_base, index=False)


class ConversorACLNEWAVE:
    """
    Classe responsável por realizar o ajuste dos arquivos sistema.dat
     e patamar.dat de um deck do NEWAVE, considerando dados de ACL.

    No arquivo sistema.dat é alterado o bloco da geração esperada de pequenas
    usinas.

    No arquivo patamar.dat é alterada a profundidade dos patamares de cada bloco
    no sistema.dat que possua alteração devido ao ACL.
    """

    SUBSISTEMAS = {"SUDESTE": 1, "SUL": 2, "NORDESTE": 3, "NORTE": 4}
    NOMES_USINAS_NAO_SIMULADAS = {
        1: "PCH",
        2: "PCT",
        3: "EOL",
        4: "UFV",
    }

    def __init__(
        self,
        caminho_deck: str,
        caminho_base: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__caminho_base = caminho_base
        self.__arquivo_caso = arquivo_caso
        self.__le_nomes_arquivos()
        self.__le_base()

    def __le_nomes_arquivos(self):
        caso = Caso.read(join(self.__caminho_deck, self.__arquivo_caso))
        self.__nome_arquivos = caso.arquivos
        arquivos = Arquivos.read(
            join(self.__caminho_deck, self.__nome_arquivos)
        )
        dger = Dger.read(join(self.__caminho_deck, arquivos.dger))
        self.__nome_sistema = arquivos.sistema
        self.__nome_patamar = arquivos.patamar
        self.__ano_inicio_estudo = dger.ano_inicio_estudo
        self.__numero_anos_estudo = dger.num_anos_estudo

    def __le_base(self):
        self.__df_base = pd.read_csv(self.__caminho_base, parse_dates=True)
        self.__df_base["data"] = pd.to_datetime(self.__df_base["data"])

    def __quebra_pequsi_em_patamares(
        self, sistema: Sistema, patamar: Patamar
    ) -> pd.DataFrame:
        pat_pequsi = patamar.usinas_nao_simuladas
        pequsi = sistema.geracao_usinas_nao_simuladas

        pequsi_por_pat = pat_pequsi.copy()
        submercados = pat_pequsi["codigo_submercado"].unique().tolist()
        patamares = pat_pequsi["patamar"].unique().tolist()
        blocos = self.__df_base["bloco"].unique().tolist()
        for s in submercados:
            for p in patamares:
                for b in blocos:
                    profs = (
                        pat_pequsi.loc[
                            (pat_pequsi["codigo_submerado"] == s)
                            & (pat_pequsi["patamar"] == p)
                            & (pat_pequsi["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    geracoes = (
                        pequsi.loc[
                            (pequsi["codigo_submercado"] == s)
                            & (pequsi["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    pequsi_por_pat.loc[
                        (pequsi_por_pat["codigo_submercado"] == s)
                        & (pequsi_por_pat["patamar"] == p)
                        & (pequsi_por_pat["indice_bloco"] == b),
                        "valor",
                    ] = (
                        profs * geracoes
                    )
        return pequsi_por_pat

    def __soma_valores_acl(self, pequsi_por_pat: pd.DataFrame) -> pd.DataFrame:
        submercados = pequsi_por_pat["codigo_submercado"].unique().tolist()
        patamares = pequsi_por_pat["patamar"].unique().tolist()
        blocos = self.__df_base["indice_bloco"].unique().tolist()
        for s in submercados:
            for p in patamares:
                for b in blocos:
                    valores_base_acl = (
                        self.__df_base.loc[
                            (self.__df_base["codigo_submercado"] == s)
                            & (self.__df_base["patamar"] == p)
                            & (self.__df_base["indice_bloco"] == b),
                            "delta_acl",
                        ]
                        .to_numpy()
                        .flatten()
                    )
                    if len(valores_base_acl) == 0:
                        print(f"Não existem valores na base de ACL")
                        continue
                    pequsi_por_pat.loc[
                        (pequsi_por_pat["codigo_submercado"] == s)
                        & (pequsi_por_pat["patamar"] == p)
                        & (pequsi_por_pat["indice_bloco"] == b),
                        "valor",
                    ] += valores_base_acl

        return pequsi_por_pat

    def __calcula_patamar_medio(
        self, sistema: Sistema, patamar: Patamar, pequsi_por_pat: pd.DataFrame
    ) -> pd.DataFrame:
        duracoes = patamar.duracao_mensal_patamares
        patamares = pequsi_por_pat["patamar"].unique().tolist()
        submercados = pequsi_por_pat["codigo_submercado"].unique().tolist()
        blocos = self.__df_base["indice_bloco"].unique().tolist()
        pequsi_medio = sistema.geracao_usinas_nao_simuladas.copy()
        for s in submercados:
            for b in blocos:
                media_patamares = np.zeros((12,))
                for p in patamares:
                    geracao = (
                        pequsi_por_pat.loc[
                            (pequsi_por_pat["codigo_submercado"] == s)
                            & (pequsi_por_pat["patamar"] == p)
                            & (pequsi_por_pat["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    duracao = (
                        duracoes.loc[
                            (duracoes["patamar"] == p),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    media_patamares += np.multiply(geracao, duracao)
                pequsi_medio.loc[
                    (pequsi_medio["codigo_submercado"] == s)
                    & (pequsi_medio["indice_bloco"] == b),
                    "valor",
                ] = media_patamares

        return pequsi_medio

    def __calcula_profundidades(
        self,
        patamar: Patamar,
        pequsi_por_pat: pd.DataFrame,
        pequsi_medio: pd.DataFrame,
    ) -> pd.DataFrame:
        patamares = pequsi_por_pat["patamar"].unique().tolist()
        submercados = pequsi_por_pat["codigo_submercado"].unique().tolist()
        blocos = self.__df_base["indice_bloco"].unique().tolist()
        profs_pequsi = patamar.usinas_nao_simuladas.copy()
        for s in submercados:
            for b in blocos:
                for p in patamares:
                    geracao_pat = (
                        pequsi_por_pat.loc[
                            (pequsi_por_pat["codigo_submercado"] == s)
                            & (pequsi_por_pat["patamar"] == p)
                            & (pequsi_por_pat["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    geracao_media = (
                        pequsi_medio.loc[
                            (pequsi_medio["codigo_submercado"] == s)
                            & (pequsi_medio["indice_bloco"] == b),
                            "valor",
                        ]
                        .to_numpy()
                        .flatten()
                        .flatten()
                    )
                    profs_pequsi.loc[
                        (profs_pequsi["codigo_submercado"] == s)
                        & (profs_pequsi["patamar"] == p)
                        & (profs_pequsi["indice_bloco"] == b),
                        "valor",
                    ] = np.divide(geracao_pat, geracao_media)

        return profs_pequsi.fillna(1.0)

    def processa_acl(self):
        # O processo todo é:
        # 1 - ler os dados do deck e gerar um DF que quebre cada PEQUSI por
        # patamar, em valor absoluto
        # 2 - Somar os valores da base, nas respectivas datas
        # 3 - Recalcular um patamar médio, por pequsi
        # 4 - Calculas as novas profundidades de patamar
        # 5 - Escreve os blocos atualizados no sistema.dat e patamar.dat
        sistema = Sistema.read(join(self.__caminho_deck, self.__nome_sistema))
        patamar = Patamar.read(join(self.__caminho_deck, self.__nome_patamar))
        pequsi_por_patamar = self.__quebra_pequsi_em_patamares(
            sistema, patamar
        )
        pequsi_somado = self.__soma_valores_acl(pequsi_por_patamar)
        pequsi_medio = self.__calcula_patamar_medio(
            sistema, patamar, pequsi_somado
        )
        profs_pequsi = self.__calcula_profundidades(
            patamar, pequsi_somado, pequsi_medio
        )
        sistema.geracao_usinas_nao_simuladas = pequsi_medio
        patamar.usinas_nao_simuladas = profs_pequsi
        sistema.write(join(self.__caminho_deck, self.__nome_sistema))
        patamar.write(join(self.__caminho_deck, self.__nome_patamar))


class ConversorACLVerificadoNEWAVE:
    """
    Classe responsável por realizar o ajuste dos arquivos sistema.dat
     e patamar.dat de um deck do NEWAVE, considerando dados de ACL.

    Nos arquivos sistema.dat e patamar.dat os dados são sobrescritos com
    valores verificados no horizonte.
    """

    SUBSISTEMAS = {"SUDESTE": 1, "SUL": 2, "NORDESTE": 3, "NORTE": 4}
    NOMES_USINAS_NAO_SIMULADAS = {
        1: "PCH",
        2: "PCT",
        3: "EOL",
        4: "UFV",
    }

    def __init__(
        self,
        caminho_deck: str,
        caminho_base_pequsi: str,
        caminho_base_profundidades: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__caminho_base_pequsi = caminho_base_pequsi
        self.__caminho_base_profundidades = caminho_base_profundidades
        self.__arquivo_caso = arquivo_caso
        self.__le_nomes_arquivos()
        self.__le_base()

    def __le_nomes_arquivos(self):
        caso = Caso.read(join(self.__caminho_deck, self.__arquivo_caso))
        self.__nome_arquivos = caso.arquivos
        arquivos = Arquivos.read(
            join(self.__caminho_deck, self.__nome_arquivos)
        )
        self.__nome_sistema = arquivos.sistema
        self.__nome_patamar = arquivos.patamar

    def __le_base(self):
        self.__df_base_pequsi = pd.read_csv(
            self.__caminho_base_pequsi, parse_dates=True
        )
        self.__df_base_pequsi["data"] = pd.to_datetime(
            self.__df_base_pequsi["data"]
        )
        # self.__df_base_profundidades = pd.read_csv(
        #     self.__caminho_base_profundidades, parse_dates=True
        # )
        # self.__df_base_profundidades["data"] = pd.to_datetime(
        #     self.__df_base_profundidades["data"]
        # )

    def __obtem_pequsi_verificada(
        self, base_pequsi: pd.DataFrame, pequsi_existente: pd.DataFrame
    ) -> pd.DataFrame:
        submercados = pequsi_existente["codigo_submercado"].unique()
        fontes = pequsi_existente["fonte"].unique()
        df_verif = pequsi_existente.copy()
        datas_caso = df_verif["data"].unique().tolist()
        for sub in submercados:
            for fonte in fontes:
                dados_verif = base_pequsi.loc[
                    (base_pequsi["codigo_submercado"] == sub)
                    & (base_pequsi["data"].isin(datas_caso))
                    & (base_pequsi["fonte"] == fonte),
                    "geracao",
                ].to_numpy()
                df_verif.loc[
                    (df_verif["codigo_submercado"] == sub)
                    & (df_verif["fonte"] == fonte),
                    "valor",
                ] = dados_verif
        return df_verif

    # def __obtem_profundidade_verificada(
    #     self,
    #     base_profundidade: pd.DataFrame,
    #     profundidade_existente: pd.DataFrame,
    # ) -> pd.DataFrame:
    #     submercados = profundidade_existente["Subsistema"].unique()
    #     fontes = profundidade_existente["Bloco"].unique()
    #     anos = profundidade_existente["Ano"].unique()
    #     patamares = profundidade_existente["Patamar"].unique()
    #     df_verif = profundidade_existente.copy()
    #     for sub in submercados:
    #         for fonte in fontes:
    #             for ano in anos:
    #                 for patamar in patamares:
    #                     dados_verif = base_profundidade.loc[
    #                         (base_profundidade["submercado"] == sub)
    #                         & (
    #                             base_profundidade["fonte"]
    #                             == self.__class__.NOMES_USINAS_NAO_SIMULADAS[
    #                                 fonte
    #                             ]
    #                         )
    #                         & (base_profundidade["data"].dt.year == ano)
    #                         & (base_profundidade["patamar"] == patamar),
    #                         "profundidade",
    #                     ].to_numpy()
    #                     df_verif.loc[
    #                         (df_verif["Subsistema"] == sub)
    #                         & (df_verif["Bloco"] == fonte)
    #                         & (df_verif["Ano"] == ano)
    #                         & (df_verif["Patamar"] == patamar),
    #                         list(self.__class__.MESES.values()),
    #                     ] = dados_verif
    #     return df_verif

    def processa_acl(self):
        # O processo todo é:
        # 1 - ler os dados do deck e gerar um DF que quebre cada PEQUSI por
        # patamar, em valor absoluto
        # 2 - Somar os valores da base, nas respectivas datas
        # 3 - Recalcular um patamar médio, por pequsi
        # 4 - Calculas as novas profundidades de patamar
        # 5 - Escreve os blocos atualizados no sistema.dat e patamar.dat

        # TODO - voltar a recalcular profundidades
        sistema = Sistema.read(join(self.__caminho_deck, self.__nome_sistema))
        # patamar = Patamar.le_arquivo(self.__caminho_deck, self.__nome_patamar)
        df_pequsi = sistema.geracao_usinas_nao_simuladas
        df_pequsi = df_pequsi.loc[df_pequsi["indice_bloco"] <= 4]
        df_pequsi = self.__obtem_pequsi_verificada(
            self.__df_base_pequsi, df_pequsi
        )
        # profs_verif = self.__obtem_profundidade_verificada(
        #     self.__df_base_profundidades, patamar.usinas_nao_simuladas
        # )
        sistema.geracao_usinas_nao_simuladas = df_pequsi
        # patamar.usinas_nao_simuladas = profs_verif
        sistema.write(join(self.__caminho_deck, self.__nome_sistema))
        # patamar.escreve_arquivo(self.__caminho_deck, self.__nome_patamar)


class ConversorCargasPECNEWAVE:
    """
    Classe responsável por realizar o ajuste dos arquivos sistema.dat
    , c_adic.dat e patamar.dat de um deck do NEWAVE, considerando dados de MMGD.

    No arquivo sistema.dat é alterado o bloco da geração esperada de pequenas
    usinas.

    No arquivo c_adic.dat são inseridas as gerações base de MMGD.

    No arquivo patamar.dat é alterada a profundidade dos patamares de cada bloco
    de MMGD relacionado no sistema.dat e também é recalculada a profundidade
    do mercado considerando a adição da base de MMGD.
    """

    SUBSISTEMAS = {"SUDESTE": 1, "SUL": 2, "NORDESTE": 3, "NORTE": 4}
    COLUNAS_USINAS_NAO_SIMULADAS = {
        5: "Hidro",
        6: "Termeletrica",
        7: "Eolica",
        8: "Fotovoltaica",
    }
    NOMES_USINAS_NAO_SIMULADAS = {
        5: "PCH_MMGD",
        6: "PCT_MMGD",
        7: "EOL_MMGD",
        8: "UFV_MMGD",
    }
    NOME_PATAMAR_MEDIO = "MEDIUM"
    PATAMARES_MERCADO = ["HIGH", "MIDDLE", "LOW"]
    ORDENS_PATAMARES = {
        "HIGH": 0,
        "MIDDLE": 1,
        "LOW": 2,
        "MEDIUM": 3,
    }
    COL_PROFUNDIDADES_UFV = "PU_fv"
    COL_CARGA_MMGD = "LOAD_MMGD"
    COL_BASE_MMGD = "Base_MMGD"

    def __init__(
        self,
        caminho_deck: str,
        caminho_planilha: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__caminho_planilha = caminho_planilha
        self.__arquivo_caso = arquivo_caso
        self.__le_nomes_arquivos()
        self.__le_planilha()

    def __le_nomes_arquivos(self):
        caso = Caso.read(join(self.__caminho_deck, self.__arquivo_caso))
        self.__nome_arquivos = caso.arquivos
        arquivos = Arquivos.read(
            join(self.__caminho_deck, self.__nome_arquivos)
        )
        dger = Dger.read(join(self.__caminho_deck, arquivos.dger))
        self.__nome_sistema = arquivos.sistema
        self.__nome_patamar = arquivos.patamar
        self.__nome_cadic = arquivos.c_adic
        self.__numero_anos_estudo = dger.num_anos_estudo

    def __le_planilha(self):
        self.df_planilha = pd.read_excel(
            self.__caminho_planilha, parse_dates=True
        )
        self.df_planilha["SOURCE_INDEX"] = self.df_planilha.apply(
            lambda linha: self.SUBSISTEMAS[linha["SOURCE"]], axis=1
        )
        self.df_planilha["TYPE_INDEX"] = self.df_planilha.apply(
            lambda linha: self.ORDENS_PATAMARES[linha["TYPE"]], axis=1
        )
        self.df_planilha = self.df_planilha.sort_values(
            ["SOURCE_INDEX", "DATE", "TYPE_INDEX"]
        )

    def processa_sistema_mercado(self):
        df = pd.DataFrame()
        dfp = self.df_planilha
        # Itera nos subsistemas
        for str_subsistema, indice_subsistema in self.SUBSISTEMAS.items():
            # Itera nos anos do estudo
            filtro = (dfp["SOURCE"] == str_subsistema) & (
                dfp["TYPE"] == self.NOME_PATAMAR_MEDIO
            )
            datas = dfp.loc[filtro, "DATE"].tolist()
            dados = dfp.loc[filtro, self.COL_CARGA_MMGD].to_numpy()
            # Adiciona o periodo pós
            datas = np.concatenate(
                (datas, [d + relativedelta(years=1) for d in datas[-12:]])
            )
            dados = np.concatenate((dados, dados[-12:]))
            # Monta o trecho do dataframe associado ao bloco lido
            df_mercado_mmgd = pd.DataFrame(
                data={"data": datas, "valor": dados}
            )
            df_mercado_mmgd["codigo_submercado"] = indice_subsistema
            # Reordena as colunas e concatena
            df_mercado_mmgd = df_mercado_mmgd[
                ["codigo_submercado", "data", "valor"]
            ]
            df = pd.concat([df, df_mercado_mmgd], ignore_index=True)
        sistema = Sistema.read(join(self.__caminho_deck, self.__nome_sistema))
        sistema.mercado_energia = df
        sistema.write(join(self.__caminho_deck, self.__nome_sistema))

    def processa_cadic_mmgd_base(self):
        cadic = Cadic.read(join(self.__caminho_deck, self.__nome_cadic))

        razoes_cadic = cadic.cargas["razao"].unique().tolist()
        if any(["MMGD" in r for r in razoes_cadic]):
            return

        df = pd.DataFrame()
        dfp = self.df_planilha
        # Itera nos subsistemas
        for str_subsistema, indice_subsistema in self.SUBSISTEMAS.items():
            # Itera nos anos do estudo
            filtro = (dfp["SOURCE"] == str_subsistema) & (
                dfp["TYPE"] == self.NOME_PATAMAR_MEDIO
            )
            datas = dfp.loc[filtro, "DATE"].tolist()
            dados = dfp.loc[filtro, self.COL_BASE_MMGD].to_numpy()
            # Adiciona o periodo pós
            datas = np.concatenate(
                (datas, [d + relativedelta(years=1) for d in datas[-12:]])
            )
            dados = np.concatenate((dados, dados[-12:]))
            # Monta o trecho do dataframe associado ao bloco lido
            df_cadic_mmgd = pd.DataFrame(data={"data": datas, "valor": dados})
            df_cadic_mmgd["codigo_submercado"] = indice_subsistema
            df_cadic_mmgd["nome_submercado"] = str_subsistema
            df_cadic_mmgd["razao"] = "MMGD"
            # Reordena as colunas e concatena
            df_cadic_mmgd = df_cadic_mmgd[
                [
                    "codigo_submercado",
                    "nome_submercado",
                    "razao",
                    "data",
                    "valor",
                ]
            ]
            df = pd.concat([df, df_cadic_mmgd], ignore_index=True)

        cadic.cargas = pd.concat([cadic.cargas, df], ignore_index=True)
        cadic.write(join(self.__caminho_deck, self.__nome_cadic))

    def processa_sistema_mmgd_expansao(self):
        sistema = Sistema.read(join(self.__caminho_deck, self.__nome_sistema))
        fontes_pequsi = (
            sistema.geracao_usinas_nao_simuladas["fonte"].unique().tolist()
        )
        if any(["MMGD" in r for r in fontes_pequsi]):
            return

        df = pd.DataFrame()
        dfp = self.df_planilha
        # Itera nos subsistemas
        for str_subsistema, indice_subsistema in self.SUBSISTEMAS.items():
            # Itera nos tipos de usinas não simuladas
            for (
                indice_pequsi,
                coluna_pequsi,
            ) in self.COLUNAS_USINAS_NAO_SIMULADAS.items():
                razao_pequsi = self.NOMES_USINAS_NAO_SIMULADAS[indice_pequsi]
                # Itera nos anos do estudo
                filtro = (dfp["SOURCE"] == str_subsistema) & (
                    dfp["TYPE"] == self.NOME_PATAMAR_MEDIO
                )
                datas = dfp.loc[filtro, "DATE"].tolist()
                dados = dfp.loc[filtro, coluna_pequsi].to_numpy()
                # Monta o trecho do dataframe associado ao bloco lido
                df_pequsi = pd.DataFrame(data={"data": datas, "valor": dados})
                df_pequsi["codigo_submercado"] = indice_subsistema
                df_pequsi["fonte"] = razao_pequsi
                df_pequsi["indice_bloco"] = indice_pequsi
                # Reordena as colunas e concatena
                df_pequsi = df_pequsi[
                    [
                        "codigo_submercado",
                        "indice_bloco",
                        "fonte",
                        "data",
                        "valor",
                    ]
                ]
                df = pd.concat([df, df_pequsi], ignore_index=True)

        sistema.geracao_usinas_nao_simuladas = pd.concat(
            [sistema.geracao_usinas_nao_simuladas, df], ignore_index=True
        )
        sistema.geracao_usinas_nao_simuladas.sort_values(
            ["codigo_submercado", "indice_bloco"], inplace=True
        )
        sistema.write(join(self.__caminho_deck, self.__nome_sistema))

    def processa_patamar_mercado(self):
        df = pd.DataFrame()
        dfp = self.df_planilha
        patamar = Patamar.read(join(self.__caminho_deck, self.__nome_patamar))
        # Itera nos subsistemas
        for str_subsistema, indice_subsistema in self.SUBSISTEMAS.items():
            dados = np.zeros((60 * len(self.PATAMARES_MERCADO),))
            for indice_patamar, nome_patamar in enumerate(
                self.PATAMARES_MERCADO
            ):
                filtro_medio = (dfp["SOURCE"] == str_subsistema) & (
                    dfp["TYPE"] == self.NOME_PATAMAR_MEDIO
                )
                filtro = (dfp["SOURCE"] == str_subsistema) & (
                    dfp["TYPE"] == nome_patamar
                )
                datas = dfp.loc[filtro, "DATE"].tolist()
                dados_medios = dfp.loc[
                    filtro_medio, self.COL_CARGA_MMGD
                ].to_numpy()
                dados = dfp.loc[filtro, self.COL_CARGA_MMGD].to_numpy()
                indice_inicial = 60 * indice_patamar
                indice_final = 60 * (indice_patamar + 1)
                dados[indice_inicial:indice_final] = np.divide(
                    dados, dados_medios
                )
            # Monta o trecho do dataframe associado ao bloco lido
            df_pats = pd.DataFrame(
                data={
                    "data": np.tile(datas, len(self.PATAMARES_MERCADO)),
                    "valor": dados,
                }
            )
            df_pats["codigo_submercado"] = indice_subsistema
            df_pats["patamar"] = np.repeat(
                list(range(1, len(self.PATAMARES_MERCADO) + 1)), 60
            )
            # Reordena as colunas e concatena
            df_pats = df_pats[
                ["codigo_submercado", "data", "patamar", "valor"]
            ].sort_values(["codigo_submercado", "data", "patamar"])
            df = pd.concat([df, df_pats], ignore_index=True)
        patamar.carga_patamares = df
        patamar.write(join(self.__caminho_deck, self.__nome_patamar))

    def processa_patamar_mmgd(self):
        patamar = Patamar.read(join(self.__caminho_deck, self.__nome_patamar))
        blocos = patamar.usinas_nao_simuladas["indice_bloco"].unique().tolist()
        if len(blocos) > 4:
            return

        df = pd.DataFrame()
        dfp = self.df_planilha
        datas_unicas = np.array(
            patamar.usinas_nao_simuladas["data"].unique().tolist()
        )
        # Itera nos subsistemas
        for str_subsistema, indice_subsistema in self.SUBSISTEMAS.items():
            # Itera nos tipos de usinas não simuladas
            for (
                indice_pequsi,
                coluna_pequsi,
            ) in self.COLUNAS_USINAS_NAO_SIMULADAS.items():
                razao_pequsi = self.NOMES_USINAS_NAO_SIMULADAS[indice_pequsi]
                # Só tem profundidades se for UFV
                dados_pq = np.ones(
                    (patamar.numero_patamares * len(datas_unicas),)
                )
                if razao_pequsi == "UFV_MMGD":
                    for indice_patamar in range(patamar.numero_patamares):
                        nome_patamar = [
                            nome
                            for nome, indice in self.ORDENS_PATAMARES.items()
                            if indice == indice_patamar
                        ][0]
                        filtro = (dfp["SOURCE"] == str_subsistema) & (
                            dfp["TYPE"] == nome_patamar
                        )
                        dados = dfp.loc[
                            filtro, self.COL_PROFUNDIDADES_UFV
                        ].to_numpy()
                        indice_inicial = indice_patamar * len(datas_unicas)
                        indice_final = indice_inicial + len(datas_unicas)
                        dados_pq[indice_inicial:indice_final] = dados

                # Monta o trecho do dataframe associado ao bloco lido
                df_pats = pd.DataFrame(
                    data={
                        "data": np.tile(
                            datas_unicas, len(self.PATAMARES_MERCADO)
                        ),
                        "valor": dados_pq,
                    }
                )
                df_pats["indice_bloco"] = indice_pequsi
                df_pats["codigo_submercado"] = indice_subsistema
                df_pats["patamar"] = np.repeat(
                    np.array(list(range(1, patamar.numero_patamares + 1))),
                    len(datas_unicas),
                )
                # Reordena as colunas e concatena
                df_pats = df_pats[
                    [
                        "codigo_submercado",
                        "patamar",
                        "indice_bloco",
                        "data",
                        "valor",
                    ]
                ]
                df = pd.concat([df, df_pats], ignore_index=True)
        patamar.usinas_nao_simuladas = pd.concat(
            [patamar.usinas_nao_simuladas, df], ignore_index=True
        )
        patamar.usinas_nao_simuladas.sort_values(
            ["codigo_submercado", "indice_bloco", "data", "patamar"],
            inplace=True,
        )
        patamar.write(join(self.__caminho_deck, self.__nome_patamar))


class DecompositorPequsiNEWAVE:
    def __init__(self, caso_referencia: str, caso: str) -> None:
        self.__caso_referencia = caso_referencia
        self.__caso = caso

    def __adequa_sistema(self):
        sistema_referencia = Sistema.read(
            join(self.__caso_referencia, "sistema.dat")
        )
        sistema_adequacao = Sistema.read(join(self.__caso, "sistema.dat"))

        df = sistema_adequacao.geracao_usinas_nao_simuladas

        # Só adequa se não tem pequsi separada por bloco
        if len(df["bloco"].unique()) >= 4:
            return

        df_ref = sistema_referencia.geracao_usinas_nao_simuladas

        df_ref_agrupado = (
            df_ref.groupby(["codigo_submercado", "data"]).sum().reset_index()
        )

        for submercado in df_ref["codigo_submercado"].unique():
            for fonte in df_ref["fonte"].unique():
                df_ref.loc[
                    (df_ref["codigo_submercado"] == submercado)
                    & (df_ref["fonte"] == fonte),
                    "valor",
                ] = np.divide(
                    df_ref.loc[
                        (df_ref["codigo_submercado"] == submercado)
                        & (df_ref["fonte"] == fonte),
                        "valor",
                    ],
                    df_ref_agrupado.loc[
                        (df_ref_agrupado["codigo_submercado"] == submercado),
                        "valor",
                    ]
                    .to_numpy()
                    .flatten(),
                )

        for submercado in df_ref["codigo_submercado"].unique():
            for fonte in df_ref["fonte"].unique():
                meses = [1, 2, 3, 4]
                df_ref.loc[
                    (df_ref["codigo_submercado"] == submercado)
                    & (df_ref["fonte"] == fonte)
                    & (df_ref["data"].dt.year == 2020)
                    & df_ref["data"].dt.month.isin(meses),
                    "valor",
                ] = float(
                    df_ref.loc[
                        (df_ref["codigo_submercado"] == submercado)
                        & (df_ref["fonte"] == fonte)
                        & (df_ref["data"].dt.year == 2021)
                        & df_ref["data"].dt.month.isin(meses),
                        "valor",
                    ]
                )

        df_novo = df_ref.copy()
        for submercado in df_novo["codigo_submercado"].unique():
            for fonte in df_novo["fonte"].unique():
                df_novo.loc[
                    (df_novo["codigo_submercado"] == submercado)
                    & (df_novo["fonte"] == fonte),
                    "valor",
                ] = np.multiply(
                    df.loc[
                        (df["codigo_submercado"] == submercado),
                        "valor",
                    ]
                    .to_numpy()
                    .flatten(),
                    df_ref.loc[
                        (df_ref["codigo_submercado"] == submercado)
                        & (df_ref["fonte"] == fonte),
                        "valor",
                    ]
                    .to_numpy()
                    .flatten(),
                )
        sistema_adequacao.geracao_usinas_nao_simuladas = df_novo
        sistema_adequacao.write(join(self.__caso, "sistema.dat"))

    def __adequa_patamar(self):
        patamar_referencia = Patamar.read(
            join(self.__caso_referencia, "patamar.dat")
        )
        patamar_adequacao = Patamar.read(join(self.__caso, "patamar.dat"))

        # Só adequa se não tem os patamares para pequsi
        if patamar_adequacao.usinas_nao_simuladas is not None:
            return

        patamar_referencia.duracao_mensal_patamares = (
            patamar_adequacao.duracao_mensal_patamares
        )
        patamar_referencia.carga_patamares = patamar_adequacao.carga_patamares
        patamar_referencia.intercambio_patamares = (
            patamar_adequacao.intercambio_patamares
        )
        # Cria dataframe "artificial" com os patamares da carga repetidos

        df_repetido = pd.DataFrame()
        for bloco in [1, 2, 3, 4]:
            df = patamar_adequacao.carga_patamares.copy()
            df["indice_bloco"] = bloco
            df_repetido = pd.concat([df_repetido, df], ignore_index=True)

        df_repetido = df_repetido[
            ["codigo_submercado", "indice_bloco", "data", "patamar", "valor"]
        ]
        df_repetido.sort_values(
            by=["codigo_submercado", "indice_bloco", "data", "patamar"],
            inplace=True,
        )
        patamar_referencia.usinas_nao_simuladas = df_repetido
        patamar_referencia.write(join(self.__caso, "patamar.dat"))

    def quebra_pequsi(self):
        self.__adequa_sistema()
        self.__adequa_patamar()


def adequa_acl_mmgd_newave(diretorio: str):
    Log.log().info(f"Adequando ACL e MMGD...")

    # Verifica se o NEWAVE precisa ser adequado
    caso = Path(diretorio).parts[-2]
    ano, mes, _ = caso.split("_")

    # Se o caso for de antes de Maio / 2020, quebra o bloco
    # de pequenas usinas por fonte
    data_caso = datetime(year=int(ano), month=int(mes), day=1)
    data_referencia = datetime(2020, 5, 1)
    if data_caso < data_referencia:
        decompositor = DecompositorPequsiNEWAVE(
            "2020_05_rv0/newave", diretorio
        )
        decompositor.quebra_pequsi()

    # Adequa ACL (substituir pequenas usinas pelo
    # histórico montado a priori)
    conversor_acl = ConversorACLVerificadoNEWAVE(
        caminho_deck=diretorio,
        caminho_base_pequsi=Configuracoes().arquivo_base_pequsi,
        caminho_base_profundidades="",
    )
    conversor_acl.processa_acl()

    # Adequa MMGD
    planilha_mmgd = join(
        Configuracoes().diretorio_dados_mmgd_newave,
        f"Previsoes_MMGD_NW_PMO_{ano}{mes}.xlsx",
    )
    conversor_mmgd = ConversorCargasPECNEWAVE(
        caminho_deck=diretorio, caminho_planilha=planilha_mmgd
    )
    conversor_mmgd.processa_cadic_mmgd_base()
    conversor_mmgd.processa_sistema_mmgd_expansao()
    conversor_mmgd.processa_patamar_mercado()
    conversor_mmgd.processa_patamar_mmgd()
