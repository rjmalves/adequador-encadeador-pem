from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import CD
import pandas as pd
import datetime
from os.path import join
from os import getenv
import pathlib
from dotenv import load_dotenv

# Dados de entrada:
DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = join(DIR_BASE, getenv("DIRETORIO_DADOS_ADEQUACAO"))

ARQUIVO_CUSTOS_DEFICIT = join(
    DIRETORIO_DADOS_ADEQUACAO, getenv("ARQUIVO_CUSTOS_DEFICIT")
)


def ajusta_deficit(diretorio: str, arquivo: str):

    df_deficit = pd.read_csv(ARQUIVO_CUSTOS_DEFICIT, sep=";")

    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()

    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # -------------------- pega datas
    dataini = datetime.date(
        day=dadger.dt.dia, month=dadger.dt.mes, year=dadger.dt.ano
    )  # data de inicio do deck
    anodeck = (dataini + datetime.timedelta(days=7)).year  # ano do PMO

    cds = dadger.lista_registros(CD)
    patamares = [reg.numero_curva for reg in cds]

    if anodeck in anos:
        if (2 in patamares) or (3 in patamares) or (4 in patamares):
            ind = anos.index(anodeck)
            for reg in cds:
                if reg.numero_curva > 1:
                    dadger.deleta_registro(reg)
                else:
                    reg.custos = 3*[custo[ind]]
                    reg.limites_superiores = [100, 100, 100]

    dadger.escreve_arquivo(diretorio, arquivo)
