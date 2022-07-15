from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import CD
import pandas as pd
import datetime
from adequador.utils.backup import converte_utf8
from adequador.utils.log import Log
from adequador.utils.nomes import dados_caso, nome_arquivo_dadger
from adequador.utils.configuracoes import Configuracoes


def ajusta_deficit(diretorio: str):

    Log.log().info(f"Ajustando déficit...")

    df_deficit = pd.read_csv(Configuracoes().arquivo_custos_deficit, sep=";")

    anos = df_deficit["ano"].tolist()
    custo = df_deficit["custo"].tolist()

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)

    converte_utf8(diretorio, arquivo)
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
                    reg.custos = 3 * [custo[ind]]
                    reg.limites_superiores = [100, 100, 100]

    dadger.escreve_arquivo(diretorio, arquivo)
