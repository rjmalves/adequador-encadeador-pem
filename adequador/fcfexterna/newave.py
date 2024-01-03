from inewave.newave import Caso, Arquivos, Dger, Sistema, Cadic
import pandas as pd
from os import listdir
from os.path import join
from pathlib import Path
from zipfile import ZipFile
from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes


class AdequaFCFExternaNEWAVE:
    def __init__(
        self,
        caminho_deck: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__arquivo_caso = arquivo_caso
        self.__caso = Path(caminho_deck).parts[-2]
        self.__ano, self.__mes, _ = self.__caso.split("_")
        self.__le_nomes_arquivos()

    def __le_nomes_arquivos(self):
        self.__caso = Caso.read(join(self.__caminho_deck, self.__arquivo_caso))
        self.__nome_arquivos = self.__caso.arquivos
        self.__arquivos = Arquivos.read(
            join(self.__caminho_deck, self.__nome_arquivos)
        )

    def adiciona_fcf_pos_estudo(self):
        # Modifica os arquivos necessários no caso
        self.__adequa_arquivos_remocao_pos()
        # Transfere o arquivo da FCF necessária para o caso
        self.__copia_fcf_externa()

    def __adequa_arquivos_remocao_pos(self):
        # dger.dat
        dger = Dger.read(join(self.__caminho_deck, self.__arquivos.dger))
        dger.fcf_pos_estudo = 1
        dger.num_anos_pos_estudo = 0
        dger.write(join(self.__caminho_deck, self.__arquivos.dger))

        # sistema.dat
        sistema = Sistema.read(
            join(self.__caminho_deck, self.__arquivos.sistema)
        )
        df_mercado = sistema.mercado_energia
        anos_mercado = df_mercado["data"].dt.year.unique().tolist()
        anos_estudo = anos_mercado[: dger.num_anos_estudo]
        sistema.mercado_energia = df_mercado.loc[
            df_mercado["data"].dt.year.isin(anos_estudo)
        ]
        sistema.write(join(self.__caminho_deck, self.__arquivos.sistema))

        # c_adic.dat
        cadic = Cadic.read(join(self.__caminho_deck, self.__arquivos.c_adic))
        df_cargas = cadic.cargas
        anos_cargas = df_cargas["data"].dt.year.unique().tolist()
        anos_estudo = anos_cargas[: dger.num_anos_estudo]
        cadic.cargas = df_cargas.loc[
            df_cargas["data"].dt.year.isin(anos_estudo)
        ]
        cadic.write(join(self.__caminho_deck, self.__arquivos.sistema))

    def __copia_fcf_externa(self):
        df_mapa_fcf = pd.read_csv(
            Configuracoes().arquivo_mapa_fcf_externa, sep=";"
        )
        caso_com_pos = df_mapa_fcf.loc[
            df_mapa_fcf["caso_sem_pos"] == self.__caso, "caso_completo"
        ].iloc[0]
        caminho_caso_com_pos = join(
            Configuracoes().diretorio_casos_fcf_externa, caso_com_pos, "newave"
        )
        # Extrai os arquivos da FCF externa
        arquivo_zip_cortes = [
            a
            for a in listdir(self.__caminho_deck)
            if "cortes_" in a and ".zip" in a
        ][0]
        with ZipFile(join(caminho_caso_com_pos, arquivo_zip_cortes), "r") as z:
            mapa_nomes_cortes = {
                "cortesh.dat": "cortesh-pos.dat",
                "cortes-060.dat": "cortes-pos.dat",
            }
            for arq_origem, arq_destino in mapa_nomes_cortes.items():
                z.extract(arq_origem, join(self.__caminho_deck, arq_destino))


def adequa_fcfexterna_newave(diretorio: str):
    Log.log().info(f"Adequando FCF Externa...")
    fcfpos = AdequaFCFExternaNEWAVE(caminho_deck=diretorio)
    fcfpos.adiciona_fcf_pos_estudo()
