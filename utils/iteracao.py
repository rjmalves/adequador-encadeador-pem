from typing import Callable, Optional
from os.path import join, isfile
from os import getenv
from shutil import copyfile
import time
import pathlib
from dotenv import load_dotenv
from utils.converte import converte_codificacao
from utils.log import Log


DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)
SCRIPT_CONVERTE_CODIFICACAO = getenv("SCRIPT_CONVERTE_CODIFICACAO")


def itera_casos(
    diretorio_casos: str,
    casos: list,
    caso_inicio: Optional[str],
    caso_fim: str,
    programa: str,
    nome_arquivo: Callable,
    funcao_ajuste: Callable,
    backup: bool = False,
):

    iniciou = True if caso_inicio is None else False

    for caso in casos:
        if caso == caso_inicio:
            iniciou = True
        if caso == caso_fim:
            break
        if not iniciou:
            continue
        diretorio = join(diretorio_casos, caso, programa)
        arquivo = nome_arquivo(caso)
        arquivo_backup = f"backup_{arquivo}"
        if (
            backup
            and not isfile(join(diretorio, arquivo_backup))
            and isfile(join(diretorio, arquivo))
        ):
            copyfile(join(diretorio, arquivo), join(diretorio, arquivo_backup))
        if isfile(join(diretorio, arquivo)):
            converte_codificacao(
                join(diretorio, arquivo), SCRIPT_CONVERTE_CODIFICACAO
            )

        Log.log().info(
            f"Fazendo adequação do deck de {programa} do caso {caso}"
        )
        t_inicio = time.time()

        # Executa a função de ajuste
        funcao_ajuste(diretorio, arquivo)

        Log.log().info(
            f"Fim da adequação do caso. Tempo = {time.time() - t_inicio}"
        )
