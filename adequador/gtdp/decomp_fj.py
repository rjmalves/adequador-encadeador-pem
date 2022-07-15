from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import CQ, FJ
from adequador.utils.backup import converte_utf8
from adequador.utils.log import Log
from adequador.utils.nomes import (
    dados_caso,
    nome_arquivo_dadger,
    nome_arquivo_polinjus,
)


def ajusta_fj(diretorio: str):

    Log.log().info(f"Adequando GTDP_FJ...")

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    converte_utf8(diretorio, arquivo)
    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # Consideração dos polinômios de jusante
    if dadger.fj is None:
        fj_novo = FJ()
        fj_novo.arquivo = nome_arquivo_polinjus()
        reg_anterior = dadger.lista_registros(CQ)[-1]
        dadger.cria_registro(reg_anterior, fj_novo)
    else:
        dadger.fj.arquivo = nome_arquivo_polinjus()

    dadger.escreve_arquivo(diretorio, arquivo)
