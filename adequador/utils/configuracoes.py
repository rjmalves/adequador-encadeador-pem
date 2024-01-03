from adequador.utils.singleton import Singleton
from os import getenv
from os.path import join
import pathlib


class Configuracoes(metaclass=Singleton):
    def __init__(self):
        self.dir_base = pathlib.Path().resolve()
        self.caso_inicio = getenv("CASO_INICIO")
        self.caso_fim = getenv("CASO_FIM")
        self.adequa_newave = bool(int(getenv("ADEQUA_NEWAVE")))
        self.ajustes_newave = getenv("AJUSTES_NEWAVE").split(",")
        self.adequa_decomp = bool(int(getenv("ADEQUA_DECOMP")))
        self.ajustes_decomp = getenv("AJUSTES_DECOMP").split(",")
        self.realiza_backup = bool(int(getenv("REALIZA_BACKUP")))
        self.diretorio_dados_adequacao = join(
            self.dir_base, getenv("DIRETORIO_DADOS_ADEQUACAO")
        )
        self.arquivo_dados_gerais_newave = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_DADOS_GERAIS_NEWAVE"),
        )
        self.arquivo_selcor_newave = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_SELCOR_NEWAVE"),
        )
        self.arquivo_cpamp_newave = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_CPAMP_NEWAVE"),
        )
        self.arquivo_valores_penalidades_newave = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_VALORES_PENALIDADES_NEWAVE"),
        )
        self.arquivo_base_pequsi = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_BASE_PEQUSI"),
        )
        self.arquivo_vminop = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_VMINOP")
        )
        self.arquivo_cfuga_cmont = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_CFUGA_CMONT")
        )
        self.arquivo_cfuga_cmont_historico = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_CFUGA_CMONT_HISTORICO"),
        )
        self.arquivo_volumes_sazonais = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_VOLUMES_SAZONAIS")
        )
        self.arquivo_ac_nposnw = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_AC_NPOSNW")
        )
        self.arquivo_ac_vertju = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_AC_VERTJU")
        )
        self.arquivo_hidr = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_HIDR")
        )
        self.arquivo_indices = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_INDICES")
        )
        self.arquivo_polinjus = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_POLINJUS"),
        )
        self.arquivo_custos_deficit = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_CUSTOS_DEFICIT")
        )
        self.arquivo_volumes_espera = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_VOLUMES_ESPERA")
        )
        self.diretorio_vazoes = join(
            self.diretorio_dados_adequacao, getenv("DIRETORIO_VAZOES")
        )
        self.diretorio_velocidades = join(
            self.diretorio_dados_adequacao, getenv("DIRETORIO_VELOCIDADES")
        )
        self.diretorio_dados_mmgd_newave = join(
            self.diretorio_dados_adequacao,
            getenv("DIRETORIO_DADOS_MMGD_NEWAVE"),
        )
        self.diretorio_dados_mmgd_decomp = join(
            self.diretorio_dados_adequacao,
            getenv("DIRETORIO_DADOS_MMGD_DECOMP"),
        )
        self.diretorio_casos_fcf_externa = getenv(
            "DIRETORIO_CASOS_FCF_EXTERNA"
        )
        self.arquivo_mapa_fcf_externa = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_MAPA_FCF_EXTERNA"),
        )
        self.arquivo_produtibilidades_usinas = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_PRODUTIBILIDADES_USINAS"),
        )
        self.executavel_convertenomes_newave = getenv(
            "EXECUTAVEL_CONVERTENOMES_NEWAVE"
        )
        self.executavel_convertenomes_decomp = getenv(
            "EXECUTAVEL_CONVERTENOMES_DECOMP"
        )
        self.script_converte_codificacao = getenv(
            "SCRIPT_CONVERTE_CODIFICACAO"
        )
