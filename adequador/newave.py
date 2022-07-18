from adequador.convertenomes.newave import ajusta_convertenomes_newave
from adequador.arquivos_entrada.atualiza_vazoes import atualiza_vazoes
from adequador.dados_gerais.newave import ajusta_dados_gerais_cvar
from adequador.gtdp.copia_hidr_polinjus import copia_hidr
from adequador.gtdp.newave_modif_cfuga_cmont import adequa_cfuga_cmont
from adequador.penalidades.newave_penalid_deficit import (
    corrige_deficit_sistema,
    corrige_penalid,
)
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.iteracao import itera_casos
from typing import Dict, Callable
from os import listdir
from os.path import join, isdir

from adequador.vminop.newave_vminop import adequa_vminop

CODIGOS_AJUSTES_NEWAVE: Dict[str, Callable] = {
    "CONVERTENOMES": ajusta_convertenomes_newave,
    "VAZOES": atualiza_vazoes,
    "REES": None,
    "DADOSGERAIS": ajusta_dados_gerais_cvar,
    "GTDP": adequa_cfuga_cmont,
    "DEFICIT": corrige_deficit_sistema,
    "PENALIDADES": corrige_penalid,
    "VMINOP": adequa_vminop,
    "HIDR": copia_hidr,
}


def adequa_newave():
    ajustes = []
    if Configuracoes().adequa_newave:
        Log.log().info(
            f"Ajustes para o NEWAVE: "
            + ", ".join(Configuracoes().ajustes_newave)
        )
        for a in Configuracoes().ajustes_newave:
            ajustes.append(CODIGOS_AJUSTES_NEWAVE[a])

        casos = [
            c
            for c in listdir(Configuracoes().dir_base)
            if isdir(join(Configuracoes().dir_base, c))
            if "_rv0" in c
        ]
        casos.sort()
        Log.log().info("Casos NEWAVE: " + ", ".join(casos))

        itera_casos(
            diretorio_casos=Configuracoes().dir_base,
            casos=casos,
            caso_inicio=Configuracoes().caso_inicio,
            caso_fim=Configuracoes().caso_fim,
            programa="newave",
            funcoes_ajuste=ajustes,
        )
