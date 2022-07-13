from os import listdir, getenv
import pathlib
from os.path import isdir, join
from typing import Callable, Dict, Tuple
from dotenv import load_dotenv
from utils.iteracao import itera_casos
from utils.nomes import (
    nome_arquivo_dadger,
    nome_arquivo_modif,
    nome_arquivo_cvar,
    nome_arquivo_dger,
)
from compatibilizacao_rees.decomp import ajusta_dados_rees
from dados_gerais.decomp import ajusta_dados_gerais as ajusta_dados_gerais_dc
from dados_gerais.newave import ajusta_dados_gerais as ajusta_dados_gerais_nw
from dados_gerais.newave import ajusta_cvar
from gtdp.newave_modif_cfuga_cmont import (
    adequa_cfuga_cmont as adequa_cfuga_cmont_nw,
)
from gtdp.decomp_cfuga_cmont import adequa_cfuga_cmont as adequa_cfuga_cmont_dc
from gtdp.decomp_ac import ajusta_acs
from gtdp.decomp_fj import ajusta_fj
from restricoes.decomp_volume_espera import ajusta_volume_espera
from gtdp.copia_hidr_polinjus import copia_arquivos_gtdp
from vminop.decomp_rhe import ajusta_rhe
from vminop.newave_dger_curva import adequa_dger_curva

# Lê as configurações das variáveis de ambiente
load_dotenv(override=True)

DIR_BASE = pathlib.Path().resolve()
load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)

# Dados de entrada
DIRETORIO_CASOS = getenv("DIRETORIO_CASOS")
CASO_INICIO = getenv("CASO_INICIO")
CASO_FIM = getenv("CASO_FIM")
ADEQUA_NEWAVE = bool(int(getenv("ADEQUA_NEWAVE")))
ADEQUA_DECOMP = bool(int(getenv("ADEQUA_DECOMP")))
AJUSTES_NEWAVE = [a for a in getenv("AJUSTES_NEWAVE").split(",") if len(a) > 0]
AJUSTES_DECOMP = [a for a in getenv("AJUSTES_DECOMP").split(",") if len(a) > 0]


CODIGOS_AJUSTES_NEWAVE: Dict[Tuple[Callable, Callable]] = {
    "DADOSGERAIS": (ajusta_dados_gerais_nw, nome_arquivo_dger),
    "CVAR": (ajusta_cvar, nome_arquivo_cvar),
    "GTDP_CFUGA_CMONT": (adequa_cfuga_cmont_nw, nome_arquivo_modif),
    "GTDP_CFUGA_CMONT": (adequa_cfuga_cmont_nw, nome_arquivo_modif),
}

CODIGOS_AJUSTES_DECOMP: Dict[Tuple[Callable, Callable]] = {
    "REES": (ajusta_dados_rees, nome_arquivo_dadger),
    "DADOSGERAIS": (ajusta_dados_gerais_dc, nome_arquivo_dadger),
    "GTDP_CFUGA_CMONT": (adequa_cfuga_cmont_dc, nome_arquivo_dadger),
    "GTDP_FJ": (ajusta_fj, nome_arquivo_dadger),
    "GTDP_AC": (ajusta_acs, nome_arquivo_dadger),
    "VOLUMES_ESPERA": (ajusta_volume_espera, nome_arquivo_dadger),
    "VMINOP": (ajusta_rhe, nome_arquivo_dadger),
}

# MARIANA: Falta o script de Deficit para o DECOMP
# MARIANA: Pq o valor de penalidade do VminOp para o NEWAVE é fixo? TODO
# MARIANA: Onde são definidos os arquivos csv de dados de entrada? Colocar como opção no .cfg
# MARIANA: Falta ajustar o script decomp_rhe para ler do csv -- OK
# MARIANA: E os scrpts de cópia de arquivos, conversão, entram aonde? -- Junto com os outros.


# ------- NEWAVE --------
ajustes = []
if ADEQUA_NEWAVE:
    for a in AJUSTES_NEWAVE:
        ajustes.append(CODIGOS_AJUSTES_NEWAVE[a])

casos = [
    c
    for c in listdir(DIRETORIO_CASOS)
    if isdir(join(DIRETORIO_CASOS, c))
    if "_rv0" in c
]
casos.sort()

for ajuste in ajustes:
    itera_casos(
        diretorio_casos=DIRETORIO_CASOS,
        casos=casos,
        caso_inicio=CASO_INICIO,
        caso_fim=CASO_FIM,
        programa="newave",
        nome_arquivo=ajuste[1],
        funcao_ajuste=ajuste[0],
    )


# ------- DECOMP --------
ajustes = []
if ADEQUA_DECOMP:
    for a in AJUSTES_DECOMP:
        ajustes.append(CODIGOS_AJUSTES_DECOMP[a])

casos = [
    c for c in listdir(DIRETORIO_CASOS) if isdir(join(DIRETORIO_CASOS, c))
]
casos.sort()

for ajuste in ajustes:
    itera_casos(
        diretorio_casos=DIRETORIO_CASOS,
        casos=casos,
        caso_inicio=CASO_INICIO,
        caso_fim=CASO_FIM,
        programa="decomp",
        nome_arquivo=ajuste[1],
        funcao_ajuste=ajuste[0],
    )
