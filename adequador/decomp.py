from typing import Dict, Callable
from os import listdir
from os.path import isdir, join
from adequador.convertenomes.decomp import ajusta_convertenomes_decomp
from adequador.arquivos_entrada.atualiza_vazoes import atualiza_vazoes
from adequador.arquivos_entrada.atualiza_velocidades import (
    atualiza_velocidades,
)
from adequador.compatibilizacao_rees.decomp import ajusta_dados_rees
from adequador.convertenomes.utf8 import ajusta_utf8
from adequador.dados_gerais.decomp import ajusta_dados_gerais
from adequador.gtdp.decomp_gtdp import ajusta_gtdp
from adequador.penalidades.decomp_deficit import ajusta_deficit
from adequador.restricoes.decomp_volume_espera import ajusta_volume_espera
from adequador.vminop.decomp_rhe import ajusta_rhe
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.iteracao import itera_casos

CODIGOS_AJUSTES_DECOMP: Dict[str, Callable] = {
    "CONVERTENOMES": ajusta_convertenomes_decomp,
    "VAZOES": atualiza_vazoes,
    "VELOCIDADES": atualiza_velocidades,
    "REES": ajusta_dados_rees,
    "DADOSGERAIS": ajusta_dados_gerais,
    "GTDP": ajusta_gtdp,
    "DEFICIT": ajusta_deficit,
    "VOLUMES_ESPERA": ajusta_volume_espera,
    "VMINOP": ajusta_rhe,
    "UTF8": ajusta_utf8,
}


def adequa_decomp():
    ajustes = []
    if Configuracoes().adequa_decomp:
        Log.log().info(
            f"Ajustes para o DECOMP: "
            + ", ".join(Configuracoes().ajustes_decomp)
        )
        for a in Configuracoes().ajustes_decomp:
            ajustes.append(CODIGOS_AJUSTES_DECOMP[a])

        casos = [
            c
            for c in listdir(Configuracoes().dir_base)
            if isdir(join(Configuracoes().dir_base, c)) and "_rv" in c
        ]
        casos.sort()
        Log.log().info("Casos DECOMP: " + ", ".join(casos))

        itera_casos(
            diretorio_casos=Configuracoes().dir_base,
            casos=casos,
            caso_inicio=Configuracoes().caso_inicio,
            caso_fim=Configuracoes().caso_fim,
            programa="decomp",
            funcoes_ajuste=ajustes,
        )
