from adequador.convertenomes.newave import ajusta_convertenomes_newave
from adequador.convertenomes.utf8 import ajusta_utf8
from adequador.dados_gerais.newave import ajusta_dados_gerais_cvar_selcor
from adequador.gtdp.newave_modif_cfuga_cmont_exph import (
    adequa_cfuga_cmont_exph,
)
from adequador.penalidades.newave_penalid_deficit import (
    corrige_deficit_sistema,
    corrige_penalid,
)
from adequador.acl_mmgd.newave import adequa_acl_mmgd_newave
from adequador.hibrido.newave import adequa_hibrido_newave
from adequador.arquivos_entrada.atualiza_vazoes_newave import atualiza_vazoes
from adequador.fcfexterna.newave import adequa_fcfexterna_newave
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.iteracao import itera_casos
from typing import Dict, Callable
from os import listdir
from os.path import join, isdir

from adequador.vminop.newave_vminop import adequa_vminop

CODIGOS_AJUSTES_NEWAVE: Dict[str, Callable] = {
    "CONVERTENOMES": ajusta_convertenomes_newave,
    "REES": None,
    "VAZOES": atualiza_vazoes,
    "DADOSGERAIS": ajusta_dados_gerais_cvar_selcor,
    "GTDP": adequa_cfuga_cmont_exph,
    "DEFICIT": corrige_deficit_sistema,
    "PENALIDADES": corrige_penalid,
    "VMINOP": adequa_vminop,
    "UTF8": ajusta_utf8,
    "ACL_MMGD": adequa_acl_mmgd_newave,
    "HIBRIDO": adequa_hibrido_newave,
    "FCFEXTERNA": adequa_fcfexterna_newave,
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
