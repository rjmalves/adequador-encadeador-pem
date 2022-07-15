from typing import Dict, Callable
from os import listdir
from os.path import isdir, join
from adequador.arquivos_entrada.atualiza_vazoes import atualiza_vazoes
from adequador.compatibilizacao_rees.decomp import ajusta_dados_rees
from adequador.dados_gerais.decomp import ajusta_dados_gerais
from adequador.gtdp.decomp_cfuga_cmont import adequa_cfuga_cmont
from adequador.gtdp.decomp_ac import ajusta_acs
from adequador.gtdp.decomp_fj import ajusta_fj
from adequador.gtdp.copia_hidr_polinjus import copia_hidr, copia_polinjus
from adequador.penalidades.decomp_deficit import ajusta_deficit
from adequador.restricoes.decomp_volume_espera import ajusta_volume_espera
from adequador.vminop.decomp_rhe import ajusta_rhe
from adequador.utils.configuracoes import Configuracoes
from adequador.utils.log import Log
from adequador.utils.iteracao import itera_casos

CODIGOS_AJUSTES_DECOMP: Dict[str, Callable] = {
    "VAZOES": atualiza_vazoes,
    "REES": ajusta_dados_rees,
    "DADOSGERAIS": ajusta_dados_gerais,
    "GTDP_CFUGA_CMONT": adequa_cfuga_cmont,
    "GTDP_FJ": ajusta_fj,
    "GTDP_AC": ajusta_acs,
    "DEFICIT": ajusta_deficit,
    "VOLUMES_ESPERA": ajusta_volume_espera,
    "VMINOP": ajusta_rhe,
    "HIDR": copia_hidr,
    "POLINJUS": copia_polinjus,
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
