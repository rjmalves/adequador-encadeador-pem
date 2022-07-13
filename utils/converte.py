from typing import Tuple, Optional, List
from os.path import isfile
from os import listdir
import time
import subprocess

TIMEOUT_DEFAULT = 10.0


def executa_terminal(
    cmds: List[str], timeout: float = TIMEOUT_DEFAULT
) -> Tuple[Optional[int], List[str]]:
    """
    Executa um comando no terminal e obtém as saídas e o código
    retornado pelo comando.

    :param cmds: Partes do comando que serão unidas em uma única
        string para execução.
    :param timeout: Tempo máximo para aguardar a saída do comando
        em segundos.
    :return: O código e as linhas de saída do comando.
    :rtype: Tuple[int, List[str]]
    """
    cmd = " ".join(cmds)
    processo = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True
    )
    t_inicio = time.time()
    linhas_saida: List[str] = []
    while True:
        std = processo.stdout
        if std is None:
            raise ValueError("Erro no subprocesso")
        saida = std.readline()
        linhas_saida.append(saida.strip())
        codigo = processo.poll()
        if codigo is not None:
            for saida in std.readlines():
                linhas_saida.append(saida.strip())
            break
        t_atual = time.time()
        if t_atual - t_inicio > timeout:
            break
        time.sleep(0.5)
    processo.terminate()
    return codigo, linhas_saida


def converte_codificacao(caminho: str, script_converte: str):
    print(f"Convertendo codificação do caso {caminho}")
    arqs = [
        a
        for a in listdir(caminho)
        if (".dat" in a or "dadger.rv" in a) and isfile(a)
    ]
    for a in arqs:
        _, out = executa_terminal([f"file -i {a}"])
        cod = out[0].split("charset=")[1].strip()
        if all([cod != "utf-8", cod != "us-ascii", cod != "binary"]):
            cod = cod.upper()
            c, _ = executa_terminal([f"{script_converte}" + f" {a} {cod}"])
