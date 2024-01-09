from inewave.newave import Caso, Arquivos, Dger, Sistema, Cadic
import pandas as pd
from os import listdir
from os.path import join
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
from shutil import move
from adequador.utils.log import Log
from adequador.utils.configuracoes import Configuracoes


class AdequaFCFExternaNEWAVE:

    MESES_POS = [datetime(9999, m, 1) for m in range(1, 13)]

    def __init__(
        self,
        caminho_deck: str,
        arquivo_caso: str = "caso.dat",
    ) -> None:
        self.__caminho_deck = caminho_deck
        self.__arquivo_caso = arquivo_caso
        self.__diretorio_caso = Path(caminho_deck).parts[-2]
        self.__ano, self.__mes, _ = self.__diretorio_caso.split("_")
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
        sistema.mercado_energia = df_mercado.loc[
            ~df_mercado["data"].isin(AdequaFCFExternaNEWAVE.MESES_POS)
        ]
        sistema.write(join(self.__caminho_deck, self.__arquivos.sistema))

        # c_adic.dat
        ano_inicio = dger.ano_inicio_estudo
        num_anos = dger.num_anos_estudo
        ano_final = ano_inicio + num_anos
        meses_fora_periodo = [datetime(ano_final, m, 1) for m in range(1, 13)]
        cadic = Cadic.read(join(self.__caminho_deck, self.__arquivos.c_adic))
        df_cargas = cadic.cargas
        cadic.cargas = df_cargas.loc[
            ~df_cargas["data"].isin(AdequaFCFExternaNEWAVE.MESES_POS)
        ]
        cadic.cargas = df_cargas.loc[
            ~df_cargas["data"].isin(meses_fora_periodo)
        ]
        cadic.write(join(self.__caminho_deck, self.__arquivos.c_adic))

    def __copia_fcf_externa(self):
        df_mapa_fcf = pd.read_csv(
            Configuracoes().arquivo_mapa_fcf_externa, sep=";"
        )
        caso_com_pos = df_mapa_fcf.loc[
            df_mapa_fcf["caso_sem_pos"] == self.__diretorio_caso, "caso_completo"
        ].iloc[0]
        caminho_caso_com_pos = join(
            Configuracoes().diretorio_casos_fcf_externa, caso_com_pos, "newave"
        )
        # Extrai os arquivos da FCF externa
        arquivo_zip_cortes = [
            a
            for a in listdir(caminho_caso_com_pos)
            if "cortes_" in a and ".zip" in a
        ][0]
        with ZipFile(join(caminho_caso_com_pos, arquivo_zip_cortes), "r") as z:
            mapa_nomes_cortes = {
                "cortesh.dat": "cortesh-pos.dat",
                "cortes-060.dat": "cortes-pos.dat",
            }
            for arq_origem, arq_destino in mapa_nomes_cortes.items():
                z.extract(arq_origem, caminho_caso_com_pos)
                move(join(caminho_caso_com_pos, arq_origem), join(self.__caminho_deck, arq_destino))


def adequa_fcfexterna_newave(diretorio: str):
    Log.log().info(f"Adequando FCF Externa...")
    fcfpos = AdequaFCFExternaNEWAVE(caminho_deck=diretorio)
    fcfpos.adiciona_fcf_pos_estudo()
