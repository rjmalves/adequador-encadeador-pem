from os.path import join
from os import getenv, sep
from dotenv import load_dotenv
from shutil import copyfile
import pathlib

DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
DIRETORIO_DADOS_ADEQUACAO = getenv("DIRETORIO_DADOS_ADEQUACAO")

DIR_VAZOES = join(DIRETORIO_DADOS_ADEQUACAO, getenv("DIRETORIO_VAZOES"))


def obtem_nome_arquivo_vazoes(ano: str, mes: str, revisao: str):
    raiz = f"vazoes.Gevazp_{ano}{mes.zfill(2)}_"
    if revisao == "0":
        return raiz + "PMO"
    else:
        return raiz + f"REV{revisao}"


def atualiza_vazoes(diretorio: str, arquivo: str):
    dados_estudo = diretorio.split(sep)[-2]
    ano_caso = dados_estudo[0]
    mes_caso = dados_estudo[1]
    revisao_caso = dados_estudo[2].split("rv")[1]
    copyfile(
        join(
            DIR_VAZOES,
            obtem_nome_arquivo_vazoes(ano_caso, mes_caso, revisao_caso),
        ),
        join(diretorio, arquivo),
    )
