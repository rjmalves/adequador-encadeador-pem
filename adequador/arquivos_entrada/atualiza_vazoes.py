from os.path import join
from shutil import copyfile
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.nomes import dados_caso
from adequador.utils.nomes import nome_arquivo_vazoes


def obtem_nome_arquivo_vazoes(ano: str, mes: str, revisao: str):
    return f"vazoes.{ano}_{mes.zfill(2)}_rv{revisao}"


def atualiza_vazoes(diretorio: str):
    Log.log().info(f"Adequando VAZOES...")
    ano_caso, mes_caso, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_vazoes(revisao_caso)
    copyfile(
        join(
            Configuracoes().diretorio_vazoes,
            obtem_nome_arquivo_vazoes(ano_caso, mes_caso, revisao_caso),
        ),
        join(diretorio, arquivo),
    )
