from idecomp.decomp import Caso, Arquivos, Dadger
from idecomp.decomp.modelos.dadger import UH, CX
import pandas as pd
from os.path import join
from datetime import datetime, timedelta


class AdequaDeckHibridoDECOMP:
    """
    Classe responsável por realizar adequações para um deck
    de DECOMP para acoplar com um caso de NEWAVE híbrido.
    - Atributos NW nos registros UH de usinas futuras
    - Registros CX para os complexos
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
        self.__revisao = self.__nome_arquivos.split("rv")[1]

    def __adiciona_CX(self, dadger: Dadger, usinaNW: int, usinaDC: int):
        usina = dadger.uh(usinaDC)
        if usina is not None:
            if dadger.cx(codigo_newave=usinaNW, codigo_decomp=usinaDC) is None:
                posicao = dadger.uh()[-1]
                cx_novo = CX()
                cx_novo.codigo_newave = usinaNW
                cx_novo.codigo_decomp = usinaDC
                dadger.data.add_after(posicao, cx_novo)

    def adiciona_registros_CX(self, arquivo_usinas_cx: str):
        dadger = Dadger.read(join(self.__caminho_deck, self.__arquivos.dadger))

        df_cx = pd.read_csv(arquivo_usinas_cx, sep=";")
        for _, linha in df_cx.iterrows():
            usiDC = linha["usiDC"]
            usiNW = linha["usiNW"]
            self.__adiciona_CX(dadger, usiNW, usiDC)

        # Escreve novo arquivo
        dadger.write(join(self.__caminho_deck, self.__arquivos.dadger))

    def __adiciona_NW(self, dadger: Dadger, u: int):
        usina = dadger.uh(codigo=u)
        if usina is None:
            posicao = dadger.uh()[0]
            uh_novo = UH()
            uh_novo.codigo_usina = u
            uh_novo.configuracao_newave = "NW"

            dadger.data.add_after(posicao, uh_novo)

    def adiciona_registros_NW(self, arquivo_usinas_nw: str):
        dadger = Dadger.read(join(self.__caminho_deck, self.__arquivos.dadger))

        df_nw = pd.read_csv(arquivo_usinas_nw, sep=";")
        # ------------ Coleta informações de datas do deck
        n_est = len(dadger.dp(codigo_submercado=1))
        dataini = datetime(
            day=dadger.dt.dia, month=dadger.dt.mes, year=dadger.dt.ano
        )  # data de inicio do 1º estágio
        anodeck = (dataini + timedelta(days=7)).year  # ano do PMO

        datasdeck = [dataini]
        for e in range(1, n_est, 1):
            datasdeck = datasdeck + [
                dataini + timedelta(days=7 * e)
            ]  # datas iniciais de todos os estágios
        pmo = datasdeck[(n_est - 1) - 1].month  # mês do PMO

        for _, linha in df_nw.iterrows():
            adiciona_usina_caso = all(
                [
                    linha["ano"] == anodeck,
                    linha["mes"] == pmo,
                    linha["rv"] == "-" or linha["rv"] == self.__revisao,
                ]
            )
            if adiciona_usina_caso:
                u = linha["usina"]
                self.__adiciona_NW(dadger, u)

        # Escreve novo arquivo
        dadger.write(join(self.__caminho_deck, self.__arquivos.dadger))


def adequa_hibrido_decomp(diretorio: str):
    hibrido = AdequaDeckHibridoDECOMP(caminho_deck=diretorio)
    hibrido.adiciona_registros_CX()
    hibrido.adiciona_registros_NW()
