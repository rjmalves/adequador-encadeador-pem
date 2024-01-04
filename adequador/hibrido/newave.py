from inewave.newave import Caso, Arquivos, Dger, Modif, Confhd, Ree, Re, Hidr
from inewave.newave.modelos.modif import USINA, VAZMAXT, TURBMINT, TURBMAXT
import pandas as pd
from os.path import join
from datetime import datetime
from dateutil.relativedelta import relativedelta
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from typing import Dict, Tuple


class AdequaDeckHibridoNEWAVE:
    """
    Classe responsável por realizar adequações para um deck
    de NEWAVE REE para representar um caso de híbrido.
    - Horizonte de individualização (ree.dat)
    - Penalidades adicionais (vazmax, turb. min, turb. max)
    - Restrições adicionais (FSARH)
    - Correções de JURUENA (decks de 2021 e 2022)
    """

    def __init__(
        self,
        caminho_deck: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__arquivo_caso = arquivo_caso
        self.__le_nomes_arquivos()

    def __le_nomes_arquivos(self):
        self.__caso = Caso.read(join(self.__caminho_deck, self.__arquivo_caso))
        self.__nome_arquivos = self.__caso.arquivos
        self.__arquivos = Arquivos.read(
            join(self.__caminho_deck, self.__nome_arquivos)
        )

    def horizonte_individualizado(self):
        df = pd.read_csv(Configuracoes().arquivo_dados_gerais_newave, sep=";")
        numero_meses = int(
            df.loc[
                df["parametro"] == "periodos_individualizados", "valor"
            ].iloc[0]
        )
        if numero_meses > 0:
            ree = Ree.read(join(self.__caminho_deck, self.__arquivos.ree))
            dger = Dger.read(join(self.__caminho_deck, self.__arquivos.dger))
            dger.restricao_defluencia = 1
            dger.restricao_turbinamento = 1
            data_caso = datetime(
                year=dger.ano_inicio_estudo,
                month=dger.mes_inicio_estudo,
                day=1,
            )
            data_fim = data_caso + relativedelta(months=numero_meses)
            ree.rees["mes_fim_individualizado"] = data_fim.month
            ree.rees["ano_fim_individualizado"] = data_fim.year
            ree.write(join(self.__caminho_deck, self.__arquivos.ree))

    def __aplica_vazmaxt_usina(
        self, modif: Modif, df: pd.DataFrame, u: int, estagios: pd.Series
    ):
        reg_usina = modif.usina(codigo=u)
        # Verifica se a usina é modificada
        # Se não, insere o registro usina e altera no confhd
        if reg_usina is None:
            reg_usina = USINA()
            reg_usina.codigo = u
            reg_usina.nome = df.loc[df["Id_Usina"] == u, "Usina"].tolist()[0]
            modif.data.append(reg_usina)
            confhd = Confhd.read(
                join(self.__caminho_deck, self.__arquivos.confhd)
            )
            usis = confhd.usinas
            usis.loc[usis["codigo_usina"] == u, "usina_modificada"] = 1
            confhd.write(join(self.__caminho_deck, self.__arquivos.confhd))
        else:
            # Apaga todos os vazmaxt da usina
            modifs_usina = modif.modificacoes_usina(u)
            if modifs_usina is not None:
                vazmaxt_usina = [
                    m
                    for m in modif.modificacoes_usina(u)
                    if isinstance(m, VAZMAXT)
                ]
                for m in vazmaxt_usina:
                    modif.data.remove(m)

        # Cria os vazmaxt e vai inserindo, logo abaixo da USINA
        ultimo_reg = reg_usina
        for e in estagios:
            # Pega a restrição permanente mais recente da usina
            fsarh_u = df.loc[
                (df["Id_Usina"] == u)
                & (df["Temporalidade restrição"] == "Permanente")
                & (df["Data início"] <= e)
                & (df["Data fim"] >= e)
            ]
            valor_restricao_permanente = 99999.0
            if fsarh_u.shape[0] > 0:
                data_criacao_mais_recente = fsarh_u["Data criação"].max()
                fasrh_u_mais_recente = fsarh_u.loc[
                    fsarh_u["Data criação"] == data_criacao_mais_recente
                ]
                valor_restricao_permanente = fasrh_u_mais_recente[
                    "Valor"
                ].min()
            # Confere se a usina tem restrição sazonal
            # PREMISSA: uma usina tem no maximo 1 restrição sazonal
            fsarh_u = df.loc[
                (df["Id_Usina"] == u)
                & (df["Temporalidade restrição"] == "Sazonal")
                & (df["Data início"] <= e)
                & (df["Data fim"] >= e)
            ]
            meses_fsarh_sazonal = []
            if fsarh_u.shape[0] > 0:
                mes_inicio = int(fsarh_u["Mês início sazonal"].tolist()[0])
                mes_fim = int(fsarh_u["Mês fim sazonal"].tolist()[0])
                if mes_inicio < mes_fim:
                    meses_fsarh_sazonal = list(range(mes_inicio, mes_fim + 1))
                else:
                    meses_fsarh_sazonal = list(
                        set(range(1, 13)).difference(
                            set(range(mes_fim + 1, mes_inicio))
                        )
                    )
                valor_restricao_sazonal = fsarh_u["Valor"].tolist()[0]
            reg_novo = VAZMAXT()
            reg_novo.data_inicio = datetime(year=e.year, month=e.month, day=1)
            if reg_novo.data_inicio.month in meses_fsarh_sazonal:
                reg_novo.vazao = valor_restricao_sazonal
            else:
                reg_novo.vazao = valor_restricao_permanente
            modif.data.add_after(ultimo_reg, reg_novo)
            ultimo_reg = reg_novo

    def __aplica_turbmint_usina(
        self, modif: Modif, df: pd.DataFrame, u: int, estagios: pd.Series
    ):
        reg_usina = modif.usina(codigo=u)
        # Verifica se a usina é modificada
        # Se não, insere o registro usina e altera no confhd
        if reg_usina is None:
            reg_usina = USINA()
            reg_usina.codigo = u
            reg_usina.nome = df.loc[df["Id_Usina"] == u, "Usina"].tolist()[0]
            modif.data.append(reg_usina)
            confhd = Confhd.read(
                join(self.__caminho_deck, self.__arquivos.confhd)
            )
            usis = confhd.usinas
            usis.loc[usis["codigo_usina"] == u, "usina_modificada"] = 1
            confhd.write(join(self.__caminho_deck, self.__arquivos.confhd))
        else:
            # Apaga todos os turbmint da usina
            modifs_usina = modif.modificacoes_usina(u)
            if modifs_usina is not None:
                turbmint_usina = [
                    m
                    for m in modif.modificacoes_usina(u)
                    if isinstance(m, TURBMINT)
                ]
                for m in turbmint_usina:
                    modif.data.remove(m)

        # Cria os vazmaxt e vai inserindo, logo abaixo da USINA
        ultimo_reg = reg_usina
        for e in estagios:
            # Pega a restrição permanente mais recente da usina
            fsarh_u = df.loc[
                (df["Id_Usina"] == u)
                & (df["Temporalidade restrição"] == "Permanente")
                & (df["Data início"] <= e)
                & (df["Data fim"] >= e)
            ]
            valor_restricao_permanente = 0.0
            if fsarh_u.shape[0] > 0:
                data_criacao_mais_recente = fsarh_u["Data criação"].max()
                fasrh_u_mais_recente = fsarh_u.loc[
                    fsarh_u["Data criação"] == data_criacao_mais_recente
                ]
                valor_restricao_permanente = fasrh_u_mais_recente[
                    "Valor"
                ].min()
            # Confere se a usina tem restrição sazonal
            # PREMISSA: uma usina tem no maximo 1 restrição sazonal
            fsarh_u = df.loc[
                (df["Id_Usina"] == u)
                & (df["Temporalidade restrição"] == "Sazonal")
                & (df["Data início"] <= e)
                & (df["Data fim"] >= e)
            ]
            meses_fsarh_sazonal = []
            if fsarh_u.shape[0] > 0:
                mes_inicio = int(fsarh_u["Mês início sazonal"].tolist()[0])
                mes_fim = int(fsarh_u["Mês fim sazonal"].tolist()[0])
                if mes_inicio < mes_fim:
                    meses_fsarh_sazonal = list(range(mes_inicio, mes_fim + 1))
                else:
                    meses_fsarh_sazonal = list(
                        set(range(1, 13)).difference(
                            set(range(mes_fim + 1, mes_inicio))
                        )
                    )
                valor_restricao_sazonal = fsarh_u["Valor"].tolist()[0]
            reg_novo = TURBMINT()
            reg_novo.data_inicio = datetime(year=e.year, month=e.month, day=1)
            if reg_novo.data_inicio.month in meses_fsarh_sazonal:
                reg_novo.turbinamento = valor_restricao_sazonal
            else:
                reg_novo.turbinamento = valor_restricao_permanente
            modif.data.add_after(ultimo_reg, reg_novo)
            ultimo_reg = reg_novo

    def adiciona_restricoes_fsarh_defluencia_maxima(
        self, dados_fsarh: str = "./dados_adequacao/def_max_permanente.csv"
    ):
        dger = Dger.read(join(self.__caminho_deck, self.__arquivos.dger))
        modif = Modif.read(join(self.__caminho_deck, self.__arquivos.modif))
        mes_inicio = datetime(
            year=dger.ano_inicio_estudo, month=dger.mes_inicio_estudo, day=1
        )
        mes_fim = datetime(
            year=dger.ano_inicio_estudo + dger.num_anos_estudo - 1,
            month=12,
            day=1,
        )
        df = pd.read_csv(dados_fsarh, index_col=0)
        df["Data criação"] = pd.to_datetime(df["Data criação"])
        df["Data início"] = pd.to_datetime(df["Data início"])
        df["Data fim"] = pd.to_datetime(df["Data fim"])
        usinas = df["Id_Usina"].unique().tolist()
        estagios = pd.date_range(mes_inicio, mes_fim, freq="MS")

        for u in usinas:
            self.__aplica_vazmaxt_usina(modif, df, u, estagios)

        modif.write(join(self.__caminho_deck, self.__arquivos.modif))

    def adiciona_restricoes_fsarh_turbinamento_minimo(
        self, dados_fsarh: str = "./dados_adequacao/tur_min_permanente.csv"
    ):
        dger = Dger.read(join(self.__caminho_deck, self.__arquivos.dger))
        modif = Modif.read(join(self.__caminho_deck, self.__arquivos.modif))
        mes_inicio = datetime(
            year=dger.ano_inicio_estudo, month=dger.mes_inicio_estudo, day=1
        )
        mes_fim = datetime(
            year=dger.ano_inicio_estudo + dger.num_anos_estudo - 1,
            month=12,
            day=1,
        )
        df = pd.read_csv(dados_fsarh, index_col=0)
        df["Data criação"] = pd.to_datetime(df["Data criação"])
        df["Data início"] = pd.to_datetime(df["Data início"])
        df["Data fim"] = pd.to_datetime(df["Data fim"])
        usinas = df["Id_Usina"].unique().tolist()
        estagios = pd.date_range(mes_inicio, mes_fim, freq="MS")

        for u in usinas:
            self.__aplica_turbmint_usina(modif, df, u, estagios)

        modif.write(join(self.__caminho_deck, self.__arquivos.modif))

    def __monta_conjuntos_usinas(self, re: Re) -> Dict[int, list]:
        usinas_res = {}
        df_conjuntos = re.usinas_conjuntos
        conjuntos = df_conjuntos["conjunto"].unique()
        for conjunto in conjuntos:
            usinas_res[conjunto] = (
                df_conjuntos.loc[
                    df_conjuntos["conjunto"] == conjunto, "codigo_usina"
                ]
                .dropna()
                .tolist()
            )
        return usinas_res

    def __calcula_engolimento_fatores_divisao_re(
        self, usinas_res: Dict[int, list], hidr: pd.DataFrame
    ) -> Tuple[Dict[int, list], Dict[int, float]]:
        usinas_totais = list(usinas_res.values())
        usinas_unicas = list(set([u for conj in usinas_totais for u in conj]))
        fatores_res = {}
        engol_usinas = {u: 0 for u in usinas_unicas}
        for conjunto, usinas in usinas_res.items():
            pot_conjunto = 0.0
            pot_usis = []
            for usina in usinas:
                n_conj = hidr.at[usina, "numero_conjuntos_maquinas"]
                pot_usi = 0.0
                engol_usi = 0.0
                for i in range(1, n_conj + 1):
                    pot_usi += (
                        hidr.at[usina, f"maquinas_conjunto_{i}"]
                        * hidr.at[usina, f"potencia_nominal_conjunto_{i}"]
                    )
                    engol_usi += (
                        hidr.at[usina, f"maquinas_conjunto_{i}"]
                        * hidr.at[usina, f"vazao_nominal_conjunto_{i}"]
                    )
                pot_usis.append(pot_usi)
                engol_usinas[usina] = engol_usi
                pot_conjunto += pot_usi
            fatores_res[conjunto] = [
                pot_usi / pot_conjunto for pot_usi in pot_usis
            ]
        return fatores_res, engol_usinas

    def __obtem_prodt_usina(
        self, prodts: pd.DataFrame, hidr: pd.DataFrame, codigo_usina: int
    ) -> float:
        nome_usina = hidr.at[codigo_usina, "nome_usina"]
        return prodts.loc[
            (prodts["configuracao"] == 1)
            & (prodts["nome_usina"] == nome_usina),
            "produtibilidade_equivalente_volmin_volmax",
        ].iloc[0]

    def __calcula_restricoes_turbinamento_maximo(
        self,
        dger: Dger,
        re: Re,
        hidr: pd.DataFrame,
        engol_usinas: Dict[int, float],
        usinas_res: Dict[int, list],
        fatores_res: Dict[int, list],
    ) -> Dict[int, pd.DataFrame]:
        datas = pd.date_range(
            datetime(
                year=dger.ano_inicio_estudo,
                month=dger.mes_inicio_estudo,
                day=1,
            ),
            datetime(
                year=dger.ano_inicio_estudo + dger.num_anos_estudo - 1,
                month=12,
                day=1,
            ),
            freq="MS",
        )
        # Cria os dataframes com as restrições de turbinamento de cada usina, porém
        # limitando pelo engolimento máximo
        dfs_usinas = {
            usina: pd.DataFrame(
                data={
                    "data": datas,
                    "turbmx": [engol] * len(datas),
                }
            )
            for usina, engol in engol_usinas.items()
        }

        prodts = pd.read_csv(Configuracoes().arquivo_produtibilidades_usinas)

        # Divide proporcionalmente a restrição de geração de cada uma
        # Converte a restrição de geração em turbinamento usando a PRODT
        for _, restricao in re.restricoes.iterrows():
            conjunto = restricao["conjunto"]
            restricao_mw = restricao["restricao"]
            data_inicio = datetime(
                year=restricao["ano_inicio"],
                month=restricao["mes_inicio"],
                day=1,
            )
            data_fim = datetime(
                year=restricao["ano_fim"], month=restricao["mes_fim"], day=1
            )
            datas_restricao = pd.date_range(data_inicio, data_fim, freq="MS")
            usi = usinas_res[conjunto]
            for i, codigo_usina in enumerate(usi):
                fator = fatores_res[conjunto][i]
                prodt = self.__obtem_prodt_usina(prodts, hidr, codigo_usina)
                limite_turb_usina = restricao_mw * fator / prodt
                dfs_usinas[codigo_usina].loc[
                    dfs_usinas[codigo_usina]["data"].isin(datas_restricao),
                    "turbmx",
                ] = limite_turb_usina
        return dfs_usinas

    def __aplica_turbmaxt_usina(
        self,
        confhd: Confhd,
        modif: Modif,
        hidr: pd.DataFrame,
        dfs_usinas: Dict[int, pd.DataFrame],
    ):
        for usina, df in dfs_usinas.items():
            modificada = confhd.usinas.loc[
                confhd.usinas["codigo_usina"] == usina, "usina_modificada"
            ].iloc[0]
            if not modificada:
                confhd.usinas.loc[
                    confhd.usinas["codigo_usina"] == usina, "usina_modificada"
                ] = 1
                reg_usina = USINA()
                reg_usina.codigo = int(usina)
                reg_usina.nome = hidr.at[usina, "nome_usina"]
                modif.data.append(reg_usina)

            # Apaga todos os turbmaxt da usina
            modifs_usina = modif.modificacoes_usina(usina)
            if modifs_usina is not None:
                turbmaxt_usina = [
                    m
                    for m in modif.modificacoes_usina(usina)
                    if isinstance(m, TURBMAXT)
                ]
                for m in turbmaxt_usina:
                    modif.data.remove(m)
                ultimo_reg = (
                    modifs_usina[-1]
                    if len(modifs_usina) > 0
                    else modif.usina(codigo=usina)
                )
            else:
                ultimo_reg = modif.usina(codigo=usina)
            # Adiciona os turbmax devidos
            for _, linha in df.iterrows():
                reg_turb = TURBMAXT()
                reg_turb.data_inicio = linha["data"]
                reg_turb.turbinamento = linha["turbmx"]
                modif.data.add_after(ultimo_reg, reg_turb)
                ultimo_reg = reg_turb

    def adiciona_restricoes_re_turbinamento_maximo(self):
        dger = Dger.read(join(self.__caminho_deck, self.__arquivos.dger))
        re = Re.read(join(self.__caminho_deck, self.__arquivos.re))
        hidr = Hidr.read(join(self.__caminho_deck, "hidr.dat")).cadastro
        confhd = Confhd.read(join(self.__caminho_deck, self.__arquivos.confhd))
        modif = Modif.read(join(self.__caminho_deck, self.__arquivos.modif))

        usinas_res = self.__monta_conjuntos_usinas(re)
        (
            fatores_res,
            engol_usinas,
        ) = self.__calcula_engolimento_fatores_divisao_re(usinas_res, hidr)

        dfs_usinas = self.__calcula_restricoes_turbinamento_maximo(
            dger, re, hidr, engol_usinas, usinas_res, fatores_res
        )

        self.__aplica_turbmaxt_usina(confhd, modif, hidr, dfs_usinas)

        confhd.write(join(self.__caminho_deck, self.__arquivos.confhd))
        modif.write(join(self.__caminho_deck, self.__arquivos.modif))


def adequa_hibrido_newave(diretorio: str):
    Log.log().info("Adequando HIBRIDO...")

    hibrido = AdequaDeckHibridoNEWAVE(caminho_deck=diretorio)
    hibrido.horizonte_individualizado()
    hibrido.adiciona_restricoes_fsarh_defluencia_maxima()
    hibrido.adiciona_restricoes_fsarh_turbinamento_minimo()
    hibrido.adiciona_restricoes_re_turbinamento_maximo()
