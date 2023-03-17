from os.path import join
from shutil import copyfile
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.nomes import (
    nome_arquivo_hidr,
    nome_arquivo_polinjus,
    dados_caso,
)


def __vale_fontes_nova(ano, mes, revisao) -> bool:
    ANO_FONTES_NOVA = 2022
    MES_FONTES_NOVA = 9
    RV_FONTES_NOVA = 1
    condicoes = [
        (ano > ANO_FONTES_NOVA),
        (ano == ANO_FONTES_NOVA) & (mes > MES_FONTES_NOVA),
        (ano == ANO_FONTES_NOVA)
        & (mes == MES_FONTES_NOVA) * (revisao >= RV_FONTES_NOVA),
    ]
    return any(condicoes)


def copia_hidr(diretorio: str):
    ano, mes, revisao = dados_caso(diretorio)
    arquivo = nome_arquivo_hidr()
    arq_destino_hidr = join(diretorio, arquivo)
    if __vale_fontes_nova(int(ano), int(mes), int(revisao.split("rv")[1])):
        copyfile(Configuracoes().arquivo_hidr_fontes_nova, arq_destino_hidr)
    else:
        copyfile(Configuracoes().arquivo_hidr_fontes_antiga, arq_destino_hidr)


def copia_polinjus(diretorio: str):
    ano, mes, revisao = dados_caso(diretorio)

    arquivo = nome_arquivo_polinjus()
    arq_destino_polinjus = join(diretorio, arquivo)
    if __vale_fontes_nova(int(ano), int(mes), int(revisao.split("rv")[1])):
        copyfile(
            Configuracoes().arquivo_polinjus_fontes_nova, arq_destino_polinjus
        )
    else:
        copyfile(
            Configuracoes().arquivo_polinjus_fontes_antiga,
            arq_destino_polinjus,
        )
