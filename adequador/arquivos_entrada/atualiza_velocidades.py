from os.path import join
from shutil import copyfile
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.nomes import dados_caso
from adequador.utils.nomes import nome_arquivo_vazoes


def obtem_nome_arquivo_velocidades(ano: str, mes: str, revisao: str):
    raiz = f"velocidades.Gevazp_{ano}{mes.zfill(2)}_"
    digito_revisao = revisao.split("rv")[1]
    if digito_revisao == "0":
        return raiz + "PMO"
    else:
        return raiz + f"REV{digito_revisao}"


def atualiza_velocidades(diretorio: str):
    Log.log().info(f"Adequando VELOCIDADES...")
    ano_caso, mes_caso, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_vazoes(revisao_caso)
    copyfile(
        join(
            Configuracoes().diretorio_velocidades,
            obtem_nome_arquivo_velocidades(ano_caso, mes_caso, revisao_caso),
        ),
        join(diretorio, arquivo),
    )
