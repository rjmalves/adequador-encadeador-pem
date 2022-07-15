from typing import Callable, List
from os.path import join
import time
from adequador.utils.log import Log


def itera_casos(
    diretorio_casos: str,
    casos: list,
    caso_inicio: str,
    caso_fim: str,
    programa: str,
    funcoes_ajuste: List[Callable],
):

    iniciou = True if caso_inicio == "" else False

    for caso in casos:
        if caso == caso_inicio:
            iniciou = True
        if caso == caso_fim:
            break
        if not iniciou:
            continue
        diretorio = join(diretorio_casos, caso, programa)

        Log.log().info(
            f"Fazendo adequação do deck de {programa} do caso {caso}"
        )
        t_inicio = time.time()

        # Executa a função de ajuste
        for f in funcoes_ajuste:
            f(diretorio)

        Log.log().info(
            f"Fim da adequação do caso. Tempo = {time.time() - t_inicio}"
        )
