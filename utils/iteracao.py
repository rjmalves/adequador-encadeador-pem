from typing import Callable, Optional
from os.path import join
import time

def itera_casos(diretorio_casos: str, casos: list, caso_inicio: Optional[str], caso_fim: str, 
                programa:str, nome_arquivo: Callable, funcao_ajuste: Callable):

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

        print(f"Fazendo adequação do deck de {programa} do caso {caso}")
        t_inicio = time.time()

        # Executa a função de ajuste 
        funcao_ajuste(diretorio,arquivo)

        print(f"Fim da adequação do caso. Tempo = {time.time() - t_inicio}")